from __future__ import print_function
from coral_growth.growth_form import GrowthForm

class SurfaceArea(GrowthForm):
    def __init__(self, obj_path, network, net_depth, traits, params):
        attributes = []
        super().__init__(attributes, obj_path, network, net_depth, traits, params)

    def fitness(self):
        # The surface area.
        return sum(f.area() for f in self.mesh.faces)
