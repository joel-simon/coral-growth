# cython: boundscheck=True
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True

from __future__ import print_function, division
from plant_growth.vector3D cimport Vect
from libc.math cimport floor, fmin, fmax
import numpy as np
cimport numpy as np

cdef AABB bb_from_tri(Vect *v1, Vect *v2, Vect *v3):
    cdef AABB bb
    bb.minx = fmin(fmin(v1.x, v2.x), v3.x)
    bb.maxx = fmax(fmax(v1.x, v2.x), v3.x)
    bb.miny = fmin(fmin(v1.y, v2.y), v3.y)
    bb.maxy = fmax(fmax(v1.y, v2.y), v3.y)
    bb.minz = fmin(fmin(v1.z, v2.z), v3.z)
    bb.maxz = fmax(fmax(v1.z, v2.z), v3.z)
    return bb

cdef class SpatialHash:
    def __init__(self, double cell_size):
        assert(cell_size > 0)

        self.cell_size = cell_size
        self.d = dict()
        self.bid_buffer = np.zeros(100, dtype='int64')

    cdef int __cells_for_rect(self, AABB bb):
        cdef double cx, cy, cz
        cdef long hash_key
        cdef int n = 0

        cy = floor(bb.miny / self.cell_size)
        while (cy * self.cell_size) <= bb.maxy:
            cx = floor(bb.minx / self.cell_size)
            while (cx * self.cell_size) <= bb.maxx:
                cz = floor(bb.minz / self.cell_size)
                while (cz * self.cell_size) <= bb.maxz:
                    hash_key = ((<short>cx)<< 32) + (<short>cy)<<16 + <short>cz
                    self.bid_buffer[n] = hash_key
                    n += 1
                    cz += 1.0
                cx += 1.0
            cy += 1.0

        assert n < 100

        return n

    # cdef void add_tri(self, long key, Vect *v1, Vect *v2, Vect *v3) except *:
    #
    #     # self.add_object(key, &bb)

    # cdef void remove_tri(self, long key, Vect *v1, Vect *v2, Vect *v3) except *:
    #     cdef AABB bb
    #     # bb.minx = min(v1.p.x, v2.p.x, v3.p.x)
    #     # bb.maxx = max(v1.p.x, v2.p.x, v3.p.x)
    #     # bb.miny = min(v1.p.y, v2.p.y, v3.p.y)
    #     # bb.maxy = max(v1.p.y, v2.p.y, v3.p.y)
    #     # bb.minz = min(v1.p.z, v2.p.z, v3.p.z)
    #     # bb.maxz = max(v1.p.z, v2.p.z, v3.p.z)
    #     # self.remove_object(key, bb)

    cdef void add_object(self, long key, AABB bb):
        """Add an object obj with bounding box"""
        print('adding', key, bb.minx, bb.maxx, bb.miny, bb.maxy, bb.minz, bb.maxz)
        cdef long c
        cdef int n = self.__cells_for_rect(bb)

        for i in range(n):
            c = self.bid_buffer[i]
            if c in self.d:
                self.d[c].add(key)
            else:
                self.d[c] = set([key])

    cdef void remove_object(self, long key) except *: #, AABB bb
        """Remove an object obj with bounding box"""
        print('removing', key)#, bb.minx, bb.maxx, bb.miny, bb.maxy, bb.minz, bb.maxz)
        # cdef long c
        # cdef int n = self.__cells_for_rect(bb)

        # for i in range(n):
            # c = self.bid_buffer[i]
            # self.d[c].remove(key)
        for v in self.d.values():
            if key in v:
                v.remove(key)

    cdef void move_object(self, long key, AABB frombb, AABB tobb) except *:
        # Move from (p1, p2) to (p3, p4)
        # cdef bint all_same
        # all_same = floor(x1 / self.cell_size) == floor(x3 / self.cell_size) and \
        #             floor(y1 / self.cell_size) == floor(y3 / self.cell_size) and \
        #             floor(x2 / self.cell_size) == floor(x4 / self.cell_size) and \
        #             floor(y2 / self.cell_size) == floor(y4 / self.cell_size)
        # if not all_same:
        self.remove_object(key)
        self.add_object(key, tobb)

    cdef set collisions(self, AABB bb):
        """ Get a set of all objects that potentially intersect obj. """
        cdef int i, c, v

        cdef int n = self.__cells_for_rect(bb)
        cdef set potentials = set() #.union(*(self.d[c] for c in cells if c in self.d))

        for i in range(n):
            c = self.bid_buffer[i]
            if c in self.d:
                potentials.update(self.d[c])

        return potentials

    # cdef void empty(self):
    #     self.d = dict()

