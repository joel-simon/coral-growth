from plant_growth.plant cimport Plant

cdef inline int myround(double x, int base):
    return int(base * round(x/base))

cdef class World:
    cdef public int width, height, soil_height, max_plants
    cdef public list plants
    cdef public object sh

    cpdef int add_plant(self, double x, double y, double r, network, double efficiency)

    cpdef void simulation_step(self)

    cdef void __insert_new(self, Plant plant, list ids) except *

    cdef bint __segment_has_intersection(self, int id0, Plant plant)

    cdef void __fix_collision(self, Plant plant) except *

    cdef void calculate_light(self, Plant plant)
