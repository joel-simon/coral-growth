import math
import numpy as np
import time
# from .flowx import *
# from .flowx2 import *

from pykdtree.kdtree import KDTree

def calculate_collection(coral, k, max_compete):
    tree = KDTree(np.asarray(coral.polyp_pos[:coral.n_polyps]))
    dists, indx = tree.query(np.asarray(coral.polyp_pos[:coral.n_polyps]), k=k+1)
    np.clip(dists, 0, max_compete, out=dists)
    distances = np.mean(dists[:, 1:], axis=1)

    for i in range(coral.n_polyps):
        coral.polyp_collection[i] = 5*coral.polyp_verts[i].curvature * distances[i]

    # capture = np.mean(d)
    # foo = np.zeros((1, 3))
    # tree = KDTree(  )
    # dists, _ = tree.query(feature_arr, k=k+1)
    # sparseness_list = np.mean(dists[:, 1:], axis=1)

    # polyp_voxel, voxel_grid, min_v = create_voxel_grid(coral)
    # collection1, _, paths = calculate_collectionx(voxel_grid, 5, .1, reverse=False, export=export)
    # # collection2, _, paths = calculate_collectionx(voxel_grid, 2, .25, reverse=True, export=export)

    # # # Use swap axes for quick hack since I'm in a rush :(
    # # voxel_grid = np.swapaxes(voxel_grid, 0, 2)
    # # flow_grid3, paths = calculate_flow(voxel_grid, n_iters=3, reverse=False, export=False)
    # # flow_grid4, paths = calculate_flow(voxel_grid, n_iters=3, reverse=True, export=False)
    # # flow_grid3 = np.swapaxes(flow_grid3, 0, 2)
    # # flow_grid4 = np.swapaxes(flow_grid4, 0, 2)
    # # flow_grid = np.asarray(flow_grid1) + flow_grid2# + flow_grid3 + flow_grid4
    # # collection = np.asarray(collection1) + collection2

    # calculate_collectionx(coral, polyp_voxel, voxel_grid, radius=3)

    # calculate_collectionx_from_flow(coral.polyp_collection, polyp_voxel, collection1, 2)
    # # np.clip(coral.polyp_collection, 0, 1, out=coral.polyp_collection)
    # coral.polyp_collection *= 30


    # diffuse(collection, 3)

    # for i in range(coral.n_polyps):
    #     vox = polyp_voxel[i]
    #     coral.polyp_collection[i] = collection[ vox[0], vox[1], vox[2] ] /  2

    # print('here', coral.polyp_collection[:coral.n_polyps].max(), coral.polyp_collection[:coral.n_polyps].mean())

    # if export:
    #     # voxel_grid = np.swapaxes(voxel_grid, 0, 2)
    #     return np.array(voxel_grid), np.array(collection), np.array(min_v), paths
    # else:
    #     return None
