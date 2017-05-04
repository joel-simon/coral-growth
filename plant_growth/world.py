from __future__ import division, print_function
import random
import math
import numpy as np

from plant_growth.cell import Cell
from plant_growth.vec2D import Vec2D
from plant_growth.plant import Plant
from plant_growth import linkedlist, segmenthashx, geometry, constants

# from recordclass import recordclass

# def lerp(start, end, t):
#     return start + t * (end-start)

# def diagonal_distance(p0, p1):
#     dx, dy = p1.x - p0.x, p1.y - p0.y
#     return max(abs(dx), abs(dy))

# def round_point(p):
#     return Vec2D(int(p.x), int(p.y))

# def line(p0, p1):
#     points = []
#     N = diagonal_distance(p0, p1)
#     for step in range(N):
#         t = 0 if N == 0 else (step / N)
#         yield round_point(lerp(p0, p1, t))

class World(object):
    """docstring for World"""
    def __init__(self, width, height, light, soil_height):
        self.width = width
        self.height = height
        self.light = light
        self.soil_height = soil_height

        self.sh = segmenthashx.SegmentHash(width, height, int(constants.MAX_EDGE_LENGTH)*2, 10000)

        self.plants = []

        self.cell_inputs = np.zeros((constants.NUM_INPUTS+1))

        self.__next_cell_id = 0

    def __in_bounds(self, p):
        if p.x >= self.width or p.x < 0:
            return False
        if p.y >= self.height or p.y < 0:
            return False
        return True

    def make_cell(self, p):
        """
        Called by a Plant when it needs a new cell.
        """
        cell = Cell(self.__next_cell_id, p)
        self.__next_cell_id += 1
        return cell

    def add_plant(self, polygon, network, efficiency):
        plant = Plant(self, network, polygon, efficiency)
        self.plants.append(plant)
        self.update_plant_attributes()

    def single_light_collision(self, P, id_exclude):
        light = P + Vec2D(math.cos(self.light), math.sin(self.light)) * 1000
        for id in self.sh.segment_intersect(light.x, light.y, P.x, P.y):
            if id != id_exclude:
                return True
        return False

    def update_plant_attributes(self):
        self.sh.clear()
        for plant in self.plants:
            for cell in plant.cells:
                self.sh.add_segment(cell.id, cell.P.x, cell.P.y, cell.prev.P.x, cell.prev.P.y)

        for plant in self.plants:
            plant.update_attributes()

    def __valid_move(self, plant, cell, new_p):
        if not self.__in_bounds(new_p):
            return False

        v1 = cell.next.P - new_p
        v2 = cell.prev.P - new_p
        curvature = v1.angle_clockwise(v2)

        if curvature > constants.MAX_ANGLE:
            return False

        if plant.grid[new_p.x, new_p.y]:
            return False

        x, y = (new_p+cell.prev.P)/2
        if plant.grid[x, y]:
            return False

        x, y = (new_p+cell.next.P)/2
        if plant.grid[x, y]:
            return False

        return True

    def cell_calculate_output(self, cell, plant):
        """
        Map cell stats to nerual input in [-1, 1] range.
        """
        self.cell_inputs[0] = (cell.light*2) - 1
        self.cell_inputs[1] = (cell.water*2) - 1
        self.cell_inputs[2] = (cell.curvature/(math.pi)) - 1
        self.cell_inputs[3] = (plant.consumption*2) - 1
        # self.cell_inputs[4] = plant.water / plant.light
        self.cell_inputs[4] = 1 # The last input is always used as bias.

        plant.network.Flush()
        plant.network.Input(self.cell_inputs)
        plant.network.ActivateFast()
        output = plant.network.Output()
        return output

    def calculate_plant_changes(self):
        for plant in self.plants:
            if not plant.alive:
                continue

            # Calculate cell movements and removals.
            for cell in plant.cells:
                output = self.cell_calculate_output(cell, plant)
                growth = output[0] * constants.CELL_MAX_GROWTH
                # death = output[1] > 0.5

                # if death:
                #     cell.alive = False

                # Crate normal Vector.
                Sa = cell.prev.P - cell.P
                Sb = cell.next.P - cell.P
                N = Sa.cross(Sb).normed()
                new_p1 = cell.P + N * growth
                new_p2 = cell.P + N * growth * 2

                if self.__valid_move(plant, cell, new_p1):
                    cell.new_p = new_p1
                else:
                    cell.new_p = cell.P.copy()

    def apply_plant_changes(self):
        for plant in self.plants:
            # for cell in plant.cells:
            #     if cell.alive == False:
            #         plant.cells.remove(cell)
            if len(plant.cells) < constants.MAX_CELLS: # Cant insert any new cells.
                for cell in plant.cells:
                    cell.P = cell.new_p

                plant.split_links()

    def simulation_step(self):
        self.calculate_plant_changes()
        self.apply_plant_changes()
        self.update_plant_attributes()


