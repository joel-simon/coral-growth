from plant_growth.plant cimport Plant

cdef inline int myround(double x, int base):
    return int(base * round(x/base))

cdef class World:
    cdef public int width, height, soil_height, group_width, num_buckets, bucket_max_n
    cdef public double light
    cdef public list plants

    cdef double cos_light, sin_light
    cdef int[:] bucket_sizes

    cdef int[:, :] hash_buckets

    cpdef int add_plant(self, double x, double y, double r, network, double efficiency)

    cpdef void simulation_step(self)

    cdef int __get_bucket(self, double x, double y)

    cdef void __double_bucket_size(self)

    cdef bint single_light_collision(self, Plant plant, double x0, double y0, int id_exclude)

    cdef void __update(self)
