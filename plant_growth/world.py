from __future__ import division, print_function
import random
import math
import numpy as np

from plant_growth.cell import Cell
from plant_growth.vec2D import Vec2D
from plant_growth.plant import Plant
from plant_growth import linkedlist, segmenthashx, geometry, constants


class World(object):
    """docstring for World"""
    def __init__(self, width, height, light, soil_height):
        self.width = width
        self.height = height
        self.light = light
        self.soil_height = soil_height

        self.sh = segmenthashx.SegmentHash(width, height, int(constants.MAX_EDGE_LENGTH)*2, 10000)
        self.plants = []

    def in_bounds(self, x, y):
        if x >= self.width or x < 0:
            return False
        if y >= self.height or y < 0:
            return False
        return True

    def add_plant(self, x, y, r, network, efficiency):
        plant = Plant(self, network, efficiency)
        plant.create_circle(x, y, r, constants.SEED_SEGMENTS)
        self.plants.append(plant)
        plant.update_attributes()
        self.update()

    def single_light_collision(self, P, id_exclude):
        light = P + Vec2D(math.cos(self.light), math.sin(self.light)) * 1000
        for id in self.sh.segment_intersect(light.x, light.y, P.x, P.y):
            if id != id_exclude:
                return True
        return False

    def update(self):
        self.sh.clear()
        for plant in self.plants:
            for cell in plant.cells:
                x1, y1 = cell.vector
                x2, y2 = cell.prev.vector
                self.sh.add_segment(cell.id, x1, y1, x2, y2)

    def simulation_step(self):
        for plant in self.plants:
            if plant.alive:
                plant.grow()

        self.update()

        for plant in self.plants:
            if plant.alive:
                plant.update_attributes()


