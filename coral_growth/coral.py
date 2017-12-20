# cython: boundscheck=False
# cython: wraparound=True
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True

from __future__ import print_function
from math import isnan, sqrt, floor
import numpy as np
from pykdtree.kdtree import KDTree
from random import shuffle

from cymesh.mesh import Mesh
from cymesh.subdivision.sqrt3 import divide_adaptive, split
from cymesh.collisions.findCollisions import findCollisions
# from cymesh.operators.relax import relax_mesh, relax_mesh_cotangent, relax_vert_cotangent

from coral_growth.grow_polyps import grow_polyps
from coral_growth.modules import light, gravity
from coral_growth.modules.morphogens import Morphogens
from coral_growth.modules.collisions import MeshCollisionManager

# def normed(x):
#     return x / np.linalg.norm(x)

class Coral(object):
    num_inputs = 4 # [light, curvature, gravity, extra-bias-bit]
    num_outputs = 1

    def __init__(self, obj_path, network, traits, params):
        self.mesh = Mesh.from_obj(obj_path)
        self.network = network

        self.vc = params.vc
        self.n_memory = params.polyp_memory
        self.max_polyps = params.max_polyps
        self.morphogens = Morphogens(self, traits, params.n_morphogens)
        self.morphogen_steps = params.morphogen_steps
        self.light_amount = params.light_amount
        self.n_morphogens = params.n_morphogens
        self.growth_scalar = params.growth_scalar
        self.morph_thresholds = params.morph_thresholds

        # Some parameters are evolved traits.
        self.spring_strength = traits['spring_strength']

        self.target_edge_len = np.mean([e.length() for e in self.mesh.edges])
        self.polyp_size = self.target_edge_len * 0.5
        self.max_edge_len = self.target_edge_len * params.max_face_growth
        mean_face = np.mean([f.area() for f in self.mesh.faces])
        self.max_face_area = mean_face * params.max_face_growth

        self.n_polyps = 0
        self.num_inputs = Coral.num_inputs + self.n_memory + self.n_morphogens * (self.morph_thresholds-1)
        self.num_outputs = Coral.num_outputs + self.n_memory + self.n_morphogens

        assert network.NumInputs() == self.num_inputs
        assert network.NumOutputs() == self.num_outputs

        # Data
        self.polyp_inputs = np.zeros((self.max_polyps, self.num_inputs))
        self.polyp_verts = [None] * self.max_polyps
        self.polyp_light = np.zeros(self.max_polyps)
        self.polyp_energy = np.zeros(self.max_polyps)
        self.polyp_flow = np.zeros(self.max_polyps)
        self.polyp_pos = np.zeros((self.max_polyps, 3))
        self.polyp_pos_next = np.zeros((self.max_polyps, 3))
        self.polyp_normal = np.zeros((self.max_polyps, 3))
        # self.polyp_last_pos = np.zeros((self.max_polyps, 3))
        self.polyp_gravity = np.zeros(self.max_polyps)
        self.polyp_collided = np.zeros(self.max_polyps, dtype='uint8')
        assert self.n_memory <= 32
        self.polyp_memory = np.zeros((self.max_polyps), dtype='uint32')

        self.collisionManager = MeshCollisionManager(self.mesh, self.polyp_pos, self.polyp_size)

        for vert in self.mesh.verts:
            self.createPolyp(vert)

        self.mesh.calculateNormals()
        self.mesh.calculateCurvature()
        self.updateAttributes()

        light, capture, volume = self.fitnessAttributes()
        self.start_light = light
        self.start_capture = capture
        self.start_volume = volume

        self.age = 0

    def __str__(self):
        s = 'Coral: {npolyps:%i}' % (len(self.n_polyps))
        return s

    def step(self):
        grow_polyps(self)
        self.polypDivision() # Divide mesh and create new polyps.
        self.updateAttributes()
        self.age += 1

    # def correctGrowth(self):
    #     self.mesh.calculateNormals()
    #     self.mesh.calculateCurvature()

    #     self.max_curvature = .3

    #     for vi in range(self.n_polyps):
    #         vert = self.mesh.verts[vi]
    #         invalid = False

    #         if self.polyp_pos[vi, 1] < 0:
    #             invalid = True
    #         elif abs(vert.curvature) > self.max_curvature:
    #             invalid = True

    #         if invalid:
    #             vert.p[:] = self.polyp_last_pos[vi]

    def updateAttributes(self):

        self.mesh.calculateNormals()
        self.mesh.calculateCurvature()
        light.calculate_light(self) # Update the light

        self.polyp_light[self.polyp_light != 0] -= .5
        self.polyp_light *= 2 # all light values go from 0-1

        # self.polyp_light *= self.light_amount
        # (self.light_bottom + (1-self.light_bottom)*self.polyp_pos[:,1,:] / self.world_depth)

        gravity.calculate_gravity(self)
        self.morphogens.update(self.morphogen_steps) # Update the morphogens.

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

        self.collisionManager.newVert(vert.id)

        assert vert.id == idx

    def polypDivision(self):
        """ Update the mesh and create new polyps.
        """
        for face in self.mesh.faces:
            l1 = face.he.edge.length()
            l2 = face.he.next.edge.length()
            l3 = face.he.next.next.edge.length()
            if max(l1, l2, l3) > self.max_edge_len:
                split(self.mesh, face, max_vertices=self.max_polyps)

            elif face.area() > self.max_face_area:
                split(self.mesh, face, max_vertices=self.max_polyps)

            if self.n_polyps == self.max_polyps:
                break

        for vert in self.mesh.verts:
            if 'polyp' not in vert.data:
                self.createPolyp(vert)

    def fitnessAttributes(self):
        light = 0
        capture = 0
        tree = KDTree(self.polyp_pos[:self.n_polyps], leafsize=16)
        query = np.zeros((1, 3))

        for face in self.mesh.faces:
            area = face.area()

            if isnan(area):
                area = 0

            p = face.midpoint()
            if p[1] > .1:
                query[0] = p
                d, indx = tree.query(query, k=15)
                capture += area * np.mean(d)

            light += area * sum(self.polyp_light[v.id] for v in face.vertices())

        return light, capture, self.mesh.volume()

    def fitness(self):
        light, capture, volume = self.fitnessAttributes()

        # Normalized values (values for seed).
        light /= self.start_light
        capture /= self.start_capture
        volume /= self.start_volume

        la = self.light_amount
        fitness = (la*light + (1-la)*capture) / (volume**self.vc)

        assert not isnan(fitness), (light, capture, volume)

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

        header = [ 'light', 'gravity', 'curvature', 'memory', 'collided']
        for i in range(self.n_morphogens):
            header.append( 'u%i' % i )

        out.write('#Exported from coral_growth\n')
        out.write('#attr:polyp_size:%f\n' %self.polyp_size)
        out.write('#coral ' + ' '.join(header) + '\n')

        mesh_data = self.mesh.export()

        id_to_indx = dict()

        for i, vert in enumerate(self.mesh.verts):
            r, g, b = 0, 0, 0

            if self.n_morphogens > 0:
                g = self.morphogens.U[0, i]

            if self.n_morphogens > 1:
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
                                       self.polyp_memory[i],
                                       self.polyp_collided[i] ]

            for j in range(self.n_morphogens):
                polyp_attributes[indx].append(self.morphogens.U[j, i])

            assert len(polyp_attributes[indx]) == len(header)

        for attributes in polyp_attributes:
            out.write('c ' + ' '.join(map(str, attributes)) + '\n')

        out.write('\n')

        for face in mesh_data['faces']:
            out.write('f %i %i %i\n' % tuple(face + 1))
