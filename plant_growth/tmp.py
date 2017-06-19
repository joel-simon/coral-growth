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

    """ Link verts to cids. """
    for i, vert in enumerate(mesh.verts):
        if i < plant.n_cells:
            vert.cid = plant.cell_order[i]
            mesh.cid_to_vert[vert.cid] = vert
            # print(vert, vert.cid)
        else:
            vert.cid = None

    for edge in mesh.edges:
        if edge.is_boundary():
            v1, v2 = edge.verts()
            cid1 = v1.cid
            cid2 = v2.cid
            assert cid1 is not None, v1
            assert cid2 is not None, v2

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


    for edge in mesh.edges:
        l = MAX_EDGE_LENGTH + MAX_EDGE_LENGTH *.5 * (not edge.is_boundary())
        if edge.length() > l:
            edge.length()
            to_split.append(edge)


    for edge in to_split:
        v1, v2 = edge.verts()
        vert = mesh.edge_split(edge)

        if edge.is_boundary():
            cid1 = v1.cid
            cid2 = v2.cid

            if plant.cell_next[cid2] == cid1:
                cid1, cid2 = cid2, cid1

            x = vert.x#(plant.cell_x[cid1] + plant.cell_x[cid2]) / 2.0
            y = vert.y#(plant.cell_y[cid1] + plant.cell_y[cid2]) / 2.0

            inserted.append(plant.create_cell(x, y, insert_before=cid2))
            vert.cid = inserted[-1]
            mesh.cid_to_vert[vert.cid] = vert

    for edge in copy.copy(mesh.edges):
        mesh.flip_if_better(edge)

    for v in mesh.verts:
        if v.cid == None:
            v.x0 = 0
            v.y0 = 0
            n = 0
            neighbors = list(mesh.neighbors(v))
            for nv in neighbors:
                v.x0 += nv.x
                v.y0 += nv.y
                n += 1
            v.y0 /= n
            v.x0 /= n

    for v in mesh.verts:
        if v.cid == None:
            v.x = v.x0
            v.y = v.y0

    #     v1, v2 = edge.verts()
    # #     # if (v1.id in new_verts) ^ (v2.id in new_verts):
    # #         # mesh.edge_flip(edge)

    #     if not edge.is_boundary():

    # print()
    return inserted
