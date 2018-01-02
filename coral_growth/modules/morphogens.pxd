cimport numpy as np
import numpy as np
from cymesh.mesh cimport Mesh
from cymem.cymem cimport Pool

cdef struct Node:
    int key
    Node *next

cdef class Morphogens:
    cdef Pool mem
    cdef public object coral
    cdef public Mesh mesh
    cdef public int n_morphogens
    cdef public double[:, :] U, V
    cdef public double[:] F, K, diffU, diffV, dU, dV
    cdef public unsigned short[:] n_neighbors
    cdef Node **neighbors

    cpdef void update(self, int steps) except *
    cpdef void gray_scott(self, int steps, int mi) except *
