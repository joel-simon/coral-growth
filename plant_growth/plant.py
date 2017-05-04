import math

from plant_growth.vec2D import Vec2D
from plant_growth import linkedlist, geometry, constants
from plant_growth.cell import Cell

from PIL import Image, ImageDraw

class Plant:
    def __init__(self, world, network, polygon, efficiency):
        self.world = world
        self.network = network
        self.polygon = polygon
        self.efficiency = efficiency

        self.cells = linkedlist.DoubleList()
        self.energy = 0
        self.volume = 0
        self.water = 0
        self.light = 0
        self.alive = True
        self.grid = None
        self.consumption = 0

        for p in polygon:
            self.cells.append(self.world.make_cell(p))

    def split_links(self):
        inserts = []

        for cell in self.cells:
            if (cell.P - cell.prev.P).norm() > constants.MAX_EDGE_LENGTH:
                inserts.append(cell)

        for cell in inserts:
            new_cell = self.world.make_cell((cell.P+cell.prev.P)/2.0)
            self.cells.insert_before(cell, new_cell)

    def update_attributes(self):
        if self.alive:
            self.polygon = [(c.P.x, c.P.y) for c in self.cells]

            self.__calculate_collision_grid()
            self.__calculate_light()
            self.__calculate_water()
            self.__calculate_curvature()

            self.volume = geometry.polygon_area(self.polygon)
            self.energy = min(self.water, self.light) + 1
            self.consumption = self.volume  / (self.energy * self.efficiency)

            if self.consumption >= 1:
                self.alive = False

    def __calculate_collision_grid(self):
        img = Image.new('L', (self.world.width, self.world.height), 0)
        ImageDraw.Draw(img).polygon(self.polygon, outline=0, fill=1)
        self.grid = img.load()

    def __calculate_light(self):
        self.light = 0

        for cell in self.cells:
            P = (cell.P + cell.prev.P)/2

            # Underground cells do not get sunlight.
            if cell.P.y < constants.SOIL_HEIGHT:
                cell.light = 0

            # Cast a ray to the center of every segment.
            elif not self.world.single_light_collision(P, cell.id):
                Vec2D_light = Vec2D(math.cos(self.light), math.sin(self.light))
                Vec2D_segment = Vec2D(P.y - cell.prev.P.y, P.x - cell.prev.P.x)
                angle = Vec2D_light.angle(Vec2D_segment)
                light = 1 - (abs(angle - math.pi/2.)) / (math.pi/2.)

                cell.light += light/2
                cell.prev.light += light/2
                self.light += light*constants.MAX_EDGE_LENGTH*constants.LIGHT_EFFICIENCY
            else:
                cell.light = 0

    def __calculate_water(self):
        self.water = 0
        for cell in self.cells:
            if cell.P.y < constants.SOIL_HEIGHT:
                cell.water = 1
                self.water += constants.MAX_EDGE_LENGTH*constants.WATER_EFFICIENCY
            else:
                cell.water = 0

    def __calculate_curvature(self):
        for cell in self.cells:
            v1 = cell.next.P - cell.P
            v2 = cell.prev.P - cell.P
            cell.curvature = v1.angle_clockwise(v2)
