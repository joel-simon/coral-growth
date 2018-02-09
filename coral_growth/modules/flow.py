import math
import numpy as np
import time
from .flowx import *

def calculate_collection(coral, export=False):
    polyp_voxel, voxel_grid, min_v = create_voxel_grid(coral)

    flow_grid1, paths = calculate_flow(voxel_grid, n_iters=3, reverse=False, export=False)
    flow_grid2, paths = calculate_flow(voxel_grid, n_iters=3, reverse=True, export=False)

    # # Use swap axes for quick hack since I'm in a rush :(
    # voxel_grid = np.swapaxes(voxel_grid, 0, 2)
    # flow_grid3, paths = calculate_flow(voxel_grid, n_iters=3, reverse=False, export=False)
    # flow_grid4, paths = calculate_flow(voxel_grid, n_iters=3, reverse=True, export=False)
    # flow_grid3 = np.swapaxes(flow_grid3, 0, 2)
    # flow_grid4 = np.swapaxes(flow_grid4, 0, 2)
    flow_grid = np.asarray(flow_grid1) + flow_grid2# + flow_grid3 + flow_grid4

    calculate_collection_from_flow(coral.polyp_collection, polyp_voxel, flow_grid, 2)
    # np.clip(coral.polyp_collection, 0, 1, out=coral.polyp_collection)

    coral.polyp_collection *= 5
    # print(coral.polyp_collection[:coral.n_polyps].max())

    if export:
        voxel_grid = np.swapaxes(voxel_grid, 0, 2)
        return np.array(voxel_grid), np.array(flow_grid), np.array(min_v), paths
    else:
        return None
