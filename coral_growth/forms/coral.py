from __future__ import print_function
import numpy as np
# from pykdtree.kdtree import KDTree

from coral_growth.modules.flowx import *
from coral_growth.modules.flowx2 import *

from coral_growth.modules import light
from coral_growth.growth_form import GrowthForm

class Coral(GrowthForm):
    def __init__(self, obj_path, network, net_depth, traits, params):
        # Corals calculate light and flow on every node to get growth energy.
        n_inputs, n_outputs = Coral.calculate_inouts(params)
        self.n_inputs = n_inputs
        self.n_outputs = n_outputs

        self.node_light = np.zeros(params.max_nodes)
        self.node_collection = np.zeros(params.max_nodes)
        super().__init__(2, obj_path, network, net_depth, traits, params)

    @classmethod
    def calculate_inouts(cls, params):
        n_inputs = 6 # energy, gravity, curvature, extra-bias-bit.
        n_outputs = 1 # growth.

        n_inputs += params.n_signals + (4 * params.use_polar_direction) + \
                     params.n_morphogens * (params.morphogen_thresholds-1)
        n_outputs += params.n_signals + params.n_morphogens

        return n_inputs, n_outputs

    def calculateEnergy(self):
        light.calculate_light(self) # Update the light
        np.nan_to_num(self.node_light, copy=False)
        self.calculateCollection(radius=self.params.collection_radius)

        bott = self.params.gradient_bottom
        height = self.params.gradient_height
        if height != 0:
            for i in range(self.n_nodes):
                scale = bott + min(1, self.node_pos[i, 1] / height) * (1 - bott)
                self.node_collection[i] *= scale
                self.node_light[i] *= scale

        self.light = 0
        self.collection = 0
        self.energy = 0
        light_amount = self.params.light_amount

        for i in range(self.n_nodes):
            self.light += self.node_light[i]
            self.collection += self.node_collection[i]
            self.node_attributes[i, 0] = self.light
            self.node_attributes[i, 1] = self.collection
            energy = light_amount * self.node_light[i] + \
                                   (1-light_amount)*self.node_collection[i]
            self.node_energy[i] = energy
            self.energy += energy

    def calculateCollection(self, radius):
        node_voxels, voxel_grid, min_v = create_voxel_grid(self)
        voxel_grid = np.array(voxel_grid).astype('uint8')
        calculate_collection(self.node_collection, node_voxels, voxel_grid, radius)

        for i in range(self.n_nodes):
            self.node_collection[i] *= 100

    def fitness(self):
        return self.energy
