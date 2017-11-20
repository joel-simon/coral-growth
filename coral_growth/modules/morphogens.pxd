cimport numpy as np
import numpy as np
from cymesh.mesh cimport Mesh

cdef class Morphogens:
    cdef public object coral
    cdef public Mesh mesh
    cdef public int n_morphogens
    cdef public double[:, :] U, V
    cdef public double[:] F, K, diffU, diffV, dU, dV
    cdef public unsigned short[:] n_neighbors
    cdef public list neighbors

    cpdef void update(self, int steps) except *
    cpdef void gray_scott(self, int steps, int mi) except *
