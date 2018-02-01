# # cython: boundscheck=True
# # cython: wraparound=False
# # cython: initializedcheck=False
# # cython: nonecheck=False
# # cython: cdivision=True
# import math
# from libc.math cimport round
# import numpy as np
# cimport numpy as np

# cdef int[:,:,:] calc_can_flow(int[:,:,:] obstacles) except *:
#     cdef int x, y, z
#     cdef list opens
#     cdef int nx = obstacles.shape[0]
#     cdef int ny = obstacles.shape[1]
#     cdef int nz = obstacles.shape[2]
#     cdef int[:,:,:] can_flow = np.zeros_like(obstacles)
#     can_flow[nx-1,:,:] = 1

#     cdef int[:,:] seen = np.zeros((ny, nz), dtype='i')

#     for x in range(nx-2, -1, -1):
#         for y in range(ny):
#             for z in range(nz):
#                 can_flow[x, y, z] = can_flow[x+1, y, z] and not obstacles[x, y, z]

#         # FLOOD FILL
#         seen[:,:] = 0
#         opens = []

#         for y in range(ny):
#             for z in range(nz):
#                 if can_flow[x, y, z]:
#                     opens.append((y, z))

#         while opens:
#             y, z = opens.pop()
#             if z > 0 and not seen[y, z-1] and not obstacles[x, y, z-1]:
#                 can_flow[x, y, z-1] = 1
#                 opens.append((y, z-1))
#                 seen[y, z-1] = 1
#             if z < nz -1 and not seen[y, z+1] and not obstacles[x, y, z+1]:
#                 can_flow[x, y, z+1] = 1
#                 opens.append((y, z+1))
#                 seen[y, z+1] = 1
#             if y > 0 and not seen[y-1, z] and not obstacles[x, y-1, z]:
#                 can_flow[x, y-1, z] = 1
#                 opens.append((y-1, z))
#                 seen[y-1, z] = 1
#             if y < ny -1 and not seen[y+1, z] and not obstacles[x, y+1, z]:
#                 can_flow[x, y+1, z] = 1
#                 opens.append((y+1, z))
#                 seen[y+1, z] = 1

#     return can_flow

# cdef void flow_particle(int x, int y, int z, float v, float[:,:,:] grid,\
#                         int[:,:,:] can_flow, int dy, int dz) except *:
#     cdef int y2 = y
#     cdef int z2 = z
#     cdef int ny = can_flow.shape[1]
#     cdef int nz = can_flow.shape[2]

#     while not can_flow[x+1, y2, z2]:
#         if y2+dy < 0 or z2+dz < 0 or y2+dy > ny-1 or z2+dz > nz-1:
#             return
#         elif can_flow[x, y2+dy, z2+dz]:
#             y2 += dy
#             z2 += dz
#         else:
#             return

#     if y == y2 and z == z2:
#         return

#     v /= (abs(y2 - y) + abs(z2 - z))**2

#     while y != y2 or z != z2:
#         y += dy
#         z += dz
#         grid[x, y, z] += v

# cpdef tuple calculate_flow(int[:,:,:] obstacles, float capture_percent,
#                            float fluid_diffusion):
#     cdef int x, y, z
#     cdef int nx = obstacles.shape[0]
#     cdef int ny = obstacles.shape[1]
#     cdef int nz = obstacles.shape[2]
#     cdef float v, f, y_down, y_up, z_down, z_up, df
#     cdef float[:, :] xm1 = np.zeros((ny, nz), dtype='float32')
#     cdef float[:,:,:] flow = np.zeros_like(obstacles, dtype='float32')
#     cdef float[:,:,:] collection = np.zeros_like(obstacles, dtype='float32')
#     cdef int[:,:,:] can_flow = calc_can_flow(obstacles)

#     flow[0,:,:] = 1

#     for x in range(1, nx):
#         xm1[:, :] = flow[x-1, :, :]
#         for y in range(ny):
#             for z in range(nz):
#                 # First flow the positions that cannot go directly straight.
#                 if not can_flow[x, y, z] and flow[x-1, y, z]:
#                     # Split evenly in four direction.
#                     v = xm1[y, z]*.25

#                     if y > 0:
#                         flow_particle(x-1, y, z, v, flow, can_flow, -1, 0)
#                     if y < ny - 1:
#                         flow_particle(x-1, y, z, v, flow, can_flow, 1, 0)
#                     if z > 0:
#                         flow_particle(x-1, y, z, v, flow, can_flow, 0, -1)
#                     if z < nz - 1:
#                         flow_particle(x-1, y, z, v, flow, can_flow, 0, 1)

#         # Step all forward and apply diffusion
#         for y in range(ny):
#             for z in range(nz):
#                 if can_flow[x, y, z]:
#                     # Update flow
#                     f = flow[x-1, y, z]
#                     y_down = flow[x-1, y-1, z] if y > 0 and not obstacles[x,y-1,z] else f
#                     y_up = flow[x-1, y+1, z] if y < ny-1 and not obstacles[x,y+1,z] else f
#                     z_down = flow[x-1, y, z-1] if z > 0 and not obstacles[x, y, z-1] else f
#                     z_up = flow[x-1, y, z+1] if z < nz-1 and not obstacles[x, y, z+1] else f

#                     flow[x, y, z] = (1-fluid_diffusion)*f + (fluid_diffusion*.25)*(y_up + y_down + z_up + z_down)

#                     # Polyps slow the flow around them, collecting resources
#                     df = f * capture_percent * .25
#                     if y > 0 and obstacles[x,y-1,z]:
#                         collection[x, y-1, z] += df
#                         flow[x, y, z] -=  df
#                     if y < ny-1 and obstacles[x,y+1,z]:
#                         collection[x, y+1, z] += df
#                         flow[x, y, z] -= df
#                     if z > 0 and obstacles[x, y, z-1]:
#                         collection[x, y, z-1] += df
#                         flow[x, y, z] -= df
#                     if z < nz-1 and obstacles[x, y, z+1]:
#                         collection[x, y, z+1] += df
#                         flow[x, y, z] -= df

#     return flow, collection

# cpdef calculate_collection(coral, int radius=2, float capture_percent=.1,
#                            float fluid_diffusion=.5):
#     cdef int i, x, y, z, n, nx, ny, nz, x2, y2, z2
#     cdef float total, capture
#     cdef float voxel_length = coral.voxel_length
#     cdef double [:] polyp_collection = coral.polyp_collection
#     cdef double[:,:] polyp_pos = coral.polyp_pos
#     cdef float[:,:,:] flow_grid
#     cdef float[:,:,:] capture_grid
#     cdef int[:,:] voxel_p = np.zeros((coral.n_polyps, 3), dtype='i')
#     cdef int[:, :, :] voxel_grid
#     n = coral.n_polyps

#     ############################################################################
#     # Calculate voxel position and grid size for each polyp.
#     for i in range(n):
#         voxel_p[i, 0] = <int>(round(polyp_pos[i,0] / voxel_length))
#         voxel_p[i, 1] = <int>(round(polyp_pos[i,1] / voxel_length))
#         voxel_p[i, 2] = <int>(round(polyp_pos[i,2] / voxel_length))

#     cdef int[:] min_v = np.min(voxel_p, axis=0)
#     cdef int[:] max_v = np.max(voxel_p, axis=0)

#     # Have an offset on either side for fluid to flow around.
#     nx = max_v[0] - min_v[0] + 3
#     ny = max_v[1] - min_v[1] + 2
#     nz = max_v[2] - min_v[2] + 3

#     ############################################################################
#     # Build a voxel grid based off of polyp positions.
#     voxel_grid = np.zeros((nx, ny, nz), dtype='i')
#     voxel_grid_rev = np.zeros((nx, ny, nz), dtype='i')

#     for i in range(n):
#         x = (voxel_p[i, 0] - min_v[0] + 1)
#         y = voxel_p[i, 1] - min_v[1]
#         z = voxel_p[i, 2] - min_v[2] + 1
#         voxel_grid[x, y, z] = 1
#         voxel_grid_rev[nx-x, y, z] = 1

#     ############################################################################

#     # Main calculation
#     # Very Hacky method to flow both directions.
#     flow_grid1, capture_grid1 = calculate_flow(voxel_grid, capture_percent,
#                                              fluid_diffusion)
#     flow_grid2, capture_grid2 = calculate_flow(voxel_grid_rev, capture_percent,
#                                              fluid_diffusion)
#     # flow_grid = (np.asarray(flow_grid1) + np.asarray(flow_grid2)) * .5
#     # capture_grid = (np.asarray(capture_grid1) + np.asarray(capture_grid2)) * .5

#     # Use flow values to calculate collection values. Simple neighbor average.
#     total = float((2*radius+1)**3)

#     for i in range(n):
#         x = voxel_p[i, 0] - min_v[0] + 1
#         y = voxel_p[i, 1] - min_v[1]
#         z = voxel_p[i, 2] - min_v[2] + 1

#         capture = 0
#         for x2 in range(x-radius, x+radius+1):
#             for y2 in range(y-radius, y+radius+1):
#                 for z2 in range(z-radius, z+radius+1):
#                     if x2 > 0 and y2 > 0 and z2 > 0 and x2 < nx-1 and y2 < ny-1 and z2 < nz-1:
#                         capture += capture_grid1[x2, y2, z2]
#                         capture += capture_grid2[nx-x2, y2, z2]

#         polyp_collection[i] = capture / (2*total)

#     return np.asarray(flow_grid1), np.asarray(capture_grid1), np.asarray(min_v)-1
