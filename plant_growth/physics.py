from meshpy.triangle import MeshInfo, build, refine
import numpy as np
from math import sqrt, isnan
from plant_growth.spring_system import spring_simulation
from plant_growth.constants import MAX_EDGE_LENGTH
from plant_growth.mesh import Mesh

def compute_deformation2(plant, gravity=-.1, iters=50):
    iters = 10
    delta = 1/50.
    gravity = -2.0
    damping = .05

    mesh = create_mesh(plant)
    plant.mesh = mesh

    points = np.asarray(mesh.points)
    edges = np.asarray(mesh.faces)

    fixed = np.array([p[1] < 10 for p in mesh.points], dtype='i')
    spring_simulation(points, edges, fixed, iters, delta, gravity, damping)

    for i, p in enumerate(mesh.points):
        if i < plant.n_cells:
            cid = plant.cell_order[i]
            plant.cell_next_x[cid] = p[0]
            plant.cell_next_y[cid] = p[1]
        mesh.points[i, 0] = p[0]
        mesh.points[i, 1] = p[1]

def compute_deformation(plant, gravity=-.1, iters=50):
    iters = 10
    delta = 1/50.
    gravity = -2.0
    damping = .05

    # update_mesh(plant)
    mesh = plant.mesh

    points = np.array([ [v.x, v.y] for v in mesh.verts ])
    edges = np.array([[mesh.verts.index(v) for v in edge.verts()] for edge in mesh.edges], dtype='int64')
    fixed = np.array([p[1] < 10 for p in points], dtype='i')

    spring_simulation(points, edges, fixed, iters, delta, gravity, damping)

    for i, p in enumerate(mesh.verts):
        if i < plant.n_cells:
            cid = plant.cell_order[i]
            plant.cell_next_x[cid] = p.x
            plant.cell_next_y[cid] = p.y
