# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True
from libc.math cimport sqrt
import numpy as np
cimport numpy as np

ctypedef unsigned char uint8

cdef int[:,:] neighbors = np.array([[-1, 0, 0], [1, 0, 0], [0, 1, 0],
                                    [0, -1, 0], [0, 0, -1], [0, 0, 1]], dtype='int32')

cpdef uint8[:,:,:] flood_fill(uint8[:,:,:] grid) except *:
    cdef int x, y, z, x2, y2, z2, i
    cdef int nx = grid.shape[0]
    cdef int ny = grid.shape[1]
    cdef int nz = grid.shape[2]
    cdef uint8[:,:,:] seen = np.zeros_like(grid)
    cdef uint8[:,:,:] result = np.zeros_like(grid)
    cdef list current = [(0, 0, 0)]

    while current:
        x, y, z = current.pop()
        seen[x, y, z] = 1

        if not grid[x, y, z]:
            result[x, y, z] = 1

            for i in range(neighbors.shape[0]):
                x2 = x + neighbors[i, 0]
                y2 = y + neighbors[i, 1]
                z2 = z + neighbors[i, 2]

                if x2<0 or y2<0 or z2<0 or x2>nx-1 or y2>ny-1 or z2>nz-1:
                    continue

                if seen[x2, y2, z2]:
                    continue

                current.append((x2, y2, z2))
    return result

cpdef void calculate_collection(double[:] collection, int[:,:] voxels,\
                                uint8[:,:,:] voxel_grid, int radius = 3) except *:
    cdef int i, x, y, z, dx, dy, dz, x2, y2, z2, d
    cdef float v
    cdef float total = float((2*radius+1)**3)
    cdef int nx = voxel_grid.shape[0]
    cdef int ny = voxel_grid.shape[1]
    cdef int nz = voxel_grid.shape[2]
    cdef uint8[:,:,:] outside = flood_fill(voxel_grid)
    cdef float[:,:,:] counts = np.zeros_like(voxel_grid, dtype='float32')

    ### Create a 3D kernel
    cdef int w = (2*radius)+1
    cdef float[:,:,:] kernel = np.zeros((w, w, w), dtype='float32')
    cdef int r2 = radius * radius

    for x in range(w):
        for y in range(w):
            for z in range(w):
                dx = abs(x - (radius))
                dy = abs(y - (radius))
                dz = abs(z - (radius))
                d = dx*dx + dy*dy + dz*dz
                if d <= radius*radius:
                    # kernel[x, y, z] = 1.0
                    kernel[x, y, z] = 1.0 / (1 + d / radius)

    for i in range(voxels.shape[0]):
        x = voxels[i, 0]
        y = voxels[i, 1]
        z = voxels[i, 2]

        for dx in range(w):
            for dy in range(w):
                for dz in range(w):
                    x2 = x + dx - radius + 1
                    y2 = y + dy - radius + 1
                    z2 = z + dz - radius + 1
                    if x2>0 and y2>0 and z2>0 and x2<nx-1 and y2<ny-1 and z2<nz-1:
                        counts[ x2, y2, z2 ] += kernel[ dx, dy, dz ]

    for i in range(voxels.shape[0]):
        x = voxels[i, 0]
        y = voxels[i, 1]
        z = voxels[i, 2]
        v = 0
        for dx in range(w):
            for dy in range(w):
                for dz in range(w):
                    x2 = x + dx - radius + 1
                    y2 = y + dy - radius + 1
                    z2 = z + dz - radius + 1
                    if x2>0 and y2>0 and z2>0 and x2<nx-1 and y2<ny-1 and z2<nz-1:
                        v += kernel[ dx, dy, dz ] * outside[ x2, y2, z2 ] / (1 + counts[ x2, y2, z2])

        collection[i] = v / total

