from math import sqrt, pi
import numpy as np

from cymesh.shape_features import d2_features, a3_features
from coral_growth.growth_form import GrowthForm

class ShapeVectorForm(GrowthForm):
    def __init__(self, obj_path, network, net_depth, traits, params):
        attributes = []
        super().__init__(attributes, obj_path, network, net_depth, traits, params)

    def fitness(self):
        return 1.0
        # n = 1024*1024
        # d2 = d2_features(self.mesh, n_points=n, n_bins=32, hrange=(0.0, 3.0))
        # std = np.std(d2)
        # # std = np.std(a3_features(self.mesh, n_points=n, n_bins=32, vmin=0.0, vmax=pi))
        # return std
