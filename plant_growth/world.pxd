cdef class World:
    cdef public int width, height, soil_height
    cdef public double light
    cdef public list plants

    cpdef add_plant(self, x, y, r, network, efficiency)

    cpdef single_light_collision(self, double x0, double y0, int id_exclude)

    cpdef update(self)

    cpdef simulation_step(self)
