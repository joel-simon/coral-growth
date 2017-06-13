# cython: boundscheck=True
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True

# from libcpp.set cimport set
# from libcpp.vector cimport vector
# from libcpp.map cimport map

from libc.math cimport floor
import numpy as np
cimport numpy as np

cdef class SpatialHash:
    def __init__(self, double cell_size):
        cdef int i
        assert(cell_size > 0)
        self.cell_size = cell_size
        self.d = dict()
        self.bid_buffer = np.zeros(100, dtype='i')

        self.count = 0
        self.n = 0

    cdef int __cells_for_rect(self, double x1, double y1, double x2, double y2):
        """Return a set of the cells into which r extends."""
        cdef double cx, cy
        cdef int hash_key
        cdef int n = 0

        if x1 > x2:
            x1, x2 = x2, x1

        if y1 > y2:
            y1, y2 = y2, y1

        cy = floor(y1 / self.cell_size)
        while (cy * self.cell_size) <= y2:
            cx = floor(x1 / self.cell_size)
            while (cx * self.cell_size) <= x2:
                hash_key = cantor_pair_func(int(cx), int(cy))
                self.bid_buffer[n] = hash_key
                n += 1
                cx += 1.0
            cy += 1.0

        self.count += n
        self.n += 1
        assert n < 100
        return n

    cdef void add_object(self, int key, double x1, double y1, double x2, double y2):
        """Add an object obj with bounding box"""
        cdef int c
        cdef int n = self.__cells_for_rect(x1, y1, x2, y2)
        for i in range(n):
            c = self.bid_buffer[i]
            if c in self.d:
                self.d[c].add(key)
            else:
                self.d[c] = set([key])

    cdef void remove_object(self, int key, double x1, double y1, double x2, double y2) except *:
        """Remove an object obj with bounding box"""
        cdef int c
        cdef int n = self.__cells_for_rect(x1, y1, x2, y2)
        for i in range(n):
            c = self.bid_buffer[i]
            self.d[c].remove(key)

    cdef void move_object(self, int key, double x1, double y1, double x2, double y2, double x3, double y3, double x4, double y4) except *:
        # Move from (p1, p2) to (p3, p4)
        cdef bint all_same
        all_same = floor(x1 / self.cell_size) == floor(x3 / self.cell_size) and \
                    floor(y1 / self.cell_size) == floor(y3 / self.cell_size) and \
                    floor(x2 / self.cell_size) == floor(x4 / self.cell_size) and \
                    floor(y2 / self.cell_size) == floor(y4 / self.cell_size)
        if not all_same:
            self.remove_object(key, x1, y1, x2, y2)
            self.add_object(key, x3, y3, x4, y4)

    cdef inline set potential_collisions(self, double x1, double y1, double x2, double y2):
        """Get a set of all objects that potentially intersect obj."""
        # cdef list cells

        cdef int i, c, v

        cdef int n = self.__cells_for_rect(x1, y1, x2, y2)
        cdef set potentials = set() #.union(*(self.d[c] for c in cells if c in self.d))

        for i in range(n):
            c = self.bid_buffer[i]
            if c in self.d:
                potentials.update(self.d[c])

        return potentials

