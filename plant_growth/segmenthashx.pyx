# cython: cdivision=True
# cython: profile=False

from vec2D cimport Vec2D
from libc.math cimport acos, M_PI, sqrt, fmin, fmax, floor, fabs, abs

import math
import numpy as np
from cython.view cimport array as cvarray

cdef float ccw(float ax, float ay, float bx, float By, float cx, float cy ):
    return (cy-ay) * (bx-ax) > (By-ay) * (cx-ax)

# Return true if line segments AB and CD intersect
# This does not handle colinear cases well.
cdef int intersect(float ax, float ay, float bx, float By, float cx, float cy,
                    float dx, float dy):
    return ccw(ax, ay, cx, cy, dx, dy) != ccw(bx, By, cx, cy, dx, dy) and ccw(ax, ay, bx, By, cx, cy) != ccw(ax, ay, bx, By, dx, dy)


cdef class SegmentHash:
    """docstring for SegmentHash"""
    cdef public int width, height, d, num_x, num_y
    cdef public object segments
    cdef public list[:, :] data
    cdef public int[:, :] buff # Store i, j index values into data

    def __init__(self, width, height, d):
        self.width = width
        self.height = height
        self.d = int(d)
        self.segments = None # list of vec2d tuples

        self.num_x = int(width/self.d)
        self.num_y = int(height/self.d)
        # print('Initialized polygrid with', self.num_x, self.num_y, self.d)

        cdef int max_result = self.num_x + self.num_y
        self.buff = np.zeros((max_result, 2), dtype=np.dtype("i"))

        self.clear()

    def clear(self):
        self.segments = dict()
        # Each data bucket stores a list of IDs
        self.data = np.empty((self.num_x, self.num_y), dtype=list)
        for j in range(self.num_x):
            for k in range(self.num_y):
                self.data[j, k] = []

    def add_segment(self, id, p0, p1):
        self.segments[id] = (p0, p1)
        cdef int i, j, k

        n = self._segment_supercover(p0, p1)
        for i in range(n):
            j = self.buff[i, 0]
            k = self.buff[i, 1]
            self.data[j, k].append(id)

    # float x0, float x1, float y0, float y1
    def _segment_supercover(self, p0, p1):
        """ An iterator over the squares that the segment intersects
        """
        cdef float x0 = p0.x
        cdef float y0 = p0.y
        cdef float x1 = p1.x
        cdef float y1 = p1.y
        # object result = []
        # Number of squares to cross.
        cdef df = <float>self.d
        cdef int dx = <int>((x1//df) - (x0 // df))
        cdef int dy = <int>((y1//df) - (y0 // df))
        cdef int nx = abs(dx)
        cdef int ny = abs(dy)

        cdef int sign_x = 1 if dx > 0 else -1
        cdef int sign_y = 1 if dy > 0 else -1

        cdef int px = int(x0//df)
        cdef int py = int(y0//df)

        cdef int ix = 0
        cdef int iy = 0

        cdef int n = 0
        self.buff[n, 0] = px
        self.buff[n, 1] = py

        while (ix < nx or iy < ny):
            if ny == 0:
                px += sign_x
                ix += 1
            elif nx == 0:
                py += sign_y
                iy += 1
            elif ((0.5+ix) / nx < (0.5+iy) / ny):
                # next step is horizontal
                px += sign_x
                ix += 1
            else:
                # next step is vertical
                py += sign_y
                iy += 1
            n += 1
            self.buff[n, 0] = px
            self.buff[n, 1] = py

        return n+1

    # cdef int in_bounds(self, int x, int y):
    #     if x < 0 or x >= self.width:
    #         return False
    #     if y < 0 or y >= self.height:
    #         return False
    #     return True

    def segment_intersect(self, p0, p1):
        # assert(self.in_bounds(p0))
        # assert(self.in_bounds(p1))
        cdef int i, j, k, n
        x0, y0 = p0
        x1, y1 = p1

        # brute force for testing
        # for id, (p2, p3) in enumerate(self.segments):
        #     x2, y2 = p2
        #     x3, y3 = p3
        #     if intersect(x0, y0, x1, y1, x2, y2, x3, y3):
        #         yield id

        # else:
        seen = set()
        n = self._segment_supercover(p0, p1)
        for i in range(n):
            j = self.buff[i, 0]
            k = self.buff[i, 1]
            if j < 0 or j >= self.num_x:
                continue
            if k < 0 or k >= self.num_y:
                continue
            for id in self.data[j, k]:
                if id not in seen:
                    seen.add(id)
                    p2, p3 = self.segments[id]
                    x2, y2 = p2
                    x3, y3 = p3
                    if intersect(x0, y0, x1, y1, x2, y2, x3, y3):
                        yield id
