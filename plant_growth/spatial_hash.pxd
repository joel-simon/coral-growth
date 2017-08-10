from plant_growth.vector3D cimport Vect

cdef struct AABB:
    double minx
    double maxx
    double miny
    double maxy
    double minz
    double maxz

cdef AABB bb_from_tri(Vect *v1, Vect *v2, Vect *v3)

cdef class SpatialHash:
    cdef int count, n
    cdef double cell_size

    cdef public dict d
    cdef public long[:] bid_buffer

    cdef int __cells_for_rect(self, AABB bb)
    cdef void add_object(self, long key, AABB bb)
    cdef void remove_object(self, long key) except * #, AABB bb
    cdef void move_object(self, long key, AABB frombb, AABB tobb) except *
    cdef set collisions(self, AABB bb)

    # cdef void add_tri(self, int key, Vect *v1, Vect *v2, Vect *v3) except *
    # cdef void remove_tri(self, int key, Vect *v1, Vect *v2, Vect *v3) except *
