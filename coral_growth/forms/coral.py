from __future__ import print_function
import numpy as np

from coral_growth.modules.flowx import *
from coral_growth.modules.flowx2 import *

from coral_growth.modules import light
from coral_growth.growth_form import GrowthForm

class Coral(GrowthForm):
    def __init__(self, obj_path, network, net_depth, traits, params):
        # Corals calculate light and flow on every node to get growth energy.
        self.node_light = np.zeros(params.max_nodes)
        self.node_collection = np.zeros(params.max_nodes)
        attributes = ['light', 'collection']
        super().__init__(attributes, obj_path, network, net_depth, traits, params)

    @classmethod
    def calculate_inouts(cls, params):
        n_inputs, n_outputs = GrowthForm.calculate_inouts(params)
        n_inputs += 2 # Corals have two extra inputs, light and collection.
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
            self.node_attributes[i, 0] = self.node_light[i]
            self.node_attributes[i, 1] = self.node_collection[i]
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
