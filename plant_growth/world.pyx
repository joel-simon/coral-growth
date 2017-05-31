# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True

from __future__ import print_function
from libc.math cimport cos, sin, round

import numpy as np
cimport numpy as np

from plant_growth.vec2D cimport Vec2D
from plant_growth.plant cimport Plant

from plant_growth import constants
from plant_growth cimport geometry

cdef class World:
    def __init__(self, object params):
        self.width  = params['width']
        self.height = params['height']
        self.soil_height = params['soil_height']
        self.max_plants  = params['max_plants']
        # self.light_angle = params.light
        # self.cos_light = cos(self.light_angle)
        # self.sin_light = sin(self.light_angle)

        self.plants = []

        # Spatial hashing for lighting.
        # The width must be larger than the max edge size.
        # self.group_width = constants.WORLD_GROUP_WIDTH
        # self.num_buckets = constants.WORLD_NUM_BUCKETS
        # self.bucket_max_n = constants.WORLD_BUCKET_SIZE
        # self.hash_buckets = np.zeros((self.num_buckets, self.bucket_max_n), dtype='i')
        # self.bucket_sizes = np.zeros(self.num_buckets, dtype='i')

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
        self.__update()
        plant.update_attributes()
        
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

        # Update spatial hash based off of cell growth, update_attributes
        # uses this to calculate light values.
        self.__update()

        for plant in self.plants:
            if plant.alive:
                plant.update_attributes()


    cdef void __update(self):
        pass

    cdef void calculate_light(self, Plant plant):
        """
        We assume there are no segment intersections.
        """
        cdef int i, cell_left, cell_right, cell_index
        cdef double x0, y0, x1, y1, x2, y2, slope
        cdef bint is_above
        cdef long[:] cells_indexes_ordered

        cells_indexes_ordered = np.asarray(plant.cell_x[:plant.max_i]).argsort()

        for i in range(plant.max_i):
            plant.cell_light[i] = 0

        cell_left = cells_indexes_ordered[0]
        plant.cell_light[cell_left] = 1

        for i in range(1, plant.max_i):
            cell_index = cells_indexes_ordered[i]

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

