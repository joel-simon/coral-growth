# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True
import math
from libc.math cimport round, floor
import numpy as np
cimport numpy as np

from minheap import MinHeap
from coral_growth.growth_form cimport GrowthForm

cdef int[:,:] neighbors = np.array([[-1, 0, 0], [1, 0, 0], [0, 1, 0],
                                    [0, -1, 0], [0, 0, -1], [0, 0, 1]], dtype='int32')


cdef void add_to_path(int[:,:,:] grid, float[:,:,:] flow, float[:,:,:] collection,
                      float collection_rate, float value, int[:,:,:,:] came_from,
                      int[:] start, int[:] goal) except *:
    """ The result of dijkstra is a
    """
    cdef int nx = grid.shape[0]
    cdef int ny = grid.shape[1]
    cdef int nz = grid.shape[2]
    cdef int x = goal[0]
    cdef int y = goal[1]
    cdef int z = goal[2]
    cdef int x2, y2, z2
    cdef double resources = 1.0

    while x != start[0] and y != start[1] and z != start[2]:
        flow[x, y, z] += value

        if x > 0 and grid[x-1, y, z] and resources > collection_rate:
            collection[x-1, y, z] += collection_rate
            resources -= collection_rate
        if x < nx -1 and grid[x+1, y, z] and resources > collection_rate:
            collection[x+1, y, z] += collection_rate
            resources -= collection_rate
        if y > 0 and grid[x, y-1, z] and resources > collection_rate:
            collection[x, y-1, z] += collection_rate
            resources -= collection_rate
        if y < ny-1 and grid[x, y+1, z] and resources > collection_rate:
            collection[x, y+1, z] += collection_rate
            resources -= collection_rate
        if z > 0 and grid[x, y, z-1] and resources > collection_rate:
            collection[x, y, z-1] += collection_rate
            resources -= collection_rate
        if z < nz-1 and grid[x, y, z+1] and resources > collection_rate:
            collection[x, y, z+1] += collection_rate
            resources -= collection_rate

        x2 = came_from[x, y, z, 0]
        y2 = came_from[x, y, z, 1]
        z2 = came_from[x, y, z, 2]
        x, y, z = x2, y2, z2

cdef list reconstruct_path(int[:,:,:,:] came_from, int[:] start, int[:] goal):
    cdef int x = goal[0]
    cdef int y = goal[1]
    cdef int z = goal[2]
    cdef int x2, y2, z2
    cdef list path = []
    while x != start[0] and y != start[1] and z != start[2]:
        path.append((x, y, z))
        x2 = came_from[x, y, z, 0]
        y2 = came_from[x, y, z, 1]
        z2 = came_from[x, y, z, 2]
        x, y, z = x2, y2, z2
    path.reverse()
    return path

cpdef tuple dijkstra_search(int[:,:,:] grid, float[:,:,:] cost_grid, int startx):
    cdef int pid
    cdef float new_cost
    cdef int x, y, z, x2, y2, z2
    cdef int nx = grid.shape[0]
    cdef int ny = grid.shape[1]
    cdef int nz = grid.shape[2]
    cdef int nynz = ny*nz

    frontier = MinHeap()
    cdef int[:,:,:,:] came_from = np.zeros((nx, ny, nz, 3), dtype='int32')
    cdef float[:,:,:] cost_so_far = np.zeros_like(grid, dtype='float32')

    for y in range(ny):
        for z in range(nz):
            pid = startx*nynz + y*nz + z
            frontier.push({"id": pid, "price": 0})
            came_from[startx, y, z, 0] = -1
            came_from[startx, y, z, 1] = -1
            came_from[startx, y, z, 2] = -1
            cost_so_far[startx, y, z] = 1.0

    while True:
        try:
            pid = frontier.pop()['id']
            x = pid // (nynz)
            y = (pid-x*(nynz)) // nz
            z = pid % nz

        except IndexError:
            break

        for i in range(6):
            x2 = x + neighbors[i, 0]
            y2 = y + neighbors[i, 1]
            z2 = z + neighbors[i, 2]

            if x2<0 or y2<0 or z2<0 or x2>nx-1 or y2>ny-1 or z2>nz-1:
                continue

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

cpdef tuple create_voxel_grid(GrowthForm coral):
    cdef int i, vx, vy, vz
    cpdef double[:] p

    # Cast coral objects for fast access.
    cdef double voxel_length = coral.voxel_length
    cdef double[:,:] node_pos = coral.node_pos

    # Map each node to its voxel positions. This contains negatives at first.
    cdef int [:,:] node_voxel = np.zeros((coral.n_nodes, 3), dtype='int32')
    for i in range(coral.n_nodes):
        node_voxel[i, 0] = <int>(floor(node_pos[i, 0] / voxel_length))
        node_voxel[i, 1] = <int>(floor(node_pos[i, 1] / voxel_length))
        node_voxel[i, 2] = <int>(floor(node_pos[i, 2] / voxel_length))

    # Calculate the size of the grid.
    cdef int[:] min_v = np.min(node_voxel, axis=0)
    cdef int[:] max_v = np.max(node_voxel, axis=0)

    padding = np.array([8, 4, 8], dtype='int32')
    cdef int[:] offset = padding - 4
    cdef int[:,:,:] voxel_grid = np.zeros(padding + max_v - min_v + [2, 1, 2], dtype='int32')

    for i in range(node_voxel.shape[0]):
        node_voxel[i, 0] += offset[0] - min_v[0]
        node_voxel[i, 1] += offset[1] - min_v[1]
        node_voxel[i, 2] += offset[2] - min_v[2]

    for i in range(coral.n_nodes):
        voxel_grid[node_voxel[i,0], node_voxel[i,1], node_voxel[i,2]] = 1

    for face in coral.mesh.faces:
        p = face.midpoint()
        vx = <int>(floor(p[0] / voxel_length)) - min_v[0] + offset[0]
        vy = <int>(floor(p[1] / voxel_length)) - min_v[1] + offset[1]
        vz = <int>(floor(p[2] / voxel_length)) - min_v[2] + offset[2]
        voxel_grid[vx, vy, vz] = 1

    return node_voxel, voxel_grid, (np.array(min_v) - offset)

cpdef void diffuse(float[:,:,:] collection, int steps=1):
    cdef int i, x, y, z
    cdef float[:,:,:] temp = np.zeros_like(collection)
    for i in range(steps):
        for x in range(1, collection.shape[0]-1):
            for y in range(1, collection.shape[1]-1):
                for z in range(1, collection.shape[2]-1):
                    temp[x, y, z] = .5*collection[x, y, z] + \
                                    .0833*(collection[x-1, y, z] +\
                                          collection[x+1, y, z] +\
                                          collection[x, y-1, z] +\
                                          collection[x, y+1, z] +\
                                          collection[x, y, z-1] +\
                                          collection[x, y, z+1])
        collection, temp = temp, collection
    # return collection

cpdef tuple calculate_collectionx(int[:,:,:] grid, int n_iters, float collection_rate, bint reverse=False, bint export=False):
    cdef int i, x, y, z
    cdef int nx = grid.shape[0]
    cdef int ny = grid.shape[1]
    cdef int nz = grid.shape[2]
    cdef float[:,:,:] travel_sum = np.zeros_like(grid, dtype='float32')
    cdef float[:,:,:] collection = np.zeros_like(grid, dtype='float32')
    cdef float[:,:,:] cost = np.zeros_like(grid, dtype='float32')
    cdef list paths = None
    cdef int[:] path_start = np.array([-1, -1, -1], dtype='i')
    cdef int[:] path_end = np.zeros(3, dtype='i')
    cdef int[:,:,:,:] came_from
    cdef float[:,:,:] cost_so_far

    cdef int startx = (nx-1 if reverse else 0)

    for i in range(n_iters):
        # Create new grid travel costs by past travel rates.
        for x in range(nx):
            for y in range(ny):
                for z in range(nz):
                    cost[x, y, z] = 1 + (travel_sum[x, y, z] / (i+1))

        came_from, cost_so_far = dijkstra_search(grid, cost, startx)

        # Go along the paths and calculate flow and resources
        for y in range(ny):
            for z in range(nz):
                path_end[0] = 0 if reverse else nx-1
                path_end[1] = y
                path_end[2] = z
                add_to_path(grid, travel_sum, collection, collection_rate, .5, \
                            came_from, path_start, path_end)

    travel_avg = np.array(travel_sum) / (i+1)

    if export:
        paths = []
        for y in range(ny):
            for z in range(nz):
                path_end[0] = 0 if reverse else nx-1
                path_end[1] = y
                path_end[2] = z
                paths.append(reconstruct_path(came_from, path_start, path_end))
        return collection, travel_avg, paths
    else:
        return collection, travel_avg, None

cpdef void calculate_collectionx_from_flow(double[:] collection, int[:,:] voxels,\
                                          float[:,:,:] flow_grid, int radius=1) except *:
    cdef int i, x, y, z, dx, dy, dz
    cdef float seen
    cdef float total = float((2*radius+1)**3)
    cdef int nx = flow_grid.shape[0]
    cdef int ny = flow_grid.shape[1]
    cdef int nz = flow_grid.shape[2]

    cdef unsigned int[:,:,:] counts = np.zeros_like(flow_grid, dtype='uint32')
    for i in range(voxels.shape[0]):
        x = voxels[i, 0]
        y = voxels[i, 1]
        z = voxels[i, 2]
        for dx in range(x-radius, x+radius+1):
            for dy in range(y-radius, y+radius+1):
                for dz in range(z-radius, z+radius+1):
                    if dx>0 and dy>0 and dz>0 and dx<nx-1 and dy<ny-1 and dz<nz-1:
                        counts[dx, dy, dz] += 1

    for i in range(voxels.shape[0]):
        x = voxels[i, 0]
        y = voxels[i, 1]
        z = voxels[i, 2]
        seen = 0
        for dx in range(x-radius, x+radius+1):
            for dy in range(y-radius, y+radius+1):
                for dz in range(z-radius, z+radius+1):
                    if dx>0 and dy>0 and dz>0 and dx<nx-1 and dy<ny-1 and dz<nz-1:
                        seen += flow_grid[dx, dy, dz] / counts[dx, dy, dz]

        collection[i] = seen / total

