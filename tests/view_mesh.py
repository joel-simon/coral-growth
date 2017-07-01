import math
import copy
from plant_growth.mesh import Mesh
from meshpy.triangle import MeshInfo, build
from plant_growth.pygameDraw import PygameDraw

n = 12
r = 100
max_l = r
view = PygameDraw(600, 600)
polygon = []

for i in range(n):
    a = (2 * i * math.pi / n) + math.pi / 16
    xx = 300 + math.cos(a) * r
    yy = 300 + math.sin(a) * r
    polygon.append((xx, yy))

mesh_info = MeshInfo()
mesh_info.set_points(polygon)
end = len(polygon)-1
facets = [(i, i+1) for i in range(0, end)] + [(end, 0)]
mesh_info.set_facets(facets)
triangle_mesh = build(mesh_info)

mesh = Mesh(triangle_mesh.points, triangle_mesh.elements)

def draw_mesh(mesh, off_x=0, off_y=0):
    for face in mesh.faces:
        verts = [(v.x+off_x, v.y+off_y) for v in mesh.face_verts(face)]
        view.draw_polygon(verts, (0,0,0), 1)

    for vert in mesh.verts:
        if mesh.is_boundary_vert(vert):
            view.draw_circle((vert.x+off_x, vert.y+off_y), 2, (255, 0, 0), 0)

    for vert in mesh.verts:
        view.draw_text((vert.x+off_x, vert.y+off_y), str(vert.id), font=16, center=True)

view.start_draw()
draw_mesh(mesh, -125, +125)

new_verts = set()


for edge in copy.copy(mesh.edges):
    if not mesh.is_boundary_edge(edge):
        vert = mesh.edge_split(edge)
        new_verts.add(vert.id)

draw_mesh(mesh, 125, +125)
for edge in mesh.edges:
    v1, v2 = mesh.edge_verts(edge)
    if mesh.is_boundary_edge(edge):
        continue
    mesh.flip_if_better(edge)

draw_mesh(mesh, -125, -125)
view.end_draw()

for v in [mesh.verts[12], mesh.verts[23]]:
    try:
        print(v.id, [vn.id for vn in mesh.vert_neighbors(v)])
    except Exception as e:
        raise e


view.hold()
