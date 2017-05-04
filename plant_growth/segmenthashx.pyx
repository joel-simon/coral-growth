#cython: cdivision=True
#cython: profile=False
#cython: wraparound=False
#cython: boundscheck=False
#cython: nonecheck=False

import math
import numpy as np
from cython.view cimport array as cvarray

cdef int intersect(float p0_x, float p0_y, float p1_x, float p1_y,
                    float p2_x, float p2_y, float p3_x, float p3_y):
    cdef float s1_x, s1_y, s2_x, s2_y, s, t
    s1_x = p1_x - p0_x
    s1_y = p1_y - p0_y
    s2_x = p3_x - p2_x
    s2_y = p3_y - p2_y
    s = (-s1_y * (p0_x - p2_x) + s1_x * (p0_y - p2_y)) / (-s2_x * s1_y + s1_x * s2_y)
    t = ( s2_x * (p0_y - p2_y) - s2_y * (p0_x - p2_x)) / (-s2_x * s1_y + s1_x * s2_y)

    if (s >= 0 and s <= 1 and t >= 0 and t <= 1):
        return True
        # // Collision detected
        # if (i_x != NULL)
        #     *i_x = p0_x + (t * s1_x);
        # if (i_y != NULL)
        #     *i_y = p0_y + (t * s1_y);
        # return 1;

    return False

cdef class SegmentHash:
    """docstring for SegmentHash"""
    cdef public int width, height, d, num_x, num_y, max_segments, __num_segments
    cdef object idx_to_id
    cdef public list[:, :] data
    cdef public float[:, :] segments # A [n_segments, 4] shaped array
    cdef public int[:, :] buff # Store i, j index values into data

    def __init__(self, width, height, d, max_segments):
        self.width = width
        self.height = height
        self.d = int(d)
        self.max_segments = max_segments

        self.num_x = int(width/self.d)
        self.num_y = int(height/self.d)

        cdef int max_result = self.num_x + self.num_y

        self.buff = np.zeros((max_result, 2), dtype=np.dtype("i"))
        self.data = np.empty((self.num_x, self.num_y), dtype=list)

        self.segments = np.zeros(( max_segments, 4 ), dtype=np.dtype("f"))

        self.clear()

    cpdef clear(self):
        cdef int i, j
        self.idx_to_id = dict()
        self.__num_segments = 0

        # Each data bucket stores a list of IDs
        for j in range(self.num_x):
            for k in range(self.num_y):
                self.data[j, k] = []

    cpdef add_segment(self, id, float x0, float y0, float x1, float y1):
        cdef int i, j, k, idx

        idx = self.__num_segments
        assert(idx < self.max_segments)
        self.__num_segments += 1

        self.idx_to_id[idx] = id
        self.segments[idx, 0] = x0
        self.segments[idx, 1] = y0
        self.segments[idx, 2] = x1
        self.segments[idx, 3] = y1

        # n = self.__segment_supercover(x0, y0, x1, y1)
        # for i in range(n):
        #     j = self.buff[i, 0]
        #     k = self.buff[i, 1]
        #     self.data[j, k].append(idx)

    cdef __segment_supercover(self, float x0, float y0, float x1, float y1):
        """ An iterator over the squares that the segment intersects
        """
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

    def segment_intersect(self, float x0, float y0, float x1, float y1):
        cdef int i, j, k, n, idx
        cdef float x2, y2, x3, y3

        for idx in range(self.__num_segments):
            x2 = self.segments[idx, 0]
            y2 = self.segments[idx, 1]
            x3 = self.segments[idx, 2]
            y3 = self.segments[idx, 3]
            if intersect(x0, y0, x1, y1, x2, y2, x3, y3):
                yield self.idx_to_id[idx]

        # seen = set()
        # n = self.__segment_supercover(x0, y0, x1, y1)

        # for i in range(n):
        #     j = self.buff[i, 0]
        #     k = self.buff[i, 1]

        #     if j < 0 or j >= self.num_x:
        #         continue
        #     if k < 0 or k >= self.num_y:
        #         continue

        #     for idx in self.data[j, k]:
        #         if idx not in seen:
        #             seen.add(idx)
        #             x2 = self.segments[idx, 0]
        #             y2 = self.segments[idx, 1]
        #             x3 = self.segments[idx, 2]
        #             y3 = self.segments[idx, 3]
        #             if intersect(x0, y0, x1, y1, x2, y2, x3, y3):
        #                 yield self.idx_to_id[idx]
