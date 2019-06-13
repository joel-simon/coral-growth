from math import sqrt
import numpy as np
from pykdtree.kdtree import KDTree
from coral_growth.growth_form import GrowthForm

class TestForm(GrowthForm):
    def __init__(self, obj_path, network, net_depth, traits, params):
        attributes = []
        super().__init__(attributes, obj_path, network, net_depth, traits, params)

    def fitness(self):
        pos = np.asarray(self.node_pos[self.n_nodes])
        kd_tree = KDTree(pos)
        dist, _ = kd_tree.query(pos, k=30)
        fitness = np.mean(dist)

        return fitness

    # def fitness(self):
    #     fitness = 0

    #     com = np.mean(self.node_pos[:self.n_nodes], axis=0)

    #     for v in self.mesh.verts:
    #         diff = com - v.p
    #         dist = sqrt(diff[0]*diff[0] + diff[1]*diff[1] + diff[2]*diff[2])
    #         fitness += max(0, v.curvature) * dist

    #     return fitness / self.n_nodes


    # def fitness(self):
    #     bbox = self.mesh.boundingBox()
    #     volume = (bbox[1]-bbox[0]) * (bbox[3]-bbox[2]) * (bbox[5]-bbox[4])
    #     return volume
