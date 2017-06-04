from plant_growth.plant cimport Plant
from plant_growth.spatial_hash cimport SpatialHash

cdef class World:
    cdef public int width, height, soil_height, max_plants
    cdef public list plants
    cdef public SpatialHash sh

    cpdef int add_plant(self, double x, double y, double r, network, double efficiency)

    cpdef void simulation_step(self)

    cdef void __update_positions(self)

    cdef void __insert_new(self, Plant plant, list ids) except *

    cdef bint __segment_has_intersection(self, int id0, Plant plant)

    cdef void calculate_light(self, Plant plant)
