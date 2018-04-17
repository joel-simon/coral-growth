from math import sqrt
import numpy as np
from coral_growth.growth_form import GrowthForm

class TestForm(GrowthForm):
    def __init__(self, obj_path, network, net_depth, traits, params):
        n_inputs, n_outputs = TestForm.calculate_inouts(params)
        self.n_inputs = n_inputs
        self.n_outputs = n_outputs
        attributes = []
        super().__init__(attributes, obj_path, network, net_depth, traits, params)

    @classmethod
    def calculate_inouts(cls, params):
        n_inputs = 4 # energy, gravity, curvature, extra-bias-bit.
        n_outputs = 1 # growth.
        n_inputs += params.n_signals + (4 * params.use_polar_direction) + \
                     params.n_morphogens * (params.morphogen_thresholds-1)
        n_outputs += params.n_signals + params.n_morphogens

        return n_inputs, n_outputs

    def fitness(self):
        fitness = 0

        com = np.mean(self.node_pos[:self.n_nodes], axis=0)

        for v in self.mesh.verts:
            diff = com - v.p
            dist = sqrt(diff[0]*diff[0] + diff[1]*diff[1] + diff[2]*diff[2])
            fitness += max(0, v.curvature) * dist

        return fitness / self.n_nodes




