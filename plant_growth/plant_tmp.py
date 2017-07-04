import copy
from meshpy.triangle import MeshInfo, build, refine
import numpy as np
from math import sqrt, isnan
from plant_growth.spring_system import spring_simulation
from plant_growth.constants import MAX_EDGE_LENGTH
from plant_growth.mesh import Mesh
from plant_growth.exceptions import MaxCellsException

def create_tri_mesh(plant):
    """ Use triangle library via meshpy library to triangulate intitial mesh.
        This allows us to use concave starting polygons.
    """
    growth_polygon = []

    for i in range(plant.n_cells):
        cid = plant.cell_order[i]
        growth_polygon.append((plant.cell_x[cid], plant.cell_y[cid]))

    mesh_info = MeshInfo()
    mesh_info.set_points(growth_polygon)
    end = len(growth_polygon)-1
    facets = [(i, i+1) for i in range(0, end)] + [(end, 0)]
    mesh_info.set_facets(facets)

    return build(mesh_info, generate_faces=True)

def create_mesh(plant):
    triangle_mesh = create_tri_mesh(plant)
    raw_verts = triangle_mesh.points
    raw_polygons = triangle_mesh.elements

    mesh = Mesh(raw_verts, raw_polygons)

    mesh.cid_to_vert = dict()

    """ Link verts to cids. """
    for i, vert in enumerate(mesh.get_verts()):
        if i < plant.n_cells:
            vert.cid = plant.cell_order[i]
            mesh.cid_to_vert[vert.cid] = vert

    return mesh

# def update_mesh(plant):
#     """ TO BECOME plant.update_mesh
#     """
#     """ return list of inserted veretx cids.
#     """
#     mesh = plant.mesh
#     to_split = []
#     inserted = []

#     for i in range(plant.n_cells):
#         cid = plant.cell_order[i]
#         vert = mesh.cid_to_vert[cid]
#         vert.x = plant.cell_x[cid]
#         vert.y = plant.cell_y[cid]

#     # verts = mesh.adapt(MAX_EDGE_LENGTH)

#     for edge in mesh.get_edges():
#         l = MAX_EDGE_LENGTH #+ MAX_EDGE_LENGTH *.5 * (not edge.is_boundary())
#         if mesh.edge_length(edge) > l:
#             to_split.append(edge)

#     for edge in to_split:
#         v1, v2 = mesh.edge_verts(edge)
#         vert = mesh.edge_split(edge)

#         if mesh.is_boundary_edge(edge):
#             cid1 = v1.cid
#             cid2 = v2.cid

#             if plant.cell_next[cid2] == cid1:
#                 cid1, cid2 = cid2, cid1

#             x = vert.x
#             y = vert.y

#             try:
#                 inserted.append(plant.create_cell(x, y, insert_before=cid2))
#                 vert.cid = inserted[-1]
#                 mesh.cid_to_vert[vert.cid] = vert
#             except MaxCellsException:
#                 break

#     mesh.smooth()

#     return inserted
