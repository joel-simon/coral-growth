from meshpy.triangle import MeshInfo, build, refine
import numpy as np
from math import sqrt, isnan
from plant_growth.spring_system import spring_simulation

def create_mesh(plant):
    growth_polygon = []

    for i in range(plant.n_cells):
        cid = plant.cell_order[i]
        growth_polygon.append((plant.cell_next_x[cid], plant.cell_next_y[cid]))

    mesh_info = MeshInfo()
    mesh_info.set_points(growth_polygon)
    end = len(growth_polygon)-1
    facets = [(i, i+1) for i in range(0, end)] + [(end, 0)]
    mesh_info.set_facets(facets)

    mesh = build(mesh_info, generate_faces=True)

    # edges = np.asarray(mesh.faces)
    # points = np.asarray(mesh.points)
    return mesh

def compute_deformation(plant, gravity=-.1, iters=50):
    iters = 10
    delta = 1/50.
    gravity = -2.0
    damping = .05

    mesh = create_mesh(plant)
    plant.mesh = mesh

    points = np.asarray(mesh.points)
    edges = np.asarray(mesh.faces)
    # print(points.shape, edges.shape)

    fixed = np.array([p[1] < 10 for p in mesh.points], dtype='i')
    spring_simulation(points, edges, fixed, iters, delta, gravity, damping)

    # simulate(iters, points, fixed, edges, gravity)
    for i, p in enumerate(mesh.points):
        if i < plant.n_cells:
            cid = plant.cell_order[i]
            plant.cell_next_x[cid] = p[0]
            plant.cell_next_y[cid] = p[1]
        mesh.points[i, 0] = p[0]
        mesh.points[i, 1] = p[1]


    # for i, p in enumerate(points):
    #     cid = plant.cell_order[i]
    #     if i < plant.n_cells:
    #         cid = plant.cell_order[i]
    #         plant.cell_next_x[cid] = body.position.x
    #         plant.cell_next_y[cid] = body.position.y
