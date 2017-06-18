import copy
from meshpy.triangle import MeshInfo, build, refine
import numpy as np
from math import sqrt, isnan
from plant_growth.spring_system import spring_simulation
from plant_growth.constants import MAX_EDGE_LENGTH
from plant_growth.mesh import Mesh

def create_tri_mesh(plant):
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
    # print(raw_polygons)
    mesh = Mesh(raw_verts, raw_polygons)

    mesh.cid_to_vert = dict()
    # link verts to cids.
    for i, vert in enumerate(mesh.verts):
        if i < plant.n_cells:
            vert.cid = plant.cell_order[i]
            mesh.cid_to_vert[vert.cid] = vert
        else:
            vert.cid = None
    # print(len(mesh.verts), plant.n_cells)
    # print([(v.id, v.cid) for v in mesh.verts])
    # print()
    return mesh

def update_mesh(plant):
    """ return CID of inserted cells.
    """
    assert plant.mesh
    mesh = plant.mesh
    to_split = []
    inserted = []

    for i in range(plant.n_cells):
        cid = plant.cell_order[i]
        vert = mesh.cid_to_vert[cid]
        vert.x = plant.cell_x[cid]
        vert.y = plant.cell_y[cid]

    # for edge in mesh.edges:
    #     if not edge.is_boundary():
    #         mesh.flip_if_better(edge)

    for edge in mesh.edges:
        if edge.length() > MAX_EDGE_LENGTH and not edge.is_boundary():
            edge.length()
            to_split.append(edge)

    new_verts = set()

    for edge in to_split:
        vert = mesh.edge_split(edge)
        new_verts.add(vert.id)

        if edge.is_boundary():
            v1, v2 = edge.verts()

            cid1 = v1.cid
            cid2 = v2.cid

            if plant.cell_next[cid2] == cid1:
                cid1, cid2 = cid2, cid1

            x = (plant.cell_x[cid1] + plant.cell_x[cid2]) / 2.0
            y = (plant.cell_y[cid1] + plant.cell_y[cid2]) / 2.0
            inserted.append(plant.create_cell(x, y, before=cid2))
            vert.cid = inserted[-1]
            mesh.cid_to_vert[vert.cid] = vert

    # for edge in copy.copy(mesh.edges):
        # v1, v2 = edge.verts()
        # if (v1.id in new_verts) ^ (v2.id in new_verts):
        # if not edge.is_boundary():
        #     mesh.flip_if_better(edge)
            # mesh.edge_flip(edge)

    # print()
    return inserted
