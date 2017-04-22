from __future__ import division, print_function
import random
from linkedlist import DoubleList
from cell import Cell
import geometry
import math
from modules.segmenthash import SegmentHash
from polygon_grid import PolygonGrid
from recordclass import recordclass
from vector import Vector
import numpy as np
Plant = recordclass('Plant', ['network', 'cells', 'water', 'light', 'volume'])

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

    def add_plant(self, seed_polygon, network):
        area = geometry.polygon_area(seed_polygon)
        self.pg.add_polygon(seed_polygon)
        cells = DoubleList()

        for p in seed_polygon:
            cells.append(self.__make_cell(p))

        plant = Plant(network, cells, water=0, light=0, volume=area)
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
                if cell.P.y < self.soil_height:
                    continue
                P = (cell.P + cell.prev.P)/2
                if self.__single_collision(P, cell.id):
                    cell.light = 0
                else:
                    vector_light = Vector(P.y - self.light.y, P.x - self.light.x)
                    vector_segment = Vector(P.y - cell.prev.P.y, P.x - cell.prev.P.x)
                    angle = vector_light.angle(vector_segment)
                    light = 1 - (abs(math.pi/2.-angle)) / (math.pi/2.)
                    cell.light += light/2
                    cell.prev.light += light/2
                    plant.light += light

    def __calculate_water(self):
        for plant in self.plants:
            plant.water = 0
            for cell in plant.cells:
                if cell.P.y < self.soil_height:
                    cell.water = 1
                    plant.water += 1
                else:
                    cell.water = 0

    def __calculate_curvatures(self):
        for plant in self.plants:
            for cell in plant.cells:
                v1 = cell.next.P - cell.P
                v2 = cell.prev.P - cell.P
                cell.curvature = v1.angle_clockwise(v2)

    def move_cell(self, plant, cell, dist):
        N = cell.calculate_normal()
        new_p = cell.P + N * dist*2

        if not self.__in_bounds(new_p):
            cell.frozen = True
            return False

        if self.pg.in_polygon(new_p):
            return False

        for id in self.sh.segment_intersect(cell.prev.P, new_p):
            if id != cell.id:
                # cell.frozen = True
                return False

        for id in self.sh.segment_intersect(new_p, cell.next.P):
            if id != cell.next.id:
                # cell.frozen = True
                return False

        new_p = cell.P + N * dist
        growth_area = [ cell.prev.P, new_p, cell.next.P ]
        plant.volume += geometry.polygon_area(growth_area)
        self.pg.add_polygon(growth_area)

        self.sh.segment_move(cell.id, p0=cell.P, p1=cell.prev.P)
        self.sh.segment_move(cell.next.id, p0=cell.P, p1=cell.next.P)

        cell.next_P = new_p

    def __update_positions(self):
        for plant in self.plants:
            for cell in plant.cells:
                cell.P = cell.next_P

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

    def simulation_step(self):
        self.__calculate_light()
        self.__calculate_water()
        self.__calculate_curvatures()

        inputs = np.zeros((3))

        for plant in self.plants:
            for cell in plant.cells:
                inputs[0] = cell.light
                inputs[1] = cell.water
                inputs[2] = cell.curvature / math.pi # map [0-1]

                # To replace with netowrk output.
                # out = [cell.light]
                out = [random.random()]

                dist = self.m_delta * out[0]
                self.move_cell(plant, cell, dist)

        self.__update_positions()
        self.__split_links()
