# from libcpp.set cimport set
# from libcpp.vector cimport vector
# from libcpp.map cimport map

cdef inline int cantor_pair_func(int k1, int k2):
    # https://en.wikipedia.org/wiki/Pairing_function#Cantor_pairing_function
    # Only works for non negative which is fine here.
    return <int>(.5 * (k1 + k2) * (k1 + k2 + 1) + k2)

cdef class SpatialHash:
    cdef double cell_size
    cdef dict d
    # cdef map[int, set[int]] d

    cdef list __cells_for_rect(self, double x1, double y1, double x2, double y2)

    cdef void add_object(self, int key, double x1, double y1, double x2, double y2)

    cdef void remove_object(self, int key, double x1, double y1, double x2, double y2) except *

    cdef void move_object(self, int key, double x1, double y1, double x2, double y2, double x3, double y3, double x4, double y4) except *

    cdef inline set potential_collisions(self,double x1, double y1, double x2, double y2)
