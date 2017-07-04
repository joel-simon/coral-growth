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
    data = mesh.py_data()
    edges = data['edges']
    verts = data['vertices']

    for edge in edges:
        v1 = tuple(verts[edge[0]] + [off_x, off_y])
        v2 = tuple(verts[edge[1]] + [off_x, off_y])
        view.draw_line(v1, v2, (0,0,0), 1)

    for vert in verts:
        view.draw_circle((vert[0]+off_x, vert[1]+off_y), 2, (255, 0, 0), 0)

    for i, vert in enumerate(verts):
        view.draw_text((vert[0]+off_x, vert[1]+off_y), str(i), font=16, center=True)

view.start_draw()
draw_mesh(mesh, -125, +125)

mesh.split_edges(0)# Split all
draw_mesh(mesh, 125, +125)

mesh.smooth()
draw_mesh(mesh, -125, -125)

view.end_draw()
view.hold()


