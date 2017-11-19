from cymesh.structures cimport Vert

cdef class Cell:
    cdef public int id
    cdef public Vert vert
    cdef public double energy, light, flow
    cdef public double[:] morphogens
    cdef public double[:] last_p
    cdef public unsigned int ctype
