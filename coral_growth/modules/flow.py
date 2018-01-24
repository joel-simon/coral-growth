import math
import numpy as np
from collections import defaultdict

def calc_can_flow(obstacles):
    nx = obstacles.shape[0]
    ny = obstacles.shape[1]
    nz = obstacles.shape[2]

    can_flow = np.zeros_like(obstacles)
    can_flow[-1] = 1

    for x in range(nx-2, -1, -1):
        can_flow[x] = np.logical_and(can_flow[x+1], np.logical_not(obstacles[x]))

        # FLOOD FILL
        seen = np.zeros((ny, nz))
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

def flow_particle(x, y, z, v, grid, can_flow, dy, dz):
    y2 = y
    z2 = z

    while not can_flow[x+1, y2, z2]:
        if can_flow[x, y2+dy, z2+dz]:
            y2 += dy
            z2 += dz
        else:
            return

    if y == y2 and z == z2:
        return

    while y != y2 or z != z2:
        y += dy
        z += dz

        grid[x, y, z] += v

def calculate_flow(obstacles, capture_percent):

    flow = np.zeros_like(obstacles, dtype='f')
    collection = np.zeros_like(obstacles, dtype='f')
    # particles = np.zeros_like(obstacles, dtype='f')
    can_flow = calc_can_flow(obstacles)

    nx = flow.shape[0]
    ny = flow.shape[1]
    nz = flow.shape[2]

    flow[0] = 1

    for x in range(1, nx):
        xm1 = flow[x-1].copy()

        # First, flow the particles that cannot go straight.
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

        # Move all forward with diffusion.
        for y in range(ny):
            for z in range(nz):
                if can_flow[x, y, z]:
                    f = flow[x-1, y, z]
                    y_down = flow[x-1, y-1, z] if y > 0 and not obstacles[x,y-1,z] else f
                    y_up = flow[x-1, y+1, z] if y < ny-1 and not obstacles[x,y+1,z] else f
                    z_down = flow[x-1, y, z-1] if z > 0 and not obstacles[x, y, z-1] else f
                    z_up = flow[x-1, y, z+1] if z < nz-1 and not obstacles[x, y, z+1] else f
                    flow[x, y, z] = .5*f + .125*(y_up + y_down + z_up + z_down)


                    # Polyps slow the flow around them, collecting resources
                    df = f * capture_percent * .25
                    if y > 0 and obstacles[x,y-1,z]:
                        collection[x, y-1, z] += df
                        flow[x, y, z] -=  df
                    if y < ny-1 and obstacles[x,y+1,z]:
                        collection[x, y+1, z] += df
                        flow[x, y, z] -= df
                    if z > 0 and obstacles[x, y, z-1]:
                        collection[x, y, z-1] += df
                        flow[x, y, z] -= df
                    if z < nz-1 and obstacles[x, y, z+1]:
                        collection[x, y, z+1] += df
                        flow[x, y, z] -= df

    return flow, collection


def calculate_collection(coral, radius=3, capture_percent=.1):
    voxel_p = np.zeros((coral.n_polyps, 3), dtype='i')

    for i in range(coral.n_polyps):
        p = coral.polyp_pos[i]
        voxel_p[i, 0] = int(round(p[0] / coral.voxel_length))
        voxel_p[i, 1] = int(round(p[1] / coral.voxel_length))
        voxel_p[i, 2] = int(round(p[2] / coral.voxel_length))

    min_v = voxel_p.min(axis=0)
    max_v = voxel_p.max(axis=0)

    nx = max_v[0] - min_v[0] + 3
    ny = max_v[1] - min_v[1] + 2
    nz = max_v[2] - min_v[2] + 3

    voxel_grid = np.zeros((nx, ny, nz))

    for i in range(coral.n_polyps):
        vox = voxel_p[i] - min_v
        voxel_grid[vox[0]+1, vox[1], vox[2]+1] = 1

    # Main calculation
    flow_grid, collection_grid = calculate_flow(voxel_grid, capture_percent)

    # Use flow values to calculate collection values.
    total = float((2*radius+1)**3)

    for i in range(coral.n_polyps):
        x, y, z = voxel_p[i] - min_v

        seen = 0
        for dx in range(x-radius, x+radius+1):
            for dy in range(y-radius, y+radius+1):
                for dz in range(z-radius, z+radius+1):
                    if dx > 0 and dy > 0 and dz > 0 and dx < nx-1 and dy < ny-1 and dz < nz-1:
                        seen += flow_grid[dx+1, dy, dz+1]

        coral.polyp_collection[i] = seen / total

    return flow_grid, min_v-1
