# cython: boundscheck=False
# cython: wraparound=True
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True

from __future__ import print_function
from math import isnan, sqrt
import numpy as np

from cymesh.mesh import Mesh
from cymesh.collisions.findCollisions import findCollisions
from cymesh.subdivision.sqrt3 import divide_adaptive, split
from cymesh.operators.relax import relax_mesh

from coral_growth.light import calculate_light
from coral_growth.modules.gravity import calculate_gravity
from coral_growth.modules.morphogens import Morphogens

class Coral(object):
    num_inputs = 3
    num_outputs = 1

    def __init__(self, obj_path, network, config):
        self.mesh = Mesh.from_obj(obj_path)
        self.network = network

        self.volume = 0
        self.total_gametes = 0

        self.growth_scalar = config['growth_scalar']
        self.max_polyps = config['max_polyps']

        self.morphogens = Morphogens(self, config['morphogens'])

        mean_face = np.mean([f.area() for f in self.mesh.faces])
        self.max_face_area = mean_face * config['max_face_growth']

        self.n_polyps = 0
        self.num_inputs = Coral.num_inputs + self.morphogens.n_morphogens
        self.polyp_inputs = [0 for _ in range(self.num_inputs+1)]
        self.polyp_inputs[self.num_inputs] = 1 # The last input is always used as bias.

        self.polyp_verts = [None] * self.max_polyps
        self.polyp_light = np.zeros(self.max_polyps)
        self.polyp_flow = np.zeros(self.max_polyps)
        self.polyp_pos = np.zeros((self.max_polyps, 3))
        self.polyp_normal = np.zeros((self.max_polyps, 3))
        self.polyp_last_pos = np.zeros((self.max_polyps, 3))
        self.polyp_gravity = np.zeros(self.max_polyps)
        self.poly_collided = np.zeros((self.max_polyps, 3), dtype='uint8')

        for vert in self.mesh.verts:
            self.createPolyp(vert)

        self.updateAttributes()
        self.age = 0

    def __str__(self):
        s = 'Coral: {npolyps:%i, volume:%f}' % (len(self.n_polyps), self.volume)
        return s

    def step(self):
        self.polypsGrow()
        self.updateAttributes()
        self.age += 1

    def polypsGrow(self):
        """ Calculate the changes to coral by neural network.
        """
        self.total_gametes = 0

        self.polyp_last_pos[:, :] = self.polyp_pos

        for i in range(self.n_polyps):
            self.createPolypInputs(i)
            self.network.Flush() # Compute feed-forward network results.
            self.network.Input(self.polyp_inputs)
            self.network.ActivateFast()
            output = self.network.Output()

            growth_energy = output[0]
            self.total_gametes += 1 - growth_energy
            # Move in nomral direction by growth amount.
            growth = growth_energy * self.growth_scalar
            self.polyp_pos[i] += self.polyp_normal[i] * growth

            assert not isnan(self.polyp_pos[i, 0])
            assert not isnan(self.polyp_pos[i, 1])
            assert not isnan(self.polyp_pos[i, 2])

            for mi in range(self.morphogens.n_morphogens):
                v_mi = self.morphogens.V[mi, i]
                self.morphogens.V[mi, i] =  max(v_mi, v_mi + output[mi + 1])

        self.handleCollisions()

    def updateAttributes(self):
        self.polypDivision() # Divide mesh and create new polyps.
        relax_mesh(self.mesh) # Update mesh
        self.mesh.calculateNormals()
        self.mesh.calculateCurvature()

        if self.n_polyps < self.max_polyps:
            calculate_light(self) # Update the light
            calculate_gravity(self)
            self.morphogens.update(100) # Update the morphogens.
        # self.calculate_flow() # TODO
        # self.diffuseEnergy() # TODO

    def createPolypInputs(self, i):
        """ Map polyp stats to nerual input in [-1, 1] range. """
        assert self.polyp_verts[i]
        self.polyp_inputs[0] = (self.polyp_light[i] * 2) - 1
        self.polyp_inputs[1] = (self.polyp_verts[i].curvature * 2) - 1
        self.polyp_inputs[2] = (self.polyp_gravity[i] * 2) - 1

        for mi in range(self.morphogens.n_morphogens):
            self.polyp_inputs[3+mi] = (self.morphogens.U[mi, i] * 2) - 1

    def handleCollisions(self):
        collisions = findCollisions(self.mesh)

        for vi, collided in enumerate(collisions):
            if collided:
                vert = self.mesh.verts[vi]
                vert.p[:] = self.polyp_last_pos[vi]
                self.poly_collided[vi] = 1

    def createPolyp(self, vert):
        if self.n_polyps == self.max_polyps:
            return
        i = self.n_polyps
        self.n_polyps += 1
        vert.data['polyp'] = i
        self.polyp_pos[i, :] = vert.p
        vert.normal = self.polyp_normal[i]
        vert.p = self.polyp_pos[i]
        self.polyp_verts[i] = vert

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
            split(self.mesh, face)

        # divide_adaptive(self.mesh, self.max_face_area)
        for vert in self.mesh.verts:
            if 'polyp' not in vert.data:
                self.createPolyp(vert)

        # assert self.n_polyps <= self.max_polyps
        # assert len(self.mesh.verts) <= self.max_polyps

    def export(self, out):
        """ Export the coral to .coral.obj file
            A .coral.obj file is a 3d mesh with polyp specific information.
            it is a compatable superset of the .obj file format.
            In addition to the content of a .obj file a .coral file has:

            1. A header row that begins with '#coral' that lists space
                deiminated polyp attributes
            2. A line that begins with 'c' for each vert that contains values for
                polyp for each attribute. Ordered the same as the vertices.
        """
        header = [ 'light', 'flow', 'u1' ]

        out.write('#Exported from coral_growth\n')
        out.write('#coral: ' + ' '.join(header) + '\n')

        mesh_data = self.mesh.export()

        id_to_indx = dict()

        for i, vert in enumerate(self.mesh.verts):
            out.write('v %f %f %f\n' % (tuple(vert.p)))
            id_to_indx[vert.id] = i

        out.write('\n\n')

        for vn in mesh_data['vertice_normals']:
            out.write('vn %f %f %f\n' % tuple(vn))

        polyp_attributes = [None] * self.n_polyps

        # for polyp in self.polyps:
        for i in range(self.n_polyps):
            indx = id_to_indx[self.polyp_verts[i].id]
            polyp_attributes[indx] = [ self.polyp_light[i], self.polyp_flow[i] ]
            polyp_attributes[indx].append(self.morphogens.U[0, i])

        for attributes in polyp_attributes:
            out.write('c ' + ' '.join(map(str, attributes)) + '\n')

        out.write('\n')

        for face in mesh_data['faces']:
            out.write('f %i %i %i\n' % tuple(face+1))
