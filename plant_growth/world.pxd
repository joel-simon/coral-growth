# from libcpp.set cimport set
# from libcpp.vector cimport vector
# from libcpp.map cimport map

from plant_growth.plant cimport Plant
from plant_growth.spatial_hash cimport SpatialHash

cdef class World:
    cdef public int width, height, soil_height, max_plants, max_cells
    cdef public list plants
    cdef public SpatialHash sh
    cdef dict cell_tree_ids, tree_cell_ids
    cdef object tree

    cdef inline void collision_add_segment(self, id, double x0, double y0, double x1, double y1)

    cdef inline void collision_move_segment(self, int id, double x0, double y0, double x1, double y1)

    cpdef int add_plant(self, double x, double y, double r, network, double efficiency) except -1

    cpdef void simulation_step(self) except *

    cdef void __update_positions(self) except *

    cdef void __insert_new(self, Plant plant, list ids) except *

    cdef inline bint __segment_has_intersection(self, int id0, Plant plant)

    cdef void calculate_light(self, Plant plant) except *

    cdef inline bint __valid_move(self, Plant plant, int cid, double x, double y)
