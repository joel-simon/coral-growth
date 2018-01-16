# cython: boundscheck=True
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True
import math
from libc.math cimport round
import numpy as np
cimport numpy as np

cdef int[:,:,:] calc_can_flow(int[:,:,:] obstacles) except *:
    cdef int x, y, z
    cdef list opens
    cdef int nx = obstacles.shape[0]
    cdef int ny = obstacles.shape[1]
    cdef int nz = obstacles.shape[2]
    cdef int[:,:,:] can_flow = np.zeros_like(obstacles)
    can_flow[nx-1,:,:] = 1

    cdef int[:,:] seen = np.zeros((ny, nz), dtype='i')

    for x in range(nx-2, -1, -1):
        for y in range(ny):
            for z in range(nz):
                can_flow[x, y, z] = can_flow[x+1, y, z] and not obstacles[x, y, z]

        # FLOOD FILL
        seen[:,:] = 0
        opens = []

        for y in range(ny):
            for z in range(nz):
                if can_flow[x, y, z]:
                    opens.append((y, z))

        while opens:
            y, z = opens.pop()
            if z > 0 and not seen[y, z-1] and not obstacles[x, y, z-1]:
                can_flow[x, y, z-1] = 1
                opens.append((y, z-1))
                seen[y, z-1] = 1
            if z < nz -1 and not seen[y, z+1] and not obstacles[x, y, z+1]:
                can_flow[x, y, z+1] = 1
                opens.append((y, z+1))
                seen[y, z+1] = 1
            if y > 0 and not seen[y-1, z] and not obstacles[x, y-1, z]:
                can_flow[x, y-1, z] = 1
                opens.append((y-1, z))
                seen[y-1, z] = 1
            if y < ny -1 and not seen[y+1, z] and not obstacles[x, y+1, z]:
                can_flow[x, y+1, z] = 1
                opens.append((y+1, z))
                seen[y+1, z] = 1

    return can_flow

cdef void flow_particle(int x, int y, int z, double v, double[:,:,:] grid,\
                        int[:,:,:] can_flow, int dy, int dz) except *:
    cdef int y2 = y
    cdef int z2 = z
    cdef int ny = can_flow.shape[1]
    cdef int nz = can_flow.shape[2]

    while not can_flow[x+1, y2, z2]:
        if y2+dy < 0 or z2+dz < 0 or y2+dy > ny-1 or z2+dz > nz-1:
            return
        elif can_flow[x, y2+dy, z2+dz]:
            y2 += dy
            z2 += dz
        else:
            return

    if y == y2 and z == z2:
        return

    v /= (abs(y2 - y) + abs(z2 - z))**2

    while y != y2 or z != z2:
        y += dy
        z += dz
        grid[x, y, z] += v

cpdef double[:,:,:] calculate_flow(int[:,:,:] obstacles) except *:
    cdef int x, y, z
    cdef int nx = obstacles.shape[0]
    cdef int ny = obstacles.shape[1]
    cdef int nz = obstacles.shape[2]
    cdef double v, f, y_down, y_up, z_down, z_up
    cdef double[:, :] xm1 = np.zeros((ny, nz))
    cdef double[:,:,:] flow = np.zeros_like(obstacles, dtype='float64')

    cdef int[:,:,:] can_flow = calc_can_flow(obstacles)

    flow[0,:,:] = 1

    for x in range(1, nx):

        xm1[:, :] = flow[x-1, :, :]

        for y in range(ny):
            for z in range(nz):

                if not can_flow[x, y, z] and flow[x-1, y, z]:

                    v = xm1[y, z]*.25

                    if y > 0:
                        flow_particle(x-1, y, z, v, flow, can_flow, -1, 0)
                    if y < ny - 1:
                        flow_particle(x-1, y, z, v, flow, can_flow, 1, 0)
                    if z > 0:
                        flow_particle(x-1, y, z, v, flow, can_flow, 0, -1)
                    if z < nz - 1:
                        flow_particle(x-1, y, z, v, flow, can_flow, 0, 1)

        for y in range(ny):
            for z in range(nz):
                if can_flow[x, y, z]:
                    f = flow[x-1, y, z]
                    y_down = flow[x-1, y-1, z] if y > 0 and not obstacles[x,y-1,z] else f
                    y_up = flow[x-1, y+1, z] if y < ny-1 and not obstacles[x,y+1,z] else f
                    z_down = flow[x-1, y, z-1] if z > 0 and not obstacles[x, y, z-1] else f
                    z_up = flow[x-1, y, z+1] if z < nz-1 and not obstacles[x, y, z+1] else f

                    flow[x, y, z] = .5*f + .125*(y_up + y_down + z_up + z_down)

    return flow

cpdef calculate_collection(coral, int radius=2):
    cdef int i, x, y, z, n, nx, ny, nz, x2, y2, z2
    cdef double total, seen
    cdef double voxel_length = coral.voxel_length
    cdef double [:] polyp_collection = coral.polyp_collection
    cdef double[:,:] polyp_pos = coral.polyp_pos
    cdef double[:,:,:] flow_grid
    cdef int[:,:] voxel_p = np.zeros((coral.n_polyps, 3), dtype='i')
    cdef int[:, :, :] voxel_grid
    n = coral.n_polyps

    for i in range(n):
        voxel_p[i, 0] = <int>(round(polyp_pos[i,0] / voxel_length))
        voxel_p[i, 1] = <int>(round(polyp_pos[i,1] / voxel_length))
        voxel_p[i, 2] = <int>(round(polyp_pos[i,2] / voxel_length))

    cdef int[:] min_v = np.min(voxel_p, axis=0)
    cdef int[:] max_v = np.max(voxel_p, axis=0)

    nx = max_v[0] - min_v[0] + 3
    ny = max_v[1] - min_v[1] + 2
    nz = max_v[2] - min_v[2] + 3

    voxel_grid = np.zeros((nx, ny, nz), dtype='i')

    for i in range(n):
        x = voxel_p[i, 0] - min_v[0] + 1
        y = voxel_p[i, 1] - min_v[1]
        z = voxel_p[i, 2] - min_v[2] + 1
        voxel_grid[x, y, z] = 1

    # Main calculation
    flow_grid = calculate_flow(voxel_grid)

    # Use flow values to calculate collection values.
    total = float((2*radius+1)**3)

    for i in range(n):
        x = voxel_p[i, 0] - min_v[0] + 1
        y = voxel_p[i, 1] - min_v[1]
        z = voxel_p[i, 2] - min_v[2] + 1

        seen = 0
        for x2 in range(x-radius, x+radius+1):
            for y2 in range(y-radius, y+radius+1):
                for z2 in range(z-radius, z+radius+1):
                    if x2 > 0 and y2 > 0 and z2 > 0 and x2 < nx-1 and y2 < ny-1 and z2 < nz-1:
                        seen += flow_grid[x2, y2, z2]

        polyp_collection[i] = seen / total

    return np.asarray(flow_grid), np.asarray(min_v)-1
