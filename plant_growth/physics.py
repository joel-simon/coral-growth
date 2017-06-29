from meshpy.triangle import MeshInfo, build, refine
import numpy as np
from math import sqrt, isnan

from plant_growth.spring_system_mesh import spring_simulation_mesh
from plant_growth.spring_system import spring_simulation

from plant_growth.constants import MAX_EDGE_LENGTH, MAX_DEFORMATION

import time
# from plant_growth.mesh import Mesh

def compute_deformation2(plant, gravity=-.1, iters=250, delta=1.0/50):
    damping = .01

    for vert in plant.mesh.verts:
        vert.prev_x = vert.x
        vert.prev_y = vert.y
        if vert.y <= 10:
            vert.fixed = True
        else:
            vert.fixed = False

    for vert in plant.mesh.verts:
        print('vert', vert.x, vert.y)

    spring_simulation_mesh(plant.mesh, iters=iters, delta=delta, gravity=gravity, damping=damping)

    for vert in plant.mesh.verts:
        print(vert.x, vert.y)

# def grow_break(plant, edge, vert):
#     # given an edge and one of its verts, find the next edge in theat direction
#     result = None
#     max_strain = 0
#     for edge_n in plant.mesh.edge_neighbors(vert):

# def handle_break(plant):
#     tobreak = [e for e in plant.mesh.edges if e.strain == 1]

#     while len(tobreak):
#         edge = tobreak.pop()
#         v1, v2 = edge.verts()
#         while not v1.is_boundary():
#             v1, edge2 = grow_break(edge, v1)

def compute_deformation(plant, gravity=-.1, iters=200, delta=1.0/100, damping = .00):
    t1 = time.time()
    v_to_i = dict()
    mesh = plant.mesh
    n_p = len(mesh.verts)
    n_e = len(mesh.edges)
    points = np.zeros((n_p, 2))
    fixed = np.zeros(n_p, dtype='i')
    edges = np.zeros((n_e, 2), dtype='int64')
    deformation = np.zeros(n_e)

    # Do hacky makeshift mapping from arrays to mesh.
    for cid, vert in plant.mesh.cid_to_vert.items():
        vert.x = plant.cell_next_x[cid]
        vert.y = plant.cell_next_y[cid]

    # Create others array from mesh for spring_simulation.
    for i, vert in enumerate(mesh.verts):
        v_to_i[vert] = i
        points[i, 0] = vert.x
        points[i, 1] = vert.y
        fixed[i] = vert.y < 10

    for j, edge in enumerate(mesh.edges):
        v1, v2 = edge.verts()
        edges[j, 0] = v_to_i[v1]
        edges[j, 1] = v_to_i[v2]

    # Run spring simulation.
    spring_simulation(points, edges, fixed, iters, delta, gravity, damping, deformation)

    # Take deformations and map back to mesh and cell_next arrays
    # for i, p in enumerate(points):
    #     mesh.verts[i].x = p[0]
    #     mesh.verts[i].y = p[1]
    #     if mesh.verts[i].cid:
    #         cid = mesh.verts[i].cid
    #         plant.cell_next_x[cid] = p[0]
    #         plant.cell_next_y[cid] = p[1]

    # deformation = [d*d for d in deformation]

    for j, e in enumerate(edges):
        mesh.edges[j].strain = min(1, deformation[j] / MAX_DEFORMATION)

    for i in range(plant.n_cells):
        cid = plant.cell_order[i]
        vert = plant.mesh.cid_to_vert[cid]
        strain = max(edge.strain for edge in mesh.edge_neighbors(vert))
        plant.cell_strain[cid] = strain

    max_strain = (max(e.strain for e in mesh.edges))
    # print(max_strain)
    return max_strain
