import heapq
from math import acos, pi, sqrt
from itertools import count
from cymesh.mesh import Mesh
from cymesh.view import Viewer
import tripy

mesh = Mesh.from_obj('cup2.obj')
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

    def __iter__(self):
        for key, i, value in self._data:
            yield value


def water_held(mesh):
    mesh.calculateNormals()

    seen = set()

    vert_height = (lambda vert: vert.p[1])

    for vert in sorted(mesh.verts, key=vert_height):

        if vert in seen:
            continue
        if vert.normal[1] < 0:
            continue

        neighbors = vert.neighbors()
        lowest_neighbor = min(neighbors, key=vert_height)

        if lowest_neighbor.p[1] < vert.p[1]:
            continue

        # The Heap is a ring of closest verts above the water line.
        heap = MyHeap(key=vert_height)
        heap.push_all(neighbors)
        seen.update(neighbors)
        seen.add(vert)

        water_line = lowest_neighbor.p[1]

        result = set([ vert ])


        while len(heap):
            vert2 = heap.pop()

            assert vert2 in seen
            assert vert2.p[1] >= water_line

            result.add(vert2)
            water_level = vert2.p[1]

            for vert in heap:
                assert vert.p[1] >= water_line

            # add neighbors who are above water line to heap.
            for vert3 in vert2.neighbors():
                if vert3 not in seen and vert3.p[1] >= water_level:
                    seen.add(vert3)
                    heap.push(vert3)

        return result

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

# internal = set(water_held(mesh))
# water_height = min(v.p[1] for v in outer_ring(internal))
# internal = [v for v in internal if v.p[1] < water_height]

# for vert in outer_ring(internal):
for vert in water_held(mesh):
    vert.data['color'] = (0.0, 0.0, 1.0)


view = Viewer()
view.startDraw()
view.drawMesh(mesh, edges=True)

view.endDraw()
view.mainLoop()
