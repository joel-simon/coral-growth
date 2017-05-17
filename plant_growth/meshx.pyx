from __future__ import division

import math
import numpy as np

cimport cython
from cython.view cimport array as cvarray
from libc.stdlib cimport malloc, free

cdef struct Vert:
    float x
    float y
    # Edge *e1
    # Edge *e2
    # Edge *e3

cdef struct Edge:
    Vert *v1
    Vert *v2
    Tri *t1
    Tri *t2

cdef struct Tri:
    Vert *e1
    Vert *e2
    Vert *e3

cdef struct HalfEdge:
    

cdef class Mesh:
    cdef Vert *verts
    cdef Edge *edges
    cdef Edge *tris

    def __init__(self, nmax=1000):
        pass

    def __cinit__(self, nmax=1000):
        # pass
        print(str(sizeof(Vert)))
        # print(str(sizeof(&Vert)))
        print(str(sizeof(Edge)))
        print(str(sizeof(Tri)))
        self.verts = <Vert * >malloc(nmax*sizeof(Vert))
    
    def __dealloc__(self):
        free(self.verts)

    cpdef void split_edges(self, float max_l):
        cdef int i
        for i in range(self.num_edges):
            edge = 


cdef Vert v
v.x = 0
v.y = 0
# v.f1 = None
print('Hello')
print(v.x)

