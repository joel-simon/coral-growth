# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=True
# cython: cdivision=True

from libc.math cimport floor
from math import isnan
from collections import defaultdict

cdef class SpatialHash:
    def __init__(self, double cell_size):
        assert(cell_size > 0)
        self.cell_size = cell_size
        self.d = defaultdict(set)

    cdef list __cells_for_rect(self, double x1, double y1, double x2, double y2):
        """Return a set of the cells into which r extends."""
        cdef double cx, cy
        cdef list cells = []

        if x1 > x2:
            x1, x2 = x2, x1

        if y1 > y2:
            y1, y2 = y2, y1

        cy = floor(y1 / self.cell_size)
        while (cy * self.cell_size) <= y2:
            cx = floor(x1 / self.cell_size)
            while (cx * self.cell_size) <= x2:
                cells.append( (int(cx), int(cy)) )
                cx += 1.0
            cy += 1.0
        return cells

    cdef void add_object(self, int key, double x1, double y1, double x2, double y2):
        """Add an object obj with bounding box"""
        for c in self.__cells_for_rect(x1, y1, x2, y2):
            self.d[c].add(key)

    cdef void remove_object(self, int key, double x1, double y1, double x2, double y2) except *:
        """Remove an object obj with bounding box"""
        for c in self.__cells_for_rect(x1, y1, x2, y2):
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

    cdef set potential_collisions(self, int key, double x1, double y1, double x2, double y2):
        """Get a set of all objects that potentially intersect obj."""
        cdef list cells
        cdef set potentials

        cells = self.__cells_for_rect(x1, y1, x2, y2)
        potentials = set().union(*(self.d[c] for c in cells if c in self.d))
        potentials.discard(key) # obj cannot intersect itself

        return potentials

