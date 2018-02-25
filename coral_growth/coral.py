from __future__ import print_function
from math import isnan, sqrt, floor, pi
import numpy as np
from pykdtree.kdtree import KDTree

from cymesh.mesh import Mesh
from coral_growth.modules.morphogens import Morphogens
from coral_growth.modules.collisions import MeshCollisionManager
from coral_growth.modules.flowx import *
from coral_growth.modules.flowx2 import *

from cymesh.operators.relax import relax_mesh
from coral_growth.modules import light, gravity
# from coral_growth.modules import flow as flow
# from coral_growth.modules import flow as flow
from coral_growth.base_coral import BaseCoral

class Coral(BaseCoral):
    def __init__(self, obj_path, network, net_depth, traits, params):
        self.mesh = Mesh.from_obj(obj_path)
        self.network = network
        self.net_depth = net_depth
        self.params = params
        self.C = params.C
        self.n_signals = params.n_signals
        self.n_memory = params.n_memory
        self.max_polyps = params.max_polyps
        self.n_morphogens = params.n_morphogens

        self.morphogens = Morphogens(self, traits, params.n_morphogens)

        n_inputs, n_outputs = Coral.calculate_inouts(params)
        self.n_inputs = n_inputs
        self.n_outputs = n_outputs

        # Some parameters are evolved traits.
        self.traits = traits
        self.signal_decay = np.array([ traits['signal_decay%i'%i] \
                                       for i in range(params.n_signals) ])

        # Constants for simulation dependent on start mesh.
        self.target_edge_len = np.mean([e.length() for e in self.mesh.edges])
        self.polyp_size = self.target_edge_len * 0.5
        self.max_edge_len = self.target_edge_len * 1.3
        self.max_face_area = np.mean([f.area() for f in self.mesh.faces]) * params.max_face_growth
        self.voxel_length = self.target_edge_len * .8

        # Data
        self.age = 0
        self.collection = 0
        self.light = 0
        self.n_polyps = 0
        self.volume = 0
        self.polyp_inputs = np.zeros((self.max_polyps, self.n_inputs))
        self.polyp_verts = [None] * self.max_polyps
        self.polyp_light = np.zeros(self.max_polyps)
        self.polyp_flow = np.zeros(self.max_polyps)
        self.polyp_energy = np.zeros(self.max_polyps)
        self.polyp_pos = np.zeros((self.max_polyps, 3))
        self.polyp_pos_next = np.zeros((self.max_polyps, 3))
        self.polyp_normal = np.zeros((self.max_polyps, 3))
        self.polyp_gravity = np.zeros(self.max_polyps)
        self.polyp_collection = np.zeros(self.max_polyps)
        self.polyp_collided = np.zeros(self.max_polyps, dtype='uint8')
        self.polyp_signals = np.zeros((self.max_polyps, self.params.n_signals))
        self.buffer = np.zeros((self.max_polyps)) # For intermediate calculation values.

        self.collisionManager = MeshCollisionManager(self.mesh, self.polyp_pos,\
                                                     self.polyp_normal, self.polyp_size)
        for vert in self.mesh.verts:
            self.createPolyp(vert)
        self.updateAttributes()

    @classmethod
    def calculate_inouts(cls, params):
        n_inputs = 6 # [light, collection, energy, gravity, curvature, extra-bias-bit]
        n_outputs = 1 # Growth

        n_inputs += params.n_memory + params.n_signals + \
                     params.n_morphogens * (params.morphogen_thresholds-1) + \
                     (4 * params.use_polar_direction)
        n_outputs += params.n_memory + params.n_signals + params.n_morphogens

        return n_inputs, n_outputs

    def step(self):
        self.growPolyps()

        for i in range(self.n_polyps):
            self.collisionManager.attemptVertUpdate(self.mesh.verts[i], self.polyp_pos_next[i])

        relax_mesh(self.mesh)
        self.smoothSharp()
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
                avg /= len(neighbors)
                vert.p[0] = .5 * vert.p[0] + .5 * avg[0]
                vert.p[1] = .5 * vert.p[1] + .5 * avg[1]
                vert.p[2] = .5 * vert.p[2] + .5 * avg[2]

    def updateAttributes(self):
        self.mesh.calculateNormals()
        self.mesh.calculateDefect()
        self.mesh.calculateCurvature()
        self.volume = self.mesh.volume()
        light.calculate_light(self) # Update the light
        self.calculateCollection(radius=5)
        self.calculateGravity()
        self.decaySignals()
        self.morphogens.update(self.params.morphogen_steps)
        self.applyHeightScale()
        self.calculateEnergy()
        self.diffuse()
        np.nan_to_num(self.polyp_light, copy=False)

    def calculateCollection(self, radius):
        polyp_voxels, voxel_grid, min_v = create_voxel_grid(self)
        voxel_grid = np.array(voxel_grid).astype('uint8')
        calculate_collection(self.polyp_collection, polyp_voxels, voxel_grid, radius)

        # points = np.asarray(self.polyp_pos[:self.n_polyps])
        # tree = KDTree(points)
        # dists, indx = tree.query(points, distance_upper_bound=max_compete, k=k+1)
        # distances = np.mean(dists[:, 1:], axis=1)
        # outside = flood_fill(np.asarray(voxel_grid).astype('uint8'))
        # collection = average_neighbors(outside, radius=5)

        # for i in range(self.n_polyps):
        #     vox = polyp_voxels[i]
        #     self.polyp_collection[i] = collection[ vox[0], vox[1], vox[2] ]# * distances[i] * 5

    def fitness(self, verbose=False):
        if verbose:
            print('n_polyps=',self.n_polyps)
            print('Light=', self.light)
            print('Collection=', self.collection)
            print('Energy=', self.energy)
            print('Volume=', self.volume)

        return self.energy


