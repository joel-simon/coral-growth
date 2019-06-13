from math import sqrt
import numpy as np
from coral_growth.growth_form import GrowthForm
from coral_growth.modules.water_hold import water_hold
from itertools import count
# import heapq
# import tripy
# class MyHeap(object):
#     def __init__(self, initial=None, key=lambda x:x):
#         self.key = key
#         self._counter = count()
#         if initial:
#             self._data = [(key(item), next(self._counter), item) for item in initial]
#             heapq.heapify(self._data)
#         else:
#             self._data = []

#     def push(self, item):
#         heapq.heappush(self._data, (self.key(item), next(self._counter), item))

#     def push_all(self, items):
#         for item in items:
#             self.push(item)

#     def pop(self):
#         return heapq.heappop(self._data)[2]

#     def __nonzero__(self):
#         return bool(len(self._data))

#     def __len__(self):
#         return len(self._data)



# def signed_triangle_volume(p1, p2, p3):
#     v321 = p3[0] * p2[1] * p1[2]
#     v231 = p2[0] * p3[1] * p1[2]
#     v312 = p3[0] * p1[1] * p2[2]
#     v132 = p1[0] * p3[1] * p2[2]
#     v213 = p2[0] * p1[1] * p3[2]
#     v123 = p1[0] * p2[1] * p3[2]
#     return (1.0/6.0) * (-v321 + v231 + v312 - v132 - v213 + v123)

# def outer_ring(verts):
#     ring = set()
#     for vert in verts:
#         if not all(n in verts for n in vert.neighbors()):
#             ring.add(vert)

#     ring_neighbors = {}
#     for vert in ring:
#         ring_neighbors[vert] = [n for n in vert.neighbors() if n in ring ]
#     ring = list(ring)

#     in_sorted_ring = set()
#     sorted_ring = [ring[0]]

#     while len(sorted_ring) < len(ring):
#         last = sorted_ring[-1]
#         neighbors = ring_neighbors[last]
#         if neighbors[0] in in_sorted_ring:
#             sorted_ring.append(neighbors[1])
#         else:
#             sorted_ring.append(neighbors[0])

#     return sorted_ring

# def water_held(mesh):
#     mesh.calculateNormals()
#     water_line = 0
#     seen = set()

#     for vert in sorted(mesh.verts, key=lambda vert: vert.p[1]):
#         if vert in seen:
#             continue
#         if any(neighbor.p[1] < vert.p[1] for neighbor in vert.neighbors()):
#             continue
#         if vert.normal[1] < 0:
#             continue
#         else:
#             derp = set([ vert ])
#             heap = MyHeap(key=lambda vert: vert.p[1])
#             heap.push(vert)
#             water_level = vert.p[1]

#             while len(heap):
#                 vert2 = heap.pop()

#                 if vert2.p[1] >= water_level:
#                     derp.add(vert2)
#                     water_level = vert2.p[1]

#                     for vert3 in vert2.neighbors():
#                         if vert3 not in seen:
#                             seen.add(vert3)
#                             heap.push(vert3)
#             return derp
#     return []

class Cup(GrowthForm):
    def __init__(self, obj_path, network, net_depth, traits, params):
        attributes = ['holding_water']
        super().__init__(attributes, obj_path, network, net_depth, traits, params)

    @classmethod
    def calculate_inouts(cls, params):
        n_inputs, n_outputs = GrowthForm.calculate_inouts(params)
        n_inputs += 1 # holding_water
        return n_inputs, n_outputs

    # def calculateWaterHold(self):
        # derp = set(water_held(self.mesh))
        # if len(derp) == 0:
        #     return 0.0
        # ring = outer_ring(derp)

        # polygon = [ (v.p[0], v.p[2]) for v in ring ]
        # top_height = min(v.p[1] for v in ring)
        # triangles = tripy.earclip(polygon)
        # # print(len(triangles), print(len(triangles[0])))
        # # print(triangles)
        # for i, vert in enumerate(self.mesh.verts):
        #     if vert in derp:
        #         self.node_attributes[i, 0] = 1

        # v = 0
        # for face in self.mesh.faces:
        #     v1, v2, v3 = face.vertices()
        #     if v1 in derp and v2 in derp and v3 in derp:
        #         v += signed_triangle_volume(v1.p, v2.p, v3.p)

        # for p1, p2, p3 in triangles:
        #     p1 = (p1[0], top_height, p1[1])
        #     p2 = (p2[0], top_height, p2[1])
        #     p3 = (p3[0], top_height, p3[1])
        #     v += signed_triangle_volume(p1, p2, p3)

        # return abs(v)

    # def calculateAttributes(self):
    #     super()
    #     self.calculateWaterHold()

    def fitness(self):
        return water_hold(self.mesh, self.max_edge_len)
        # bbox = self.mesh.boundingBox()
        # volume = (bbox[1]-bbox[0]) * (bbox[3]-bbox[2]) * (bbox[5]-bbox[4])
        # return volume
