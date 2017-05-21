cdef inline int myround(double x, int base):
    return int(base * round(x/base))

cdef class World:
    cdef public int width, height, soil_height, group_width, num_buckets
    cdef public double light
    cdef public list plants
    # cdef dict point_hash

    cdef int[:] bucket_size
    cdef int[:, :] hash_buckets


    cpdef add_plant(self, x, y, r, network, efficiency)

    cpdef simulation_step(self)

    cdef int get_bucket(self, double x, double y)

    cdef bint single_light_collision(self, double x0, double y0, int id_exclude)

    cdef __update(self)
