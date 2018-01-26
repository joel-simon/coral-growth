from __future__ import print_function
from math import isnan, sqrt, floor, pi
import numpy as np
import time
import pickle
from collections import defaultdict

from cymesh.mesh import Mesh
from cymesh.subdivision.sqrt3 import divide_adaptive, split
from cymesh.collisions.findCollisions import findCollisions
from cymesh.operators.relax import relax_mesh

from coral_growth.grow_polyps import grow_polyps
from coral_growth.modules import light, gravity
from coral_growth.modules import flowx as flow
from coral_growth.modules.morphogens import Morphogens
from coral_growth.modules.collisions import MeshCollisionManager

class Coral(object):
    num_inputs = 4 # [light, gravity, collection, extra-bias-bit]
    num_outputs = 1

    def __init__(self, obj_path, network, net_depth, traits, params):
        self.mesh = Mesh.from_obj(obj_path)
        self.network = network
        self.net_depth = net_depth
        self.params = params
        self.C = params.C
        self.n_signals = params.n_signals
        self.n_memory = params.n_memory
        self.max_polyps = params.max_polyps
        self.max_growth = params.max_growth
        self.morphogens = Morphogens(self, traits, params.n_morphogens)
        self.morphogen_steps = params.morphogen_steps
        self.light_amount = params.light_amount
        self.n_morphogens = params.n_morphogens
        self.morphogen_thresholds = params.morphogen_thresholds

        # Some parameters are evolved traits.
        self.signal_decay = np.array([ traits['signal_decay%i'%i] \
                                        for i in range(params.n_signals) ])
        self.signal_range = np.array([ traits['signal_range%i'%i] \
                                        for i in range(params.n_signals) ], dtype='i')

        # Constants for simulation dependent on start mesh.
        self.target_edge_len = np.mean([e.length() for e in self.mesh.edges])
        self.polyp_size = self.target_edge_len * 0.5
        self.max_edge_len = self.target_edge_len * 1.3
        self.max_face_area = np.mean([f.area() for f in self.mesh.faces]) * params.max_face_growth
        self.voxel_length = self.target_edge_len * .8

        # Update the input and output for the variable in/outs.
        self.num_inputs = Coral.num_inputs + self.n_memory + self.n_signals + \
                               self.n_morphogens * (self.morphogen_thresholds-1)
        self.num_outputs = Coral.num_outputs + self.n_memory + self.n_signals + self.n_morphogens

        self.function_times = defaultdict(int)
        assert network.NumInputs() == self.num_inputs, (network.NumInputs(), self.num_inputs)
        assert network.NumOutputs() == self.num_outputs

        # Data
        self.age = 0
        self.collection = 0
        self.light = 0
        self.n_polyps = 0
        self.start_collection = None
        self.polyp_inputs = np.zeros((self.max_polyps, self.num_inputs))
        self.polyp_verts = [None] * self.max_polyps
        self.polyp_light = np.zeros(self.max_polyps)
        self.polyp_flow = np.zeros(self.max_polyps)
        self.polyp_pos = np.zeros((self.max_polyps, 3))
        self.polyp_pos_next = np.zeros((self.max_polyps, 3))
        self.polyp_pos_past = np.zeros((self.max_polyps, 3))
        self.polyp_normal = np.zeros((self.max_polyps, 3))
        self.polyp_gravity = np.zeros(self.max_polyps)
        self.polyp_collection = np.zeros(self.max_polyps)
        self.polyp_collided = np.zeros(self.max_polyps, dtype='uint8')
        # self.polyp_memory = np.zeros((self.max_polyps), dtype='uint32')
        # self.polyp_memory = np.zeros((self.max_polyps, self.n_memory))
        self.polyp_signals = np.zeros((self.max_polyps, self.params.n_signals))

        self.collisionManager = MeshCollisionManager(self.mesh, self.polyp_pos,\
                                                     self.polyp_size)
        for vert in self.mesh.verts:
            self.createPolyp(vert)

        self.updateAttributes()
        self.start_light = self.light
        self.start_collection = self.collection

    def __str__(self):
        s = 'Coral: {npolyps:%i}' % (len(self.n_polyps))
        return s

    def step(self):
        t1 = time.time()
        self.morphogens.U[:, :] = 0
        self.morphogens.V[:, :] = 0

        grow_polyps(self)
        # TODO: clean up this mess below :(
        self.polyp_pos_past[:] = self.polyp_pos[:]
        self.polyp_pos[:] = self.polyp_pos_next[:]
        self.mesh.calculateDefect()
        self.polyp_pos[:] = self.polyp_pos_past[:]

        self.function_times['grow_polyps_p1'] += time.time() - t1
        t1 = time.time()

        for i in range(self.n_polyps):
            vert = self.mesh.verts[i]

            if self.polyp_pos_next[i, 1] < 0:
                continue

            if abs(self.polyp_verts[i].defect) > self.params.max_defect:
                continue

            self.polyp_collided[i] = self.collisionManager.attemptVertUpdate(vert.id, self.polyp_pos_next[i])

        self.function_times['grow_polyps_p2'] += time.time() - t1

        assert not np.isnan(np.sum(self.polyp_pos[:self.n_polyps])), 'NaN position :\'('

        t1 = time.time()
        relax_mesh(self.mesh)
        self.function_times['relax_mesh'] += time.time() - t1

        t1 = time.time()
        self.polypDivision() # Divide mesh and create new polyps.
        self.function_times['polyp_division'] += time.time() - t1

        self.updateAttributes()
        np.nan_to_num(self.polyp_gravity, copy=False)
        np.nan_to_num(self.polyp_light, copy=False)

        self.age += 1

    def updateAttributes(self):
        self.mesh.calculateNormals()
        self.mesh.calculateDefect()

        t1 = time.time()
        light.calculate_light(self) # Update the light
        self.polyp_light[self.polyp_light != 0] -= .5
        self.polyp_light *= 2 # all light values go from 0-1
        self.function_times['calculate_light'] += time.time() - t1

        t1 = time.time()
        self.flow_data = flow.calculate_collection(self, radius=3, \
                                        capture_percent=.05, fluid_diffusion=0.1)
        self.polyp_collection *= 50
        self.function_times['calculate_collection'] += time.time() - t1

        gravity.calculate_gravity(self)
        self.polyp_signals *= self.signal_decay

        t1 = time.time()
        self.morphogens.update(self.morphogen_steps) # Update the morphogens.
        self.function_times['morphogens.update'] += time.time() - t1

        self.calculateEnergy()

    def calculateEnergy(self):
        self.light = 0
        self.collection = 0

        boost = self.polyp_pos[:self.n_polyps, 1] ** self.params.height_boost
        np.nan_to_num(boost, copy=False)

        for face in self.mesh.faces:
            area = face.area()
            vertices = face.vertices()
            self.light += area * sum(self.polyp_light[v.id]*boost[v.id] for v in vertices) / 3
            self.collection += area * sum(self.polyp_collection[v.id]*boost[v.id] for v in vertices) / 3

        if self.start_collection:
            self.collection /= self.start_collection
            self.light /= self.start_light

        self.energy = self.light*self.light_amount + \
                      self.collection*(1-self.light_amount)

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

        neighbors = vert.neighbors()
        for vert_n in neighbors:
            for i in range(self.n_signals):
                self.polyp_signals[idx, i] += self.polyp_signals[vert_n.id, i]
        self.polyp_signals[idx] /= len(neighbors)

        self.collisionManager.newVert(vert.id)

        assert vert.id == idx

    def polypDivision(self):
        """ Update the mesh and create new polyps.
        """
        for face in self.mesh.faces:
            if face.area() > self.max_face_area:
                split(self.mesh, face, max_vertices=self.max_polyps)

            if self.n_polyps == self.max_polyps:
                break

        for vert in self.mesh.verts:
            if 'polyp' not in vert.data:
                self.createPolyp(vert)

    def fitness(self, verbose=False):
        if verbose:
            print('Light=', self.light)
            print('Collection=', self.collection)
            print('Energy=', self.energy)

        return self.energy

    def export(self, path):
        """ Export the coral to .coral.obj file
            A .coral.obj file is a 3d mesh with polyp specific information.
            it is a compatable superset of the .obj file format.
            In addition to the content of a .obj file a .coral.obj file has:

            1. A header row that begins with '#coral' that lists space
                deliminated polyp attributes
            2. A line that begins with 'c' for each vert that contains values
                for each attribute. Ordered the same as the vertices.
        """
        out = open(path, 'w+')

        header = [ 'light', 'collection', 'gravity', 'curvature' ]#, 'memory']

        for i in range(self.n_morphogens):
            header.append( 'mu_%i' % i )

        for i in range(self.n_signals):
            header.append( 'sig_%i' % i )

        # for i in range(self.n_memory):
        #     header.append( 'mem_%i' % i )

        out.write('#Exported from coral_growth\n')
        out.write('#attr light:%f collection:%f energy:%f\n' % \
                                     (self.light, self.collection, self.energy))
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

        # for i in range(self.n_polyps):
        #     self.polyp_collided[i] = abs(self.polyp_verts[i].defect) > self.params.max_defect

        for i in range(self.n_polyps):
            indx = id_to_indx[self.polyp_verts[i].id]

            polyp_attributes[indx] = [ self.polyp_light[i],
                                       self.polyp_collection[i],
                                       self.polyp_gravity[i],
                                       abs(self.polyp_verts[i].defect)/8*pi,
                                       # self.polyp_collided[i]
                                       ]

            for j in range(self.n_morphogens):
                polyp_attributes[indx].append(self.morphogens.U[j, i])

            polyp_attributes[indx].extend(self.polyp_signals[i])
            # polyp_attributes[indx].extend(self.polyp_memory[i])

            assert len(polyp_attributes[indx]) == len(header)

        for attributes in polyp_attributes:
            out.write('c ' + ' '.join(map(str, attributes)) + '\n')

        out.write('\n')

        for face in mesh_data['faces']:
            out.write('f %i %i %i\n' % tuple(face + 1))

        # f = open(path+'.grid.p', 'wb')
        # pickle.dump((self.voxel_length, self.voxel_grid), f)
        # f.close()

        # f = open(path+'.flow_grid.p', 'wb')
        # pickle.dump((self.voxel_length, self.flow_data), f)
        # f.close()
