cdef class MeshCollisionManager:
    cdef public object mesh
    cdef public double[:,:] vertices
    cdef public double blocksize
    cdef public double[:] radii
    cdef public unsigned int[:,:] particles
    cdef public object grid

    cdef bint collides(self, int id1, int id2)
    cpdef void newVert(self, int id) except *
    cpdef bint attemptVertUpdate(self, int id, double[:] p) except *
