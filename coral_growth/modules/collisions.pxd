from cymesh.structures cimport Vert

cdef class MeshCollisionManager:
    cdef public object mesh
    cdef public double[:,:] vertices, normals
    cdef public double blocksize, r
    cdef public int[:,:] particles
    cdef public object grid

    cpdef int[:] getIndices(self, double[:] p) except *
    cpdef void newVert(self, Vert vert) except *
    cpdef bint attemptVertUpdate(self, Vert vert, double[:] p) except *
