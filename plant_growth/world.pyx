# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True
# cython: linetrace=True

from libc.math cimport cos, sin, round

import numpy as np

from plant_growth.plant cimport Plant
from plant_growth.vec2D cimport Vec2D

from plant_growth import constants
from plant_growth cimport geometry

# def myround(x, base):
#     return int(base * round(x/float(base)))

cdef class World:
    def __init__(self, int width, int height, double light, int soil_height):
        self.width = width
        self.height = height
        self.light = light
        self.soil_height = soil_height
        self.group_width = constants.MAX_EDGE_LENGTH * 1.5
        # self.point_hash = {}

        self.num_buckets = 30
        self.hash_buckets = np.zeros((self.num_buckets, 500), dtype='i')
        self.bucket_size = np.zeros(self.num_buckets, dtype='i')

        self.plants = []

    cpdef add_plant(self, x, y, r, network, efficiency):
        plant = Plant(self, network, efficiency)
        plant.create_circle(x, y, r, constants.SEED_SEGMENTS)
        self.plants.append(plant)
        self.__update()
        plant.update_attributes()

    cpdef simulation_step(self):
        for plant in self.plants:
            if plant.alive:
                plant.grow()

        self.__update()

        for plant in self.plants:
            if plant.alive:
                plant.update_attributes()

    cdef int get_bucket(self, double x, double y):
        # First get spatial section.
        cdef int width = self.group_width
        cdef int q = int(width * round((x - y)/width))

        # Then, hash q to an existing bucket.
        q = (q ^ (q >> 16)) * 0x45d9f3b
        q = (q ^ (q >> 16)) * 0x45d9f3b
        q = q ^ (q >> 16)
        q = q % self.num_buckets

        return q

    cdef __update(self):
        cdef int i, j, cid, id_prev
        cdef double x, y

        cdef object[:] cell_p
        cdef int[:] cell_prev

        cdef Vec2D v_cell, v_prev
        cdef int bucket_id

        for i in range(self.bucket_size.shape[0]):
            self.bucket_size[i] = 0

        for plant in self.plants:
            cell_p = plant.cell_p
            cell_prev = plant.cell_prev

            for cid in range(plant.n_cells):
                id_prev = cell_prev[cid]
                v_cell = cell_p[cid]
                v_prev = cell_p[id_prev]

                x = (v_cell.x + v_prev.x) / 2.0
                y = (v_cell.y + v_prev.y) / 2.0

                bucket_id = self.get_bucket(x, y)

                j = self.bucket_size[bucket_id]
                self.hash_buckets[bucket_id, j] = cid
                self.bucket_size[bucket_id] += 1
                assert j < 500

    cdef bint single_light_collision(self, double x0, double y0, int id_exclude):
        cdef int i, cid, cid_prev, cid_next
        cdef double x1, y1, x2, y2, x3, y3
        cdef Plant plant = self.plants[0]
        cdef Vec2D v1, v2

        cdef object[:] cell_p = plant.cell_p
        cdef int[:] cell_prev = plant.cell_prev

        cdef int bucket_id = self.get_bucket(x0, y0)

        x1 = x0 + 1000 * cos(self.light)
        y1 = y0 + 1000 * sin(self.light)

        # for cid in range(plant.n_cells):
        for i in range(self.bucket_size[bucket_id]):
            cid = self.hash_buckets[bucket_id, i]
            if cid == id_exclude:
                continue

            cid_prev = cell_prev[cid]
            v1 = cell_p[cid]
            v2 = cell_p[cid_prev]

            if geometry.intersect(x0, y0, x1, y1, v1.x, v1.y, v2.x, v2.y):
                return True

        return False


