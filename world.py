from __future__ import division, print_function
import random
from linkedlist import DoubleList
from cell import Cell
import geometry
import math
from modules.segmenthash import SegmentHash
from recordclass import recordclass
from vector import Vector

Plant = recordclass('Plant', ['network', 'cells', 'water', 'energy', 'volume'])

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
        cells = DoubleList()

        for p in seed_polygon:
            cells.append(self.__make_cell(p))

        plant = Plant(network, cells, water=0, energy=0, volume=area)
        self.plants.append(plant)

        for cell in plant.cells:
            # print(cell.P)
            self.sh.segment_add(cell.id, cell.P, cell.prev.P)

    def __single_collision(self, P, id_exclude):
        for id in self.sh.segment_intersect(self.light, P):
            if id != id_exclude:
                return True
        return False

    def __calculate_light(self):
        for plant in self.plants:
            for cell in plant.cells:
                cell.light = 0
        for plant in self.plants:
            for cell in plant.cells:
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

    def move_cell(self, plant, cell, new_p):
        if not self.__in_bounds(new_p):
            cell.frozen = True
            return

        for id in self.sh.segment_intersect(cell.prev.P, new_p):
            if id != cell.id:
                cell.frozen = True
                return

        for id in self.sh.segment_intersect(new_p, cell.next.P):
            if id != cell.next.id:
                cell.frozen = True
                return

        growth_area = [ cell.prev.P, new_p, cell.next.P ]
        plant.volume += geometry.polygon_area(growth_area)

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

        for plant in self.plants:
            for cell in plant.cells:
                # if cell.frozen: continue
                if cell.light == 0: continue
                N = cell.calculate_normal()
                # A = cell.calulate_angle()
                step = 2 * cell.light+1*random.random()
                new_P = cell.P + N * step
                self.move_cell(plant, cell, new_P)

        self.__update_positions()
        self.__split_links()
