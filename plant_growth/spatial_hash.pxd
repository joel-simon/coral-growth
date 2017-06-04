cdef class SpatialHash:
    cdef double cell_size
    cdef object d

    cdef list __cells_for_rect(self, double x1, double y1, double x2, double y2)

    cdef void add_object(self, int key, double x1, double y1, double x2, double y2)

    cdef void remove_object(self, int key, double x1, double y1, double x2, double y2)

    cdef void move_object(self, int key, double x1, double y1, double x2, double y2, double x3, double y3, double x4, double y4)

    cdef set potential_collisions(self, int key, double x1, double y1, double x2, double y2)
