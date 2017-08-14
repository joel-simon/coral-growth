# cython: boundscheck=True
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True
from cymem.cymem cimport Pool

ctypedef unsigned int uint

cdef struct Entry:
    void *key
    Entry *next

cdef class TriHash3D:
    cdef Pool mem
    cdef double cell_size
    cdef int world_size, l, l2, size, dim_size, dim_size2
    cdef Entry **bins

    cdef void initialize(self)
    cdef uint tri_bucket(self, double a[3], double b[3], double c[3])
    cdef void add_tri(self, void *key, double a[3], double b[3], double c[3]) except *
    cdef void remove_tri(self, void *key, double a[3], double b[3], double c[3]) except *
    cdef void move_tri(self, void *key, double a[3], double b[3], double c[3],
                                        double d[3], double e[3], double f[3]) except *
    cdef uint neighbors(self, double a[3], double b[3], double c[3], uint n, void **results)  except *

