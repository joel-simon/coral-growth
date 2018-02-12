from __future__ import print_function
from math import isnan, sqrt, floor, pi
import numpy as np
import time
import pickle
from collections import defaultdict

from pykdtree.kdtree import KDTree

from cymesh.mesh import Mesh
from cymesh.subdivision.sqrt3 import divide_adaptive, split
from cymesh.collisions.findCollisions import findCollisions
from cymesh.operators.relax import relax_mesh

from coral_growth.grow_polyps import grow_polyps
from coral_growth.modules import light, gravity
from coral_growth.modules import flow as flow
from coral_growth.modules.morphogens import Morphogens
from coral_growth.modules.collisions import MeshCollisionManager

class Coral(object):
    num_inputs = 3 # [light, collection, extra-bias-bit]
    num_outputs = 1

    def __init__(self, obj_path, network, net_depth, traits, params, save_flow_data=False):
        self.mesh = Mesh.from_obj(obj_path)
        self.network = network
        self.net_depth = net_depth
        self.params = params
        self.save_flow_data = save_flow_data
        self.C = params.C
        self.n_signals = params.n_signals
        self.n_memory = params.n_memory
        self.max_polyps = params.max_polyps
        self.max_growth = params.max_growth
        self.morphogens = Morphogens(self, traits, params.n_morphogens)
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
                               self.n_morphogens * (self.morphogen_thresholds-1) + \
                               (4 * params.use_polar_direction)
        self.num_outputs = Coral.num_outputs + self.n_memory + self.n_signals + self.n_morphogens

        self.function_times = defaultdict(int)

        assert network.NumInputs() == self.num_inputs, \
                   ("Inputs do not match", network.NumInputs(), self.num_inputs)
        assert network.NumOutputs() == self.num_outputs

        # Data
        self.age = 0
        self.collection = 0
        self.light = 0
        self.n_polyps = 0
        self.start_collection = None
        self.volume = None
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
        grow_polyps(self)
        self.smoothSharp()
        self.function_times['grow_polyps_p1'] += time.time()-t1
        relax_mesh(self.mesh)
        self.polypDivision() # Divide mesh and create new polyps.
        self.updateAttributes()
        self.age += 1

    def smoothSharp(self):
        self.mesh.calculateDefect()
        for vert in self.mesh.verts:
            if abs(vert.defect) > self.params.max_defect:
                avg = np.zeros(3)
                neighbors = vert.neighbors()
                for vert2 in neighbors:
                    avg += vert2.p
                vert.p += avg / len(neighbors)
                vert.p[0] *= .5
                vert.p[1] *= .5
                vert.p[2] *= .5

    def updateAttributes(self):
        self.mesh.calculateNormals()
        self.mesh.calculateDefect()

        t1 = time.time()
        light.calculate_light(self) # Update the light
        self.polyp_light[self. polyp_light!= 0] -= .5
        self.polyp_light *= 2 # all light values go from 0-1

        if self.params.gradient_height > 0:
            below = self.polyp_pos[:, 1] < self.params.gradient_height
            height_scale = (self.polyp_pos[below, 1] / self.params.gradient_height)
            self.polyp_light[below] *= height_scale
        self.function_times['calculate_light'] += time.time() - t1

        t1 = time.time()
        self.flow_data = flow.calculate_collection(self, export=self.save_flow_data)
        if self.params.gradient_height > 0:
            self.polyp_collection[below] *= height_scale
        self.function_times['calculate_collection'] += time.time() - t1

        gravity.calculate_gravity(self)
        self.polyp_signals *= (1 - self.signal_decay)
        np.clip(self.polyp_signals, 0, 1, out=self.polyp_signals)

        t1 = time.time()
        self.morphogens.update(self.params.morphogen_steps)
        self.function_times['morphogens.update'] += time.time() - t1

        t1 = time.time()
        self.calculateEnergy()
        self.function_times['calculateEnergy'] += time.time() - t1

        self.volume = self.mesh.volume()
        np.nan_to_num(self.polyp_gravity, copy=False)
        np.nan_to_num(self.polyp_light, copy=False)

    def calculateEnergy(self):
        self.light = 0
        self.collection = 0

        for face in self.mesh.faces:
            area = face.area()
            v1, v2, v3 = face.vertices()
            self.light += area / 3 * (self.polyp_light[v1.id] + \
                                      self.polyp_light[v2.id] +
                                      self.polyp_light[v2.id])
            self.collection += area / 3 * (self.polyp_collection[v1.id] + \
                                           self.polyp_collection[v2.id] +
                                           self.polyp_collection[v2.id])
        if self.start_collection:
            self.collection /= self.start_collection
            self.light /= self.start_light

        self.energy = self.light*self.light_amount + self.collection*(1-self.light_amount)

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
        n = 0
        for vert_n in neighbors:
            if self.polyp_signals[vert_n.id].sum() != 0:
                for i in range(self.n_signals):
                    self.polyp_signals[idx, i] += self.polyp_signals[vert_n.id, i]
            n += 1
        self.polyp_signals[idx] /= n

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
            print('n_polyps=',self.n_polyps)
            print('Light=', self.light)
            print('Collection=', self.collection)
            print('Energy=', self.energy)
            print('Volume=', self.volume)

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
        header = []

        for i in range(self.n_morphogens):
            header.append( 'mu_%i' % i )
        for i in range(self.n_signals):
            header.append( 'sig_%i' % i )
        # for i in range(self.n_memory):
        #     header.append( 'mem_%i' % i )

        header.extend([ 'light', 'collection', 'curvature' ])
        out.write('#Exported from coral_growth\n')
        out.write('#attr light:%f collection:%f energy:%f\n' % \
                                     (self.light, self.collection, self.energy))
        out.write('#coral ' + ' '.join(header) + '\n')
        mesh_data = self.mesh.export()
        id_to_indx = { vert.id:i for i, vert in enumerate(self.mesh.verts) }

        # Write coral data lines.
        p_attributes = [None] * self.n_polyps
        for i in range(self.n_polyps):
            indx = id_to_indx[self.polyp_verts[i].id]
            p_attributes[indx] = []

            for j in range(self.n_morphogens):
                p_attributes[indx].append(self.morphogens.U[j, i])

            p_attributes[indx].extend(self.polyp_signals[i])
            p_attributes[indx].extend([ self.polyp_light[i], self.polyp_collection[i],
                                        abs(self.polyp_verts[i].defect)/8*pi ])

            assert len(p_attributes[indx]) == len(header)


        # Write vertices (position and color)
        for i, vert in enumerate(self.mesh.verts):
            r, g, b = p_attributes[i][:3]
            # r, g, b = 0, 0, 0
            # if self.n_morphogens > 0:
            #     g = self.morphogens.U[0, i]
            # if self.n_morphogens > 1:
            #     b = self.morphogens.U[1, i]
            out.write('v %f %f %f %f %f %f\n' % (tuple(vert.p)+(r, g, b)))
            id_to_indx[vert.id] = i
        out.write('\n\n')

        for attributes in p_attributes:
            out.write('c ' + ' '.join(map(str, attributes)) + '\n')

        # Write Faces/
        out.write('\n')
        for face in mesh_data['faces']:
            out.write('f %i %i %i\n' % tuple(face + 1))
        out.close()

        if self.save_flow_data:
            f = open(path+'.flow_grid.p', 'wb')
            pickle.dump((self.voxel_length, self.flow_data), f)
            f.close()
