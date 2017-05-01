from __future__ import division, print_function
import random

from cell import Cell
import geometry
import math

from modules.segmenthash import SegmentHash
from modules.linkedlist import DoubleList

from image_grid import PolygonGrid
from recordclass import recordclass
from vec2D import Vec2D
from constants import NUM_INPUTS, NUM_OUTPUTS, MAX_CELLS
import numpy as np

Plant = recordclass('Plant', [
    'network', 'cells', 'water', 'light', 'volume', 'efficiency', 'alive'
])

class World(object):
    """docstring for World"""
    def __init__(self, width, height, max_link_length, light, soil_height):
        self.width = width
        self.height = height
        self.max_link_length = max_link_length
        self.light = light
        self.soil_height = soil_height

        self.pg = PolygonGrid(width, height)
        self.sh = SegmentHash(width, height, int(max_link_length)*3)
        self.plants = []

        self.__next_cell_id = 0
        self.max_growth = 3

    def __in_bounds(self, p):
        if p.x >= self.width or p.x < 0:
            return False
        if p.y >= self.height or p.y < 0:
            return False
        return True

    def __make_cell(self, p):
        cell = Cell(self.__next_cell_id, p)
        self.__next_cell_id += 1
        return cell

    def add_plant(self, seed_polygon, network, efficiency):
        area = geometry.polygon_area(seed_polygon)
        self.pg.add_polygon(seed_polygon)
        cells = DoubleList()

        for p in seed_polygon:
            cells.append(self.__make_cell(p))

        plant = Plant(network, cells, 0, 0, area, efficiency, True)

        self.plants.append(plant)

        for cell in plant.cells:
            self.sh.segment_add(cell.id, cell.P, cell.prev.P)

    def __single_light_collision(self, P, id_exclude):
        light = P + Vec2D(math.cos(self.light), math.sin(self.light)) * 1000
        for id in self.sh.segment_intersect(light, P):
            if id != id_exclude:
                return True
        return False

    def __calculate_light(self):
        for plant in self.plants:
            plant.light = 0
            for cell in plant.cells:
                cell.light = 0

        for plant in self.plants:
            for cell in plant.cells:

                # Underground cells do not get sunlight.
                if cell.P.y < self.soil_height:
                    continue

                # We cast a ray to the center of every segment.
                P = (cell.P + cell.prev.P)/2

                if not self.__single_light_collision(P, cell.id):
                    Vec2D_light = Vec2D(math.cos(self.light), math.sin(self.light))
                    Vec2D_segment = Vec2D(P.y - cell.prev.P.y, P.x - cell.prev.P.x)
                    angle = Vec2D_light.angle(Vec2D_segment)
                    light = 1 - (abs(math.pi/2.-angle)) / (math.pi/2.)

                    cell.light += light/2
                    cell.prev.light += light/2
                    plant.light += light*.75

    def __calculate_water(self):
        for plant in self.plants:
            plant.water = 0
            for cell in plant.cells:
                if cell.P.y < self.soil_height:
                    cell.water = 1
                    plant.water += 3./self.max_link_length
                else:
                    cell.water = 0

    def __calculate_curvatures(self):
        for plant in self.plants:
            for cell in plant.cells:
                v1 = cell.next.P - cell.P
                v2 = cell.prev.P - cell.P
                cell.curvature = v1.angle_clockwise(v2)

    def __valid_move(self, cell, N, D):
        new_p = cell.P + N*D
        if not self.__in_bounds(new_p):
            return False

        if D > 0:
            if self.pg.in_polygon(new_p):
                return False

            if self.pg.in_polygon((new_p+cell.prev.P)/2):
                return False

            if self.pg.in_polygon((new_p+cell.next.P)/2):
                return False
        else:
            if not self.pg.in_polygon(new_p):
                return False

            if not self.pg.in_polygon((new_p+cell.prev.P)/2):
                return False

            if not self.pg.in_polygon((new_p+cell.next.P)/2):
                return False

        return True

    def __update_positions(self):
        for plant in self.plants:
            for cell in plant.cells:
                cell.P = cell.new_p
                self.sh.segment_move(cell.id, cell.prev.P, cell.P)

    def __split_links(self):
        for plant in self.plants:

            if len(plant.cells) >= MAX_CELLS: # Cant insert any new cells.
                continue

            inserts = []

            for cell in plant.cells:
                if (cell.P - cell.prev.P).norm() > self.max_link_length:
                    inserts.append(cell)

            for cell in inserts:
                new_cell = self.__make_cell((cell.P+cell.prev.P)/2.0)

                plant.cells.insert_before(cell, new_cell)

                self.sh.segment_move(cell.id, cell.P, new_cell.P)
                self.sh.segment_add(new_cell.id, new_cell.P, new_cell.prev.P)

    def calculate(self):
        self.__calculate_light()
        self.__calculate_water()
        self.__calculate_curvatures()

    def fake_output(self, cell):
        if cell.water:
            return [cell.curvature*3]
        else:
            return [cell.curvature]
            # return []

    def __cell_update(self, plant, cell, consumption):
        """
        Map cell status to nerual input in [-1, 1] range.
        """
        inputs = np.zeros((NUM_INPUTS+1))
        inputs[0] = (cell.light*2) - 1
        inputs[1] = (cell.water*2) - 1
        inputs[2] = (cell.curvature/(math.pi)) - 1
        inputs[3] = (consumption*2) - 1
        # inputs[4] = plant.water / plant.light
        inputs[4] = 1 #The last input is always used as bias.

        # if cell.curvature > math.pi:
        #     inputs[2] = - (cell.curvature-math.pi) / math.pi
        # else:
        #     inputs[2] = cell.curvature / math.pi

        plant.network.Flush()
        plant.network.Input(inputs)
        plant.network.ActivateFast()
        output = plant.network.Output()

        assert(len(output) == NUM_OUTPUTS)

        growth = output[0] * self.max_growth
        death = output[1] > 0.5

        if death:
            cell.alive = False
        #     return
        # if output[0] > output[1]:
        #     growth = output[0]
        # else:
        #     growth = - output[1]

        # growth = random.gauss(output[0], output[1]/2)
        # output = [random.random()*5]
        # output = self.fake_output(cell)

        # Handle Outputs.
        N = cell.calculate_normal()
        # D = N * growth

        if self.__valid_move(cell, N, growth):
            cell.new_p = cell.P + N*growth

    def simulation_step(self):

        for plant in self.plants:
            if not plant.alive:
                continue

            # print(plant.alive, len(plant.cells), plant.water, plant.light)
            energy = min(plant.water, plant.light)
            consumption = plant.volume * plant.efficiency / max(1, energy)

            if consumption >= 1.0:
                plant.alive = False
                continue

            # Calculate cell movements and removals.
            for cell in plant.cells:
                self.__cell_update(plant, cell, consumption)

            # for plant in self.plants:
            #     if len(to_kill) == len(plant.cells):
            #         plant.alive = False
            #         continue
            #     for cell in to_kill:
            #         plant.cells.remove(cell)


            for cell in list(plant.cells):
                if cell.alive == False:
                    plant.cells.remove(cell)

            if len(plant.cells) <= 2:
                plant.alive = False
                # continue

        self.__update_positions()

        for plant in self.plants:
            if plant.alive:
                polygon = [c.P for c in plant.cells]
                plant.volume = geometry.polygon_area(polygon)
                self.pg.add_polygon(polygon)

        self.__split_links()
