# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True

from __future__ import print_function
from libc.math cimport cos, sin, round

import numpy as np
cimport numpy as np

from plant_growth.plant cimport Plant
from plant_growth import constants
from plant_growth cimport geometry
from plant_growth.spatial_hash import SpatialHash

cdef class World:
    def __init__(self, object params):
        self.width  = params['width']
        self.height = params['height']
        self.soil_height = params['soil_height']
        self.max_plants  = params['max_plants']

        self.plants = []
        self.sh = SpatialHash(cell_size=constants.CELL_SIZE)

        # self.__open_plant_ids = list(reversed(range(self.max_plants)))
        # self.plant_alive = np.zeros(self.max_plants)
        # self.plant_x = np.zeros((self.max_plants, constants.MAX_CELLS))
        # self.plant_y = np.zeros((self.max_plants, constants.MAX_CELLS))

    cpdef int add_plant(self, double x, double y, double r, network, double efficiency):
        # if len(self.__open_plant_ids) == 0:
        #     raise ValueError()

        # cdef int plant_id = self.__open_plant_ids.pop()
        # cdef object x_arr = self.plant_x[plant_id]

        cdef Plant plant = Plant(self, network, efficiency)
        # self.plant_alive[plant_id] = 1
        plant.create_circle(x, y, r, constants.SEED_SEGMENTS)
        self.plants.append(plant)
        plant.order_cells()
        plant.update_attributes()

        cdef int id1, id2
        for id1 in plant.cell_order[:plant.n_cells]:
            id2 = plant.cell_next[id1]
            self.sh.add_object(id1, plant.cell_x[id1], plant.cell_y[id1], plant.cell_x[id2], plant.cell_y[id2])

        return 0 # To eventually become plant id.

    # cdef void kill_plant(self, Plant plant):
    #     self.plant_alive[plant.id] = 0

    cpdef void simulation_step(self):
        """ The main function called from outside.
            We assume the plant attributes begin up to date.
        """
        cdef Plant plant

        for plant in self.plants:
            if plant.alive:
                plant.grow()

        self.__fix_collisions()

        for plant in self.plants:
            if plant.alive:
                self.__insert_new(plant, plant.split_links())
                plant.order_cells()
                plant.update_attributes()

    cdef void __insert_new(self, Plant plant, list ids) except *:
        """ Remove segments that were split and add new.
            List if ids of newly created cells.
        """
        cdef int id0, id1, id2
        # id1 has been inserted betwwen 0 and 2 {id0 - id1 - id2}
        for id1 in ids:
            id0 = plant.cell_prev[id1]
            id2 = plant.cell_next[id1]

            self.sh.remove_object(id0, plant.cell_x[id0], plant.cell_y[id0],
                                       plant.cell_x[id2], plant.cell_y[id2])

            self.sh.add_object(id0, plant.cell_x[id0], plant.cell_y[id0],
                                    plant.cell_x[id1], plant.cell_y[id1])

            self.sh.add_object(id1, plant.cell_x[id1], plant.cell_y[id1],
                                    plant.cell_x[id2], plant.cell_y[id2])

    def __fix_collisions(self):
        # cdef Plant plant
        # cdef
        for plant in self.plants:
            if plant.alive:
                self.__fix_collision(plant)

    cdef bint __segment_has_intersection(self, int id0, Plant plant):
        cdef int id1, id2, id3
        cdef double x0, y0, x1, y1, x2, y2, x3, y3
        id1 = plant.cell_next[id0]
        x0 = plant.cell_x[id0]
        y0 = plant.cell_y[id0]
        x1 = plant.cell_x[id1]
        y1 = plant.cell_y[id1]

        for id2 in self.sh.potential_collisions(id0, x0, y0, x1, y1):
            id3 = plant.cell_next[id2]
            x2 = plant.cell_x[id2]
            y2 = plant.cell_y[id2]
            x3 = plant.cell_x[id3]
            y3 = plant.cell_y[id3]

            if id2 != id1 and id3 != id0:
                if geometry.intersect(x0, y0, x1, y1, x2, y2, x3, y3):
                    return True

        return False

    cdef void __fix_collision(self, Plant plant) except *:
        cdef int id0, id1, id2
        cdef double old_x, old_y

        for id1 in plant.cell_order[:plant.n_cells]:
            id0 = plant.cell_prev[id1]
            id2 = plant.cell_next[id1]

            old_x, old_y = plant.cell_x[id1], plant.cell_y[id1]

            plant.cell_x[id1] = plant.cell_next_x[id1]
            plant.cell_y[id1] = plant.cell_next_y[id1]

            if self.__segment_has_intersection(id1, plant) or self.__segment_has_intersection(id0, plant):
                # Undo movement.
                plant.cell_x[id1] = old_x
                plant.cell_y[id1] = old_y
            else:
                self.sh.move_object(id0, plant.cell_x[id0], plant.cell_y[id0], old_x, old_y, plant.cell_x[id0], plant.cell_y[id0], plant.cell_x[id1], plant.cell_y[id1])
                # self.sh.remove_object(id0, plant.cell_x[id0], plant.cell_y[id0], old_x, old_y)
                # self.sh.add_object(id0, plant.cell_x[id0], plant.cell_y[id0], plant.cell_x[id1], plant.cell_y[id1])

                self.sh.move_object(id1, old_x, old_y, plant.cell_x[id2], plant.cell_y[id2], plant.cell_x[id1], plant.cell_y[id1], plant.cell_x[id2], plant.cell_y[id2])
                # self.sh.remove_object(id1, old_x, old_y, plant.cell_x[id2], plant.cell_y[id2])
                # self.sh.add_object(id1, plant.cell_x[id1], plant.cell_y[id1], plant.cell_x[id2], plant.cell_y[id2])

    cdef void calculate_light(self, Plant plant):
        """
        We assume there are no segment intersections.
        """
        cdef int i, cell_left, cell_right, cell_index
        cdef double x0, y0, x1, y1, x2, y2, slope
        cdef bint is_above
        cdef long[:] cells_indexes_ordered

        # TODO: compare with merge sort and insertion sort for speed.
        cells_indexes_ordered = np.asarray(plant.cell_x[:plant.max_i]).argsort()

        for i in range(plant.max_i):
            plant.cell_light[i] = 0

        cell_left = cells_indexes_ordered[0]
        plant.cell_light[cell_left] = 1

        for i in range(plant.max_i):
            cell_index = cells_indexes_ordered[i]

            if plant.cell_alive[cell_index]:
                x0 = plant.cell_x[cell_index]
                y0 = plant.cell_y[cell_index]

                x1, y1 = plant.cell_x[cell_left], plant.cell_y[cell_left]

                if plant.cell_x[plant.cell_next[cell_left]] > plant.cell_x[plant.cell_prev[cell_left]]:
                    cell_right = plant.cell_next[cell_left]
                else:
                    cell_right = plant.cell_prev[cell_left]

                x2, y2 = plant.cell_x[cell_right], plant.cell_y[cell_right]

                slope = (y2 - y1) / (x2 - x1)
                is_above = y0 >= slope*(x0-x1) + y1

                if x0 > x2 or is_above:
                    plant.cell_light[cell_index] = 1
                    cell_left = cell_index

