import math
import numpy as np
import time
from .flowx import *

def calculate_collection(coral, export=False):
    polyp_voxel, voxel_grid, min_v = create_voxel_grid(coral)
    flow_grid, paths = calculate_flow(voxel_grid, n_iters=5, export=export)
    calculate_collection_from_flow(coral.polyp_collection, polyp_voxel, flow_grid, 2)
    coral.polyp_collection[:coral.n_polyps] *= 5

    if export:
        return np.array(voxel_grid), np.array(flow_grid), np.array(min_v), paths
    else:
        return None
