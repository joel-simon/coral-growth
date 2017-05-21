# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True
# cython: linetrace=True

from libc.math cimport cos, sin

import numpy as np

from plant_growth.plant cimport Plant
from plant_growth.vec2D cimport Vec2D

from plant_growth import constants
from plant_growth cimport geometry

cdef class World:
    def __init__(self, int width, int height, double light, int soil_height):
        self.width = width
        self.height = height
        self.light = light
        self.soil_height = soil_height

        self.plants = []

    cpdef add_plant(self, x, y, r, network, efficiency):
        plant = Plant(self, network, efficiency)
        plant.create_circle(x, y, r, constants.SEED_SEGMENTS)
        self.plants.append(plant)
        self.update()
        plant.update_attributes()

    cpdef single_light_collision(self, double x0, double y0, int id_exclude):
        cdef int cid, cid_prev
        cdef double x1, y1, x2, y2, x3, y3
        cdef Plant plant = self.plants[0]
        cdef object[:] cell_p = plant.cell_p
        cdef int[:] cell_prev = plant.cell_prev
        cdef Vec2D v1, v2
        cdef int n = plant.n_cells

        x1 = x0 + cos(self.light) * 1000
        y1 = y0 + sin(self.light) * 1000

        for cid in range(n):
        # for cid in self.idx.intersection((x0, y0, x1, y1)):
            # if
            if cid == id_exclude:
                continue

            cid_prev = cell_prev[cid]
            v1 = cell_p[cid]
            v2 = cell_p[cid_prev]

            if geometry.intersect(x0, y0, x1, y1, v1.x, v1.y, v2.x, v2.y):
                return True

        return False

    cpdef update(self):
        pass
        # cdef int cid
        # cdef double x1, y1, x2, y2
        # cdef object[:] cell_p
        # cdef int[:] cell_prev

        # self.idx = index.Index()

        # for plant in self.plants:
        #     cell_p = plant.cell_p
        #     cell_prev = plant.cell_prev

        #     for cid in range(plant.n_cells):
        #         x1, y1 = cell_p[cid]
        #         x2, y2 = cell_p[cell_prev[cid]]

        #         if x1 > x2:
        #             x2, x1, = x1, x2

        #         if y1 > y2:
        #             y2, y1, = y1, y2

        #         self.idx.insert(cid, (x1, y1, x2, y2))

    cpdef simulation_step(self):
        for plant in self.plants:
            if plant.alive:
                plant.grow()

        self.update()

        for plant in self.plants:
            if plant.alive:
                plant.update_attributes()


