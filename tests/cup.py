import heapq
from math import acos, pi, sqrt
from itertools import count
from cymesh.mesh import Mesh
from cymesh.view import Viewer
import tripy

mesh = Mesh.from_obj('cup2.obj')
# mesh = Mesh.from_obj('../data/triangulated_sphere_3.obj')
mesh.calculateNormals()

class MyHeap(object):
    def __init__(self, initial=None, key=lambda x:x):
        self.key = key
        self._counter = count()
        if initial:
            self._data = [(key(item), next(self._counter), item) for item in initial]
            heapq.heapify(self._data)
        else:
            self._data = []

    def push(self, item):
        heapq.heappush(self._data, (self.key(item), next(self._counter), item))

    def push_all(self, items):
        for item in items:
            self.push(item)

    def pop(self):
        return heapq.heappop(self._data)[2]

    def __nonzero__(self):
        return bool(len(self._data))

    def __len__(self):
        return len(self._data)

# def grow_fontier(nodes, seen):
#     frontier = []
#     for node in nodes:
#         for neighbor in node.neighbors():
#             if neighbor not in seen:
#                 frontier.append(neighbor)
#                 seen.add(neighbor)
#     return frontier

def water_held(mesh):
    mesh.calculateNormals()
    water_line = 0
    seen = set()

    for vert in sorted(mesh.verts, key=lambda vert: vert.p[1]):
        if vert in seen:
            continue
        if any(neighbor.p[1] < vert.p[1] for neighbor in vert.neighbors()):
            continue
        if vert.normal[1] < 0:
            continue
        else:
            derp = set([ vert ])
            heap = MyHeap(key=lambda vert: vert.p[1])
            heap.push(vert)
            water_level = vert.p[1]

            while len(heap):
                vert2 = heap.pop()

                if vert2.p[1] >= water_level:
                    derp.add(vert2)
                    water_level = vert2.p[1]

                    for vert3 in vert2.neighbors():
                        if vert3 not in seen:
                            seen.add(vert3)
                            heap.push(vert3)

            return derp
    return []


def water_held3(mesh):
    mesh.calculateNormals()
    water_line = 0
    seen = set()

    for vert in sorted(mesh.verts, key=lambda vert: vert.p[1]):
        if vert in seen:
            continue
        if any(neighbor.p[1] < vert.p[1] for neighbor in vert.neighbors()):
            continue
        if vert.normal[1] < 0:
            continue
        else:
            derp = set([ vert ])
            heap = MyHeap(key=lambda vert: vert.p[1])
            heap.push(vert)
            water_level = vert.p[1]

            while len(heap):
                vert2 = heap.pop()

                # if vert2.p[1] >= water_level:
                #     derp.add(vert2)
                #     water_level = vert2.p[1]

                for vert3 in vert2.neighbors():
                    if vert3 not in seen and vert3.p[1] > 0:
                        seen.add(vert3)
                        heap.push(vert3)

            return derp
    return []


def water_held2(mesh):
    mesh.calculateNormals()
    water_line = 0
    seen = set()

    for vert in sorted(mesh.verts, key=lambda vert: vert.p[1]):
        if vert in seen:
            continue
        if any(neighbor.p[1] < vert.p[1] for neighbor in vert.neighbors()):
            continue
        if vert.normal[1] < 0:
            continue
        else:
            # ring = set(vert.neighbors())
            ring = vert.neighbors()
            within = set([ vert ])
            # heap = MyHeap(key=lambda v: v.p[1])

            # heap.push_all(ring)
            # water_level = min(v.p[1] for v in ring)

            for _ in range(1):
            # while True:
                changes_made = False
                new_ring = []

                for vert2 in ring:
                    foo = False
                    for vert3 in vert2.neighbors():
                        if vert3 not in seen and vert3.p[1] >= vert2.p[1]:
                            new_ring.append(vert3)
                            seen.add(vert3)
                            foo = True
                            changes_made = True
                    if not foo:
                        new_ring.append(vert2)

                ring = new_ring

                # if not changes_made:
                    # break

            return within, ring
    return []

def outer_ring(verts):
    ring = set()
    for vert in verts:
        if not all(n in verts for n in vert.neighbors()):
            ring.add(vert)

    ring_neighbors = {}
    for vert in ring:
        ring_neighbors[vert] = [n for n in vert.neighbors() if n in ring ]
    ring = list(ring)

    in_sorted_ring = set()
    sorted_ring = [ring[0]]

    while len(sorted_ring) < len(ring):
        last = sorted_ring[-1]
        neighbors = ring_neighbors[last]
        if neighbors[0] in in_sorted_ring:
            sorted_ring.append(neighbors[1])
        else:
            sorted_ring.append(neighbors[0])

    return sorted_ring

for vert in mesh.verts:
    vert.p[0] *= .1
    vert.p[1] *= .1
    vert.p[2] *= .1
    vert.p[1] -= 2

internal = set(water_held(mesh))
water_height = min(v.p[1] for v in outer_ring(internal))
internal = [v for v in internal if v.p[1] < water_height]

# for vert in internal:
    # if vert.p[1] < water_height:
    # vert.data['color'] = (1.0, 0.0, 0.0)

# outer_ring(internal))
# print(len()
for vert in outer_ring(internal):
    vert.data['color'] = (0.0, 0.0, 1.0)

# verts = water_level
# top_height = min(v.p[1] for v in sorted_ring)
# polygon = [(v.p[0], v.p[2]) for v in sorted_ring]
# triangles = tripy.earclip(polygon)
# print(polygon)
# print(triangles)

view = Viewer()
view.startDraw()
view.drawMesh(mesh, edges=True)

# for p1, p2, p3 in triangles:
#     p1 = (p1[0], top_height, p1[1])
#     p2 = (p2[0], top_height, p2[1])
#     p3 = (p3[0], top_height, p3[1])
#     view.drawTriangle(p1, p2, p3)

view.endDraw()
view.mainLoop()
