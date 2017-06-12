# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True
from __future__ import print_function
from libc.math cimport cos, sin, round
from math import isnan

import heapq

import numpy as np
cimport numpy as np

from plant_growth.plant cimport Plant
from plant_growth import constants
from plant_growth cimport geometry
from plant_growth.spatial_hash cimport SpatialHash

cdef class World:
    def __init__(self, object params):
        self.width  = params['width']
        self.height = params['height']
        self.max_plants  = params['max_plants']

        self.plants = []
        self.sh = SpatialHash(cell_size=constants.CELL_SIZE)

        # self.__open_plant_ids = list(reversed(range(self.max_plants)))
        # self.plant_alive = np.zeros(self.max_plants)
        # self.plant_x = np.zeros((self.max_plants, constants.MAX_CELLS))
        # self.plant_y = np.zeros((self.max_plants, constants.MAX_CELLS))

    cpdef int add_plant(self, double x, double y, double r, network, double efficiency) except -1:
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

    cpdef void simulation_step(self) except *:
        """ The main function called from outside.
            We assume the plant attributes begin up to date.
        """
        cdef Plant plant

        for plant in self.plants:
            if plant.alive:
                plant.grow()

        self.__update_positions()

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

    cdef void __update_positions(self) except *:
        cdef Plant plant
        cdef int id0, id1, id2, i
        cdef double old_x, old_y, new_x, new_y

        for plant in self.plants:
            if not plant.alive:
                continue

            for i in range(plant.n_cells):
                id1 = plant.cell_order[i]

                if not plant.cell_alive[id1]:
                    continue

                id0 = plant.cell_prev[id1]
                id2 = plant.cell_next[id1]

                old_x = plant.cell_x[id1]
                old_y = plant.cell_y[id1]

                new_x = plant.cell_next_x[id1]
                new_y = plant.cell_next_y[id1]

                if new_x < 0:
                    new_x = 0
                elif new_x >= self.width:
                    new_x = self.width - 1

                if new_y < 0:
                    new_y = 0
                elif new_y >= self.height:
                    new_y = self.height - 1

                assert (not isnan(new_x))
                assert (not isnan(new_y))

                # if self.__valid_move(plant, id1, new_x, new_y):
                #     plant.cell_x[id1] = new_x
                #     plant.cell_y[id1] = new_y
                #     self.sh.move_object(id0, plant.cell_x[id0], plant.cell_y[id0], old_x, old_y, plant.cell_x[id0], plant.cell_y[id0], plant.cell_x[id1], plant.cell_y[id1])
                #     self.sh.move_object(id1, old_x, old_y, plant.cell_x[id2], plant.cell_y[id2], plant.cell_x[id1], plant.cell_y[id1], plant.cell_x[id2], plant.cell_y[id2])

                plant.cell_x[id1] = new_x
                plant.cell_y[id1] = new_y
                if self.__segment_has_intersection(id1, plant) or \
                   self.__segment_has_intersection(id0, plant):
                    # Undo movement.
                    plant.cell_x[id1] = old_x
                    plant.cell_y[id1] = old_y
                else:
                    self.sh.move_object(id0, plant.cell_x[id0], plant.cell_y[id0], old_x, old_y, plant.cell_x[id0], plant.cell_y[id0], plant.cell_x[id1], plant.cell_y[id1])
                    self.sh.move_object(id1, old_x, old_y, plant.cell_x[id2], plant.cell_y[id2], plant.cell_x[id1], plant.cell_y[id1], plant.cell_x[id2], plant.cell_y[id2])

    cdef bint __valid_move(self, Plant plant, int cid, double x, double y):
        cdef int cid_prev, cid_next, cid2, cid3
        cdef double x0, y0, x1, y1, x2, y2, x3, y3, min_x, min_y, max_x, max_y

        cid_prev = plant.cell_prev[cid]
        cid_next = plant.cell_next[cid]

        x_prev = plant.cell_x[cid_prev]
        y_prev = plant.cell_y[cid_prev]
        x_next = plant.cell_x[cid_next]
        y_next = plant.cell_y[cid_next]

        min_x = min(x, x_prev, x_next)
        max_x = max(x, x_prev, x_next)
        min_y = min(y, y_prev, y_next)
        max_y = max(y, y_prev, y_next)

        cdef set collisions = self.sh.potential_collisions(min_x, min_y, max_x, max_y)
        for cid2 in collisions:
            cid3 = plant.cell_next[cid2]

            if cid2 == cid or cid2 == cid_prev or cid2 == cid_next:
                continue

            if cid3 == cid_prev:
                continue

            x2 = plant.cell_x[cid2]
            y2 = plant.cell_y[cid2]
            x3 = plant.cell_x[cid3]
            y3 = plant.cell_y[cid3]

            if geometry.intersect(x, y, x_prev, y_prev, x2, y2, x3, y3):
                return 0

            if geometry.intersect(x, y, x_next, y_next, x2, y2, x3, y3):
                return 0

        return 1

    cdef inline bint __segment_has_intersection(self, int id0, Plant plant):
        cdef int id1, id2, id3
        cdef double x0, y0, x1, y1, x2, y2, x3, y3
        id1 = plant.cell_next[id0]
        x0 = plant.cell_x[id0]
        y0 = plant.cell_y[id0]
        x1 = plant.cell_x[id1]
        y1 = plant.cell_y[id1]

        cdef set collisions = self.sh.potential_collisions(x0, y0, x1, y1)
        for id2 in collisions:
            id3 = plant.cell_next[id2]
            x2 = plant.cell_x[id2]
            y2 = plant.cell_y[id2]
            x3 = plant.cell_x[id3]
            y3 = plant.cell_y[id3]

            if id2 != id1 and id3 != id0:
                if geometry.intersect(x0, y0, x1, y1, x2, y2, x3, y3):
                    return True

        return False

    cdef void calculate_light(self, Plant plant) except *:
        """
        A sweep line algorithm that maintains a heap of tallest open segments.
        For every new segment, if the open segment is above it, there is no light.
        We assume there are no segment intersections.
        """
        cdef int i, cid, cid_prev, cid_next, cid_left, cid_right
        cdef double x0, y0, x1, y1, x2, y2, slope
        cdef bint is_lit
        cdef long[:] cells_indexes_ordered
        cdef list minheap = []

        # TODO: compare with merge sort and insertion sort for speed.
        # cdef void ins_sort(double[:] k):
        #     cdef n = len(k)
        #     for i in range(1, n):    #since we want to swap an item with previous one, we start from 1
        #         j = i                    #bcoz reducing i directly will mess our for loop, so we reduce its copy j instead
        #         while j > 0 and k[j] < k[j-1]: #j>0 bcoz no point going till k[0] since there is no value to its left to be swapped
        #             k[j], k[j-1] = k[j-1], k[j] #syntactic sugar: swap the items, if right one is smaller.
        #             j = j - 1 #take k[j] all the way left to the place where it has a smaller/no value to its left.
        #     # return k

        cells_indexes_ordered = np.asarray(plant.cell_x[:plant.n_cells]).argsort()


        for i in range(plant.n_cells):
            cid = plant.cell_order[i]
            plant.cell_light[i] = 0

        # Iterate across all points from left to right.
        for i in range(plant.n_cells):
            cid = cells_indexes_ordered[i]

            is_lit = False
            x0 = plant.cell_x[cid]
            y0 = plant.cell_y[cid]

            cid_prev = plant.cell_prev[cid]
            cid_next = plant.cell_next[cid]

            # At a new point, remove any closing segments.
            if plant.cell_x[cid_prev] < x0:
                minheap.remove((-plant.cell_y[cid_prev], (cid_prev, cid)))

            if plant.cell_x[cid_next] < x0:
                minheap.remove((-plant.cell_y[cid_next], (cid_next, cid)))

            if len(minheap) == 0:
                is_lit = True
            else:
                y1, (cid_left, cid_right) = minheap[0]
                y1 *= -1
                x1 = plant.cell_x[cid_left]
                x2 = plant.cell_x[cid_right]
                y2 = plant.cell_y[cid_right]
                # See if point is above segment.
                slope = (y2 - y1) / (x2 - x1)
                is_lit = (y0 >= slope * (x0 - x1) + y1)

            # Open any new segments.
            if plant.cell_x[cid_prev] > x0:
                heapq.heappush(minheap, (-y0 , (cid, cid_prev)))

            if plant.cell_x[cid_next] > x0:
                heapq.heappush(minheap, (-y0 , (cid, cid_next)))

            if is_lit and plant.cell_alive[cid]:
                plant.cell_light[cid] = 1

        assert len(minheap) == 0
