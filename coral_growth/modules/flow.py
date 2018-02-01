import math
import numpy as np

from minheap import MinHeap

def neighbors(grid, x, y, z):
    result = []
    if x > 0: result.append((x-1, y, z))
    if x < grid.shape[0]-1: result.append((x+1, y, z))
    if y > 0: result.append((x, y-1, z))
    if y < grid.shape[1]-1: result.append((x, y+1, z))
    if z > 0: result.append((x, y, z-1))
    if z < grid.shape[2]-1: result.append((x, y, z+1))
    return result

def reconstruct_path(came_from, start, goal):
    current = goal
    path = []
    while current != start:
        path.append(current)
        current = tuple(came_from[current[0], current[1], current[2]])
    path.reverse()
    return path

def dijkstra_search(grid, cost_grid, startx):
    nx = grid.shape[0]
    ny = grid.shape[1]
    nz = grid.shape[2]
    nynz = ny*nz
    frontier = MinHeap()
    came_from = np.zeros((nx, ny, nz, 3), dtype='int32')
    cost_so_far = np.zeros_like(grid, dtype='float32')

    for y in range(grid.shape[1]):
        for z in range(grid.shape[2]):
            pid = startx*nynz + y*nz + z
            frontier.push({"id": pid, "price": 0})
            came_from[startx, y, z, 0] = -1
            came_from[startx, y, z, 1] = -1
            came_from[startx, y, z, 2] = -1
            cost_so_far[startx, y, z] = 1.0

    while True:
        try:
            item = frontier.pop()
            x = item['id'] // (nynz)
            y = (item['id']-x*(nynz)) // nz
            z = item['id'] % nz

        except IndexError:
            break

        for x2, y2, z2 in neighbors(grid, x, y, z):
            if grid[x2, y2, z2] == 1:
                continue
            new_cost = cost_so_far[x, y, z] + cost_grid[x2, y2, z2]
            if cost_so_far[x2, y2, z2] == 0 or new_cost < cost_so_far[x2, y2, z2]:
                cost_so_far[x2, y2, z2] = new_cost
                frontier.push({"id":(x2*nynz)+(y2*nz)+z2, "price": new_cost})
                came_from[x2, y2, z2, 0] = x
                came_from[x2, y2, z2, 1] = y
                came_from[x2, y2, z2, 2] = z

    return came_from, cost_so_far

def calculate_flow(grid, n_iters):
    nx = grid.shape[0]
    ny = grid.shape[1]
    nz = grid.shape[2]

    cost_grid = np.ones_like(grid, dtype='f')
    travel_sum = np.zeros_like(grid, dtype='f')

    for i in range(n_iters):
        travel_avg = travel_sum/(i+1)
        came_from, cost_so_far = dijkstra_search(grid, cost_grid+travel_avg, startx=0)

        paths = []
        for y in range(ny):
            for z in range(nz):
                path = reconstruct_path(came_from, (-1, -1, -1), (nx-1, y, z))
                paths.append(path)

                for pi, (x, y, z) in enumerate(path):
                    travel_sum[x, y, z] += .5 / (i+1)

    travel_avg = travel_sum / (i+1)
    return travel_avg, came_from, paths

def update_voxels(coral):
    polyp_voxel = np.zeros((coral.n_polyps, 3), dtype='i')

    for i in range(coral.n_polyps):
        p = coral.polyp_pos[i]
        polyp_voxel[i, 0] = int(round(p[0] / coral.voxel_length))
        polyp_voxel[i, 1] = int(round(p[1] / coral.voxel_length))
        polyp_voxel[i, 2] = int(round(p[2] / coral.voxel_length))

    min_v = polyp_voxel.min(axis=0)
    max_v = polyp_voxel.max(axis=0)

    padding = np.array([4, 2, 4])
    offset = padding - 2

    voxel_grid = np.zeros(max_v - min_v + padding + [2, 1, 2])

    polyp_voxel -= min_v
    polyp_voxel += offset

    for i in range(coral.n_polyps):
        vox = polyp_voxel[i]
        voxel_grid[ vox[0], vox[1], vox[2] ] = 1

    for face in coral.mesh.faces:
        p = face.midpoint()
        vx = int(round(p[0] / coral.voxel_length)) - min_v[0] + offset[0]
        vy = int(round(p[1] / coral.voxel_length)) - min_v[1] + offset[1]
        vz = int(round(p[2] / coral.voxel_length)) - min_v[2] + offset[2]
        voxel_grid[vx, vy, vz] = 1

    return polyp_voxel, voxel_grid, (min_v - offset)

def calculate_collection(coral):
    polyp_voxel, voxel_grid, min_v = update_voxels(coral)

    nx = voxel_grid.shape[0]
    ny = voxel_grid.shape[1]
    nz = voxel_grid.shape[2]

    flow_grid, came_from, paths = calculate_flow(voxel_grid, n_iters=1)

    radius = 1
    total = float((2*radius+1)**3)

    # coral.polyp_collection[:] = 0
    for i in range(coral.n_polyps):
        x, y, z = polyp_voxel[i]
        # for x2, y2, z2 in neighbors(flow_grid, x, y, z):
        #     coral.polyp_collection[i] += flow_grid[x2, y2, z2]

        seen = 0
        for dx in range(x-radius, x+radius+1):
            for dy in range(y-radius, y+radius+1):
                for dz in range(z-radius, z+radius+1):
                    if dx > 0 and dy > 0 and dz > 0 and dx < nx-1 and dy < ny-1 and dz < nz-1:
                        seen += flow_grid[dx, dy, dz]

        coral.polyp_collection[i] = seen / total

    return voxel_grid, flow_grid, min_v, paths
