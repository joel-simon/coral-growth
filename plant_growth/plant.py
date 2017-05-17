import math

from plant_growth.vec2D import Vec2D
from plant_growth import linkedlist, geometry, constants
from plant_growth.cell import Cell
from plant_growth.mesh import Mesh, Vert

from meshpy.triangle import MeshInfo, build, refine

from PIL import Image, ImageDraw

from recordclass import recordclass

def round_trip_connect(start, end):
    return [(i, i+1) for i in range(start, end)] + [(end, start)]

class Plant:
    def __init__(self, world, network, efficiency):
        self.world = world
        self.network = network
        self.polygon = None
        self.efficiency = efficiency

        self.energy = 0
        self.volume = 0
        self.water = 0
        self.light = 0
        self.alive = True
        self.grid = None
        self.flower_area = 0
        self.total_flowering = 0
        self.consumption = 0
        self.age = 0

        self.cells = linkedlist.DoubleList()
        self.mesh = None
        self.__next_cell_id = 0

    def __create_cell(self, x, y):
        cell = Cell(self.__next_cell_id, x, y)
        self.__next_cell_id += 1
        return cell

    def __cell_input(self, cell, inputs):
        """ Map cell stats to nerual input in [-1, 1] range.
        """
        inputs[0] = (cell.light*2) - 1
        inputs[1] = (cell.water*2) - 1
        inputs[2] = (cell.curvature/(math.pi)) - 1
        inputs[3] = (self.consumption*2) - 1
        inputs[4] = (cell.flower*2) - 1
        # self.cell_inputs[4] = plant.water / plant.light
        inputs[-1] = 1 # The last input is always used as bias.

    def grow(self):
        inputs = [0] * (constants.NUM_INPUTS+1)

        for cell in self.cells:
            self.__cell_input(cell, inputs)

            self.network.Flush()
            self.network.Input(inputs)
            self.network.ActivateFast()
            output = self.network.Output()

            growth = output[0] * constants.CELL_MAX_GROWTH

            if cell.water: # a cell with flower may move underground.
                cell.flower = False

            if output[2] > .5:
                cell.vector = (cell.prev.vector + cell.next.vector) / 2

            if not cell.water and (output[1] > .5):
                if self.energy >= constants.FLOWER_COST:
                    self.energy -= constants.FLOWER_COST
                    cell.flower = True

            # Crate normal Vector.
            Sa = cell.prev.vector - cell.vector
            Sb = cell.next.vector - cell.vector
            N = Sa.cross(Sb).normed()

            if self.__valid_growth(cell, cell.vector + ( N * 3 * growth )):
                cell.vector = cell.vector + ( N * growth )

    def __valid_growth(self, cell, vector):

        if not self.world.in_bounds(vector.x, vector.y):
            return False

        v1 = cell.next.vector - vector
        v2 = cell.prev.vector - vector

        curvature = v1.angle_clockwise(v2)

        if curvature > constants.MAX_ANGLE:
            return False

        if self.grid[ vector.x, vector.y ]:
            return False

        x, y = (vector + cell.prev.vector)/2
        if self.grid[x, y]:
            return False

        x, y = (vector + cell.next.vector)/2
        if self.grid[x, y]:
            return False

        return True

    def update_attributes(self):
        self.__split_links()

        self.polygon = [(c.vector.x, c.vector.y) for c in self.cells]
        self.volume = geometry.polygon_area(self.polygon)

        self.__calculate_mesh()
        self.__calculate_collision_grid()
        self.__calculate_light()
        self.__calculate_water()
        self.__calculate_curvature()
        self.__calculate_flowers()

        e_production = min(self.water, self.light)
        e_consumption = (self.volume / self.efficiency) + (constants.FLOWER_COST * self.num_flowers)
        self.energy = e_production - e_consumption

        if e_production > 0:
            self.consumption =  e_consumption / e_production
        else:
            self.consumption = 0

        self.age += 1

        if self.energy < 0.0:
            self.alive = False

    def create_circle(self, x, y, r, n):
        for i in range(n):
            a = 2 * i * math.pi / n
            xx = x + math.cos(a) * r
            yy = y + math.sin(a) * r
            self.cells.append(self.__create_cell(xx, yy))

    def __calculate_mesh(self):
        mesh_info = MeshInfo()
        mesh_info.set_points(self.polygon)
        mesh_info.set_facets(round_trip_connect(0, len(self.polygon)-1))
        self.mesh = build(mesh_info)

    def __split_links(self):
        inserts = []
        removes = []

        for cell in self.cells:
            next_cell = cell.prev
            dist = (cell.vector - next_cell.vector).norm()
            if dist > constants.MAX_EDGE_LENGTH:
                inserts.append(cell)

        for cell in inserts:
            x, y = (cell.vector + cell.prev.vector) / 2
            new_cell = self.__create_cell(x, y)
            self.cells.insert_before(cell, new_cell)

    def __calculate_collision_grid(self):
        img = Image.new('L', (self.world.width, self.world.height), 0)
        ImageDraw.Draw(img).polygon(self.polygon, outline=0, fill=1)
        self.grid = img.load()

    def __calculate_light(self):
        self.light = 0

        for cell in self.cells:
            P = (cell.vector + cell.prev.vector)/2

            if cell.flower:
                cell.light = 0

            # Underground out_verts do not get sunlight.
            elif cell.vector.y <= constants.SOIL_HEIGHT:
                cell.light = 0

            # Cast a ray to the center of every segment.
            elif not self.world.single_light_collision(P, cell.id):
                Vec2D_light = Vec2D(math.cos(self.light), math.sin(self.light))
                Vec2D_segment = Vec2D(P.y - cell.prev.vector.y, P.x - cell.prev.vector.x)
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
            if cell.vector.y < constants.SOIL_HEIGHT:
                cell.water = 1
                self.water += constants.MAX_EDGE_LENGTH*constants.WATER_EFFICIENCY
            else:
                cell.water = 0

    def __calculate_curvature(self):
        for cell in self.cells:
            v1 = cell.next.vector - cell.vector
            v2 = cell.prev.vector - cell.vector
            cell.curvature = v1.angle_clockwise(v2)

    def __calculate_flowers(self):
        self.num_flowers = sum(1 for c in self.cells if c.flower)
        self.total_flowering = sum(c.vector.y-constants.SOIL_HEIGHT for c in self.cells if c.flower)
