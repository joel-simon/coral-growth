# cython: boundscheck=False
# cython: wraparound=True
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True

from __future__ import print_function
from math import isnan, sqrt, floor
import numpy as np
from pykdtree.kdtree import KDTree

from cymesh.mesh import Mesh
from cymesh.collisions.findCollisions import findCollisions
from cymesh.subdivision.sqrt3 import split
from cymesh.operators.relax import relax_mesh

from coral_growth.modules import light, gravity
from coral_growth.modules.morphogens import Morphogens

class Coral(object):
    num_inputs = 4 # [light, curvature, gravity, extra-bias-bit?]
    num_outputs = 1

    def __init__(self, obj_path, network, morphogens_params, params):
        self.mesh = Mesh.from_obj(obj_path)
        self.network = network

        self.volume = 0
        self.total_gametes = 0

        self.growth_scalar = params['growth_scalar']
        self.max_polyps = params['max_polyps']
        self.moprhogen_steps = params['morphogen_steps']
        self.n_memory = params['polyp_memory']
        self.morph_thresholds = params['morph_thresholds']

        self.morphogens = Morphogens(self, morphogens_params)

        mean_face = np.mean([f.area() for f in self.mesh.faces])
        mean_edge = np.mean([e.length() for e in self.mesh.edges])
        self.max_face_area = mean_face * params['max_face_growth']

        self.n_polyps = 0

        self.num_inputs = Coral.num_inputs + self.n_memory + len(morphogens_params) * (self.morph_thresholds-1)
        self.num_outputs = Coral.num_outputs + self.n_memory + len(morphogens_params)

        assert network.NumInputs() == self.num_inputs
        assert network.NumOutputs() == self.num_outputs

        self.polyp_inputs = [0 for _ in range(self.num_inputs)]
        self.polyp_inputs[self.num_inputs-1] = 1 # The last input is always used as bias.

        self.polyp_verts = [None] * self.max_polyps
        self.polyp_light = np.zeros(self.max_polyps)
        self.polyp_energy = np.zeros(self.max_polyps)
        self.polyp_flow = np.zeros(self.max_polyps)
        self.polyp_pos = np.zeros((self.max_polyps, 3))
        self.polyp_normal = np.zeros((self.max_polyps, 3))
        self.polyp_last_pos = np.zeros((self.max_polyps, 3))
        self.polyp_gravity = np.zeros(self.max_polyps)
        self.polyp_collided = np.zeros(self.max_polyps, dtype='uint8')
        assert self.n_memory <= 32
        self.polyp_memory = np.zeros((self.max_polyps), dtype='uint32')

        for vert in self.mesh.verts:
            self.createPolyp(vert)

        self.mesh.calculateNormals()
        self.mesh.calculateCurvature()
        self.updateAttributes()
        self.age = 0

    def __str__(self):
        s = 'Coral: {npolyps:%i, volume:%f}' % (len(self.n_polyps), self.volume)
        return s

    def step(self):
        self.polypsGrow()
        self.handleCollisions()
        relax_mesh(self.mesh) # Update mesh
        self.polypDivision() # Divide mesh and create new polyps.
        self.updateAttributes()
        self.age += 1

    def polypsGrow(self):
        """ Calculate the changes to coral by neural network.
        """
        self.polyp_last_pos[:, :] = self.polyp_pos

        for i in range(self.n_polyps):
            if self.polyp_pos[i, 1] < 0:
                continue

            self.createPolypInputs(i)
            self.network.Flush() # Compute feed-forward network results.
            self.network.Input(self.polyp_inputs)
            self.network.ActivateFast()
            output = self.network.Output()

            assert len(output) == self.num_outputs

            # Move in normal direction by growth amount.
            growth = output[0] * self.growth_scalar
            self.polyp_pos[i] += self.polyp_normal[i] * growth

            # Output morphogens.
            out_idx = 1
            for mi in range(self.morphogens.n_morphogens):
                if output[out_idx] > 0.5:
                    self.morphogens.V[mi, i] = 1
                out_idx += 1

            for mi in range(self.n_memory):
                if output[out_idx] > 0.5:
                    self.polyp_memory[i] |= ( 1 << mi )
                out_idx += 1

            assert (not isnan(self.polyp_pos[i, 0]))
            assert (not isnan(self.polyp_pos[i, 1]))
            assert (not isnan(self.polyp_pos[i, 2]))

    def updateAttributes(self):

        self.mesh.calculateNormals()
        self.mesh.calculateCurvature()
        # print(max([abs(v.curvature) for v in self.mesh.verts]))
        light.calculate_light(self) # Update the light

        self.polyp_light[self.polyp_light != 0] -= .5
        self.polyp_light *= 2 # all light values go from 0-1

        # Adjust values to depend on height of polpy.
        # Make polyp on bottom get half light of one on top.
        # Height goes to about 10.
        self.polyp_light *= (.2 + self.polyp_pos[:, 1] * .2)

        gravity.calculate_gravity(self)
        self.morphogens.update(self.moprhogen_steps) # Update the morphogens.

    def createPolypInputs(self, i):
        """ Map polyp stats to nerual input in [-1, 1] range. """
        # morph_bin_size = 1.0 / self.morph_thresholds
        self.polyp_inputs = [-1] * self.num_inputs

        self.polyp_inputs[0] = (self.polyp_light[i] * 2) - 1
        self.polyp_inputs[1] = (self.polyp_verts[i].curvature * 2) - 1
        self.polyp_inputs[2] = (self.polyp_gravity[i] * 2) - 1

        input_idx = 3
        for mi in range(self.morphogens.n_morphogens):
            mbin = int(floor(self.morphogens.U[mi, i] * self.morph_thresholds))
            mbin = min(self.morph_thresholds - 1, mbin)

            if mbin > 0:
                self.polyp_inputs[input_idx + (mbin-1)] = 1

            input_idx += (self.morph_thresholds-1)

        for mi in range(self.n_memory):
            if self.polyp_memory[i] & (1 << mi):
                self.polyp_inputs[input_idx] = 1
            else:
                self.polyp_inputs[input_idx] = -1
            input_idx += 1

    def handleCollisions(self):
        collisions = findCollisions(self.mesh)
        self.polyp_collided *= 0 # Used for debugging

        for vi, collided in enumerate(collisions):
            if collided:
                vert = self.mesh.verts[vi]
                vert.p[:] = self.polyp_last_pos[vi]
                self.polyp_collided[vi] = 1

    def createPolyp(self, vert):
        if self.n_polyps == self.max_polyps:
            return

        idx = self.n_polyps
        self.n_polyps += 1
        vert.data['polyp'] = idx
        self.polyp_pos[idx, :] = vert.p
        vert.normal = self.polyp_normal[idx]
        vert.p = self.polyp_pos[idx]
        self.polyp_verts[idx] = vert

        foo = np.zeros(self.n_memory, dtype='uint32')
        neighbors = vert.neighbors()
        half = len(neighbors) // 2

        for vert_n in neighbors:
            if 'polyp' in vert_n.data:
                memory = self.polyp_memory[vert_n.data['polyp']]
                for i in range(self.n_memory):
                    if memory & (1 << i):
                        foo[i] += 1
        for i in range(self.n_memory):
            if foo[i] > half:
                self.polyp_memory[idx] |= (1 << i)

        assert vert.id == idx

    def polypDivision(self):
        """ Update the mesh and create new polyps.
        """
        to_divide = []
        for face in self.mesh.faces:
            if face.area() > self.max_face_area:
                to_divide.append(face)

        for face in to_divide:
            if len(self.mesh.verts) == self.max_polyps:
                break
            split(self.mesh, face, self.max_polyps)

        for vert in self.mesh.verts:
            if 'polyp' not in vert.data:
                self.createPolyp(vert)

    def fitness(self):
        light = 0

        volume = self.mesh.volume()

        capture = 0
        tree = KDTree(self.polyp_pos[:self.n_polyps], leafsize=16)
        query = np.zeros((1, 3))

        for face in self.mesh.faces:
            area = face.area()
            p = face.midpoint()
            if p[1] > .1:
                query[0] = p
                d, indx = tree.query(query, k=10)
                capture += area * np.mean(d)

            light += area * sum(self.polyp_light[v.id] for v in face.vertices())

        # Normalized values (values for seed).
        light /= 0.38655
        capture /= 0.154
        volume /= 1.209
        fitness = (light + capture) / sqrt(volume)

        return fitness

    def export(self, out):
        """ Export the coral to .coral.obj file
            A .coral.obj file is a 3d mesh with polyp specific information.
            it is a compatable superset of the .obj file format.
            In addition to the content of a .obj file a .coral.obj file has:

            1. A header row that begins with '#coral' that lists space
                deliminated polyp attributes
            2. A line that begins with 'c' for each vert that contains values
                for each attribute. Ordered the same as the vertices.
        """
        self.mesh.calculateNormals()
        self.mesh.calculateCurvature()

        header = [ 'light', 'gravity', 'curvature', 'collided', 'memory']
        for i in range(self.morphogens.n_morphogens):
            header.append( 'u%i' % i )

        out.write('#Exported from coral_growth\n')
        out.write('#coral ' + ' '.join(header) + '\n')

        mesh_data = self.mesh.export()

        id_to_indx = dict()

        for i, vert in enumerate(self.mesh.verts):
            r, g, b = 0, 0, 0

            if self.morphogens.n_morphogens > 0:
                g = self.morphogens.U[0, i]

            if self.morphogens.n_morphogens > 1:
                b = self.morphogens.U[1, i]

            out.write('v %f %f %f %f %f %f\n' % (tuple(vert.p)+(r, g, b)))
            id_to_indx[vert.id] = i

        out.write('\n\n')

        polyp_attributes = [None] * self.n_polyps

        for i in range(self.n_polyps):
            indx = id_to_indx[self.polyp_verts[i].id]

            polyp_attributes[indx] = [ self.polyp_light[i],
                                       self.polyp_gravity[i],
                                       self.polyp_verts[i].curvature,
                                       self.polyp_collided[i],
                                       self.polyp_memory[i] ]

            for j in range(self.morphogens.n_morphogens):
                polyp_attributes[indx].append(self.morphogens.U[j, i])

            assert len(polyp_attributes[indx]) == len(header)

        for attributes in polyp_attributes:
            out.write('c ' + ' '.join(map(str, attributes)) + '\n')

        out.write('\n')

        for face in mesh_data['faces']:
            out.write('f %i %i %i\n' % tuple(face + 1))
