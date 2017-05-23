# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True

from libc.math cimport M_PI, log, sqrt, fmin, fmax, acos, cos, sin, abs, atan2

import numpy as np
cimport numpy as np

from random import random

from plant_growth.vec2D cimport Vec2D
from plant_growth.world cimport World

from plant_growth import constants
from plant_growth cimport geometry

from meshpy.triangle import MeshInfo, build, refine
from PIL import Image, ImageDraw

def round_trip_connect(start, end):
    return [(i, i+1) for i in range(start, end)] + [(end, start)]

cdef class Plant:
    def __init__(self, world, network, efficiency):
        self.world = world
        self.network = network
        self.efficiency = efficiency

        self.energy = 0
        self.volume = 0
        self.water = 0
        self.light = 0
        self.alive = True

        self.num_flowers = 0
        self.total_flowering = 0
        self.consumption = 0
        self.age = 0
        self.max_age = float(constants.SIMULATION_STEPS)
        
        self.n_cells = 0

        self.cell_x = np.empty(constants.MAX_CELLS)
        self.cell_y = np.empty(constants.MAX_CELLS)

        self.cell_norm = np.empty((constants.MAX_CELLS, 2))
        self.cell_water = np.zeros(constants.MAX_CELLS)
        self.cell_light = np.zeros(constants.MAX_CELLS)
        self.cell_curvature = np.zeros(constants.MAX_CELLS)
        self.cell_flower = np.zeros(constants.MAX_CELLS, dtype='i')

        self.cell_next = np.zeros(constants.MAX_CELLS, dtype='i')
        self.cell_prev = np.zeros(constants.MAX_CELLS, dtype='i')

        self.ordered_cell = np.zeros(constants.MAX_CELLS, dtype='i')
        self.cell_inputs = [0 for _ in range(constants.NUM_INPUTS+1)]

        self.grid = np.zeros((world.width, world.height), dtype='i')

    cpdef void update_attributes(self):
        cdef double e_production, e_consumption

        self.polygon = self._make_polygon()
        self.volume = geometry.polygon_area(self.polygon)

        # self._calculate_mesh()
        self._calculate_norms()
        self._calculate_collision_grid()
        self._calculate_light()
        self._calculate_water()
        self._calculate_curvature()
        self._calculate_flowers()

        e_production = min(self.water, self.light)
        e_consumption = (self.volume / self.efficiency) + (constants.FLOWER_COST * self.num_flowers)
        self.energy = e_production - e_consumption

        if e_production > 0:
            self.consumption =  e_consumption / e_production
        else:
            self.consumption = 0

        self.age += 1

        if self.energy <= 0.0:
            self.alive = False

        if self.n_cells >= constants.MAX_CELLS:
            self.alive = False

    cpdef void grow(self):
        cdef double growth, x_cell, y_cell, x_prev, y_prev, x_next, y_next
        cdef bint flower, death
        cdef double[:] inputs
        cdef int cid, cid_prev, cid_next

        for cid in range(self.n_cells):
            cid_prev = self.cell_prev[cid] # id of cell before
            cid_next = self.cell_next[cid] # id of cell after

            x_cell = self.cell_x[cid]
            y_cell = self.cell_y[cid]
            x_prev = self.cell_x[cid_prev]
            y_prev = self.cell_y[cid_prev]
            x_next = self.cell_x[cid_next]
            y_next = self.cell_y[cid_next]

            # Transfer values to cell_input buffer.
            self._cell_input(cid)

            # Compute feed-forward neteork results.
            output = self._output()

            # Three possible output actions.
            growth = output[0] * constants.CELL_MAX_GROWTH
            flower = output[1] > .5
            death  = output[2] > .5

            # An underground cell may not flower.
            if self.cell_water[cid]:
                self.cell_flower[cid] = False
                flower = False

            if death:
                self.cell_x[cid] = (x_prev + x_next) / 2.0
                self.cell_y[cid] = (y_prev + y_next) / 2.0

            if not self.cell_water[cid] and flower:
                if self.energy >= constants.FLOWER_COST:
                    self.energy -= constants.FLOWER_COST
                    self.cell_flower[cid] = True

            x_test = x_cell + self.cell_norm[cid, 0] * 3 * growth
            y_test = y_cell + self.cell_norm[cid, 1] * 3 * growth

            if self._valid_growth(x_test, y_test, x_prev, y_prev, x_next, y_next):
                self.cell_x[cid] += self.cell_norm[cid, 0] * growth
                self.cell_y[cid] += self.cell_norm[cid, 1] * growth

        self._split_links()
        self._order_cells()

    cpdef void create_circle(self, double x, double y, double r, int n):
        cdef int i
        cdef double a, xx, yy
        for i in range(n):
            a = 2 * i * M_PI / n
            xx = x + cos(a) * r
            yy = y + sin(a) * r
            self._create_cell(xx, yy)

    cdef void _insert_before(self, int node, int new_node):
        """ Called by _create_cell
        """
        cdef int prev_node = self.cell_prev[node]
        self.cell_next[prev_node] = new_node
        self.cell_prev[new_node] = prev_node
        self.cell_next[new_node] = node
        self.cell_prev[node] = new_node

        if node == self.cell_head:
            self.cell_head = new_node

    cdef void _append(self, int new_node):
        """ Called by _create_cell
        """
        if self.cell_head is None:
            self.cell_head = new_node
            self.cell_tail = new_node
        else:
            self.cell_prev[new_node] = self.cell_tail
            self.cell_next[new_node] = self.cell_head
            self.cell_next[self.cell_tail] = new_node
            self.cell_tail = new_node
            self.cell_prev[self.cell_head] = self.cell_tail

    cdef int _create_cell(self, double x, double y, before=None):
        cdef int cid
        assert self.n_cells <= constants.MAX_CELLS

        cid = self.n_cells
        self.n_cells += 1
        self.cell_x[cid] = x
        self.cell_y[cid] = y

        if before:
            self._insert_before(before, cid)

        else:
            self._append(cid)

        return cid

    cdef void _cell_input(self, int cid):
        """ Map cell stats to nerual input in [-1, 1] range.
        """
        self.cell_inputs[0] = (self.cell_light[cid]*2) - 1
        self.cell_inputs[1] = (self.cell_water[cid]*2) - 1
        self.cell_inputs[2] = (self.cell_curvature[cid]/(M_PI)) - 1
        self.cell_inputs[3] = (self.consumption*2) - 1
        self.cell_inputs[4] = (self.cell_flower[cid]*2) - 1
        self.cell_inputs[5] = log(self.water / self.light)
        self.cell_inputs[6] = (2 * self.age / self.max_age) - 1
        self.cell_inputs[7] = random()
        self.cell_inputs[8] = 1 # The last input is always used as bias.

    cdef void _order_cells(self):
        cdef int cid, i
        cid = self.cell_head
        for i in range(self.n_cells):
            self.ordered_cell[i] = cid
            cid = self.cell_next[cid]

    cdef list _output(self):
        self.network.Flush()
        self.network.Input(self.cell_inputs)
        self.network.ActivateFast()
        output = self.network.Output()
        return output

    cdef bint _valid_growth(self, double x_test, double y_test, double x_prev, double y_prev, double x_next, double y_next):
        cdef int x, y
        cdef double x1, y1, x2, y2, angle

        if x_test < 0 or y_test < 0:
            return False

        if x_test >= self.world.width or y_test >= self.world.height:
            return False

        x1 = x_next - x_test
        y1 = y_next - y_test
        x2 = x_prev - x_test
        y2 = y_prev - y_test
        angle = geometry.angle_clockwise(x1, y1, x2, y2)

        if angle > constants.MAX_ANGLE:
            return False

        if self.grid[<int>x_test, <int>y_test]:
            return False

        x = <int>((x_test + x_prev) / 2.)
        y = <int>((y_test + y_prev) / 2.)
        if self.grid[x, y]:
            return False

        x = <int>((x_test + x_next) / 2.)
        y = <int>((y_test + y_next) / 2.)
        if self.grid[x, y]:
            return False

        return True

    cdef object _make_polygon(self):
        cdef int i, cid
        polygon = []

        for i in range(self.n_cells):
            cid = self.ordered_cell[i]
            polygon.append((self.cell_x[cid], self.cell_y[cid]))

        return polygon

    cdef void _calculate_mesh(self):
        mesh_info = MeshInfo()
        mesh_info.set_points(self.polygon)
        mesh_info.set_facets(round_trip_connect(0, len(self.polygon)-1))
        self.mesh = build(mesh_info)

    cdef void _calculate_norms(self):
        cdef int cid, cid_prev, cid_next
        cdef double x1, y1, x2, y2, norm_x, norm_y

        for cid in range(self.n_cells):
            cid_prev = self.cell_prev[cid]
            cid_next = self.cell_next[cid]

            x1 = self.cell_x[cid_prev] - self.cell_x[cid]
            y1 = self.cell_y[cid_prev] - self.cell_y[cid]

            x2 = self.cell_x[cid_next] - self.cell_x[cid]
            y2 = self.cell_y[cid_next] - self.cell_y[cid]

            norm_x = y2 - y1
            norm_y = -(x2 - x1)

            d = sqrt(norm_x*norm_x + norm_y*norm_y)

            if d == 0:
                norm_x = 0
                norm_y = 0
            else:
                norm_x /= d
                norm_y /= d

            self.cell_norm[cid, 0] = norm_x
            self.cell_norm[cid, 1] = norm_y

    cdef void _split_links(self):
        cdef int cid, id_prev
        cdef double dist, x, y, dx, dy

        inserts = []

        if self.n_cells >= constants.MAX_CELLS:
            return

        for cid in range(self.n_cells):
            id_prev = self.cell_prev[cid]

            dx = self.cell_x[cid] - self.cell_x[id_prev]
            dy = self.cell_y[cid] - self.cell_y[id_prev]
            dist = sqrt(dx*dx + dy*dy)
            # dist = v_cell.sub(v_prev).norm()

            if dist > constants.MAX_EDGE_LENGTH:
                inserts.append(cid)

        for cid in inserts:
            id_prev = self.cell_prev[cid]

            if self.n_cells >= constants.MAX_CELLS:
                break

            x = (self.cell_x[cid] + self.cell_x[id_prev]) / 2.0
            y = (self.cell_y[cid] + self.cell_y[id_prev]) / 2.0
            self._create_cell(x, y, before=cid)

    cdef void _calculate_collision_grid(self):
        img = Image.new('L', (self.world.width, self.world.height), 0)
        ImageDraw.Draw(img).polygon(self.polygon, outline=0, fill=1)
        np.copyto(np.asarray(self.grid).T, img)
        # self.grid = np.asarray(img, dtype=np.uint8).T

    cdef void _calculate_light(self):
        cdef int cid, id_prev
        cdef double light, x_cell, y_cell, x_prev, y_prev
        cdef Vec2D P, v_light, v_segment
        cdef double derp = constants.MAX_EDGE_LENGTH*constants.LIGHT_EFFICIENCY
        cdef double angle

        cdef double ax = cos(self.world.light - (M_PI / 2))
        cdef double ay = sin(self.world.light - (M_PI / 2))

        self.light = 0.0

        for cid in range(self.n_cells):
            self.cell_light[cid] = 0

        for cid in range(self.n_cells):
            id_prev = self.cell_prev[cid]
            x_cell = self.cell_x[cid]
            y_cell = self.cell_y[cid]
            x_prev = self.cell_x[id_prev]
            y_prev = self.cell_y[id_prev]

            x_center = (x_cell + x_prev) / 2.0
            y_center = (y_cell + y_prev) / 2.0


            # Underground cells do not recieve sunlight.
            if y_cell <= constants.SOIL_HEIGHT:
                self.cell_light[cid] = 0.0

            # Cast a ray to the center of every segment.
            elif not self.world.single_light_collision(self, x_center, y_center, cid):
                
                # angle from 0 to 2pi
                angle = geometry.angle_clockwise(x_prev - x_cell, y_prev - y_cell, ax, ay)
                
                # map angle to [0, 1]
                light = abs(angle-M_PI) / M_PI

                # TODO - figure out why this is needed.
                light = (light -.5) * 2

                # self.cell_light[cid] = light

                self.cell_light[cid] += light / 2.0
                self.cell_light[id_prev] += light / 2.0
                
                # Flowers do not contribute light.
                if not self.cell_flower[cid]:
                    self.light += light * derp

    cdef void _calculate_water(self):
        cdef int cid
        # cdef Vec2D v_cell
        self.water = 0

        for cid in range(self.n_cells):
            if self.cell_y[cid] < constants.SOIL_HEIGHT:
                self.cell_water[cid] = 1
                self.water += constants.MAX_EDGE_LENGTH*constants.WATER_EFFICIENCY
            else:
                self.cell_water[cid] = 0

    cdef void _calculate_curvature(self):
        cdef int cid, id_prev, id_next
        cdef double x1, y1, x2, y2, angle

        for cid in range(self.n_cells):
            id_prev = self.cell_prev[cid]
            id_next = self.cell_next[cid]

            x1 = self.cell_x[id_next] - self.cell_x[cid]
            y1 = self.cell_y[id_next] - self.cell_y[cid]
            x2 = self.cell_x[id_prev] - self.cell_x[cid]
            y2 = self.cell_y[id_prev] - self.cell_y[cid]

            angle = geometry.angle_clockwise(x1, y1, x2, y2)

    cdef void _calculate_flowers(self):
        cdef int cid
        cdef bint flower
        cdef double y_cell

        self.num_flowers = 0

        for cid in range(self.n_cells):
            flower = self.cell_flower[cid]
            y_cell = self.cell_y[cid]

            if flower:
                self.num_flowers += 1
                self.total_flowering += y_cell - self.world.soil_height
