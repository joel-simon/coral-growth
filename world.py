from __future__ import division, print_function
import random
from linkedlist import DoubleList
from cell import Cell
import geometry
import math
from modules.segmenthash import SegmentHash
from image_grid import PolygonGrid
from recordclass import recordclass
from vector import Vector
import numpy as np

Plant = recordclass('Plant', [
    'network', 'cells', 'water', 'light', 'volume', 'efficiency', 'alive'
])

def round_trip_connect(start, end):
    result = []
    for i in range(start, end):
        result.append((i, i+1))
        result.append((end, start))
    return result

class World(object):
    """docstring for World"""
    def __init__(self, width, height, max_link_length, light, soil_height):
        self.width = width
        self.height = height
        self.max_link_length = max_link_length
        self.light = light
        self.soil_height = soil_height

        #
        self.m_delta = 2.0
        #
        self.pg = PolygonGrid(width, height)
        self.sh = SegmentHash(width, height, int(max_link_length))
        self.plants = []
        self.steps = 0

        self.__next_cell_id = 0

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

    def __single_collision(self, P, id_exclude):
        for id in self.sh.segment_intersect(self.light, P):
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

                P = cell.P#(cell.P + cell.prev.P)/2

                if self.__single_collision(P, cell.id):
                    cell.light = 0

                else:
                    vector_light = Vector(P.y - self.light.y, P.x - self.light.x)
                    vector_segment = Vector(P.y - cell.prev.P.y, P.x - cell.prev.P.x)
                    angle = vector_light.angle(vector_segment)
                    light = 1 - (abs(math.pi/2.-angle)) / (math.pi/2.)
                    cell.light += light
                    # cell.prev.light += light/2
                    plant.light += light
                    # print(light/2)

    def __calculate_water(self):
        for plant in self.plants:
            plant.water = 0
            for cell in plant.cells:
                if cell.P.y < self.soil_height:
                    cell.water = 1
                    plant.water += 10./self.max_link_length
                else:
                    cell.water = 0

    def __calculate_curvatures(self):
        for plant in self.plants:
            for cell in plant.cells:
                v1 = cell.next.P - cell.P
                v2 = cell.prev.P - cell.P
                cell.curvature = v1.angle_clockwise(v2)

    # def move_cell(self, plant, cell, dist):
    #     """
    #     If this is not a valid move, return 0 (False)
    #     Otherwise, new cell.new_P and return the area of the increase
    #     """
    def __valid_move(self, cell, new_p):
        if not self.__in_bounds(new_p):
            return False

        # if self.pg.line_intersection(new_p, cell.prev.P):
        #     return False

        # if self.pg.line_intersection(new_p, cell.next.P):
        #     return False

        if self.pg.in_polygon(new_p):
            return False

        return True

    def __update_positions(self):
        for plant in self.plants:
            for cell in plant.cells:
                cell.P = cell.new_p
                self.sh.segment_move(cell.id, cell.prev.P, cell.P)

    def __split_links(self):
        for plant in self.plants:
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

    def simulation_step(self):
        inputs = np.zeros((5))

        for plant in self.plants:
            if not plant.alive:
                continue

            energy = 10 * min(plant.water, plant.light)
            consumption = plant.volume * plant.efficiency / energy
            # print(plant.water / plant.light)
            if consumption > 1.0:
                plant.alive = False
                continue

            network = plant.network

            for cell in plant.cells:
                inputs[0] = cell.light
                inputs[1] = cell.water
                inputs[2] = (cell.curvature/(math.pi)) - 1
                inputs[3] = consumption
                inputs[4] = plant.water / plant.light


                # if cell.curvature > math.pi:
                #     inputs[2] = - (cell.curvature-math.pi) / math.pi
                # else:
                #     inputs[2] = cell.curvature / math.pi

                network.Flush()
                network.Input(inputs)
                network.ActivateFast()
                output = network.Output()
                # output = [random.random()*5]
                # output = self.fake_output(cell)

                # Handle Outputs.
                N = cell.calculate_normal()
                P2 = cell.P + N * output[0]

                if self.__valid_move(cell, P2):
                    cell.new_p = P2

            self.__update_positions()

            polygon = [c.P for c in plant.cells]
            plant.volume = geometry.polygon_area(polygon)
            for plant in self.plants:
                self.pg.add_polygon(polygon)

            self.__split_links()
