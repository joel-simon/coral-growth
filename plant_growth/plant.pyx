# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True
from __future__ import print_function
from libc.math cimport M_PI, M_PI_2, log, sqrt, fmin, fmax, acos, cos, sin, abs, atan2
from math import isnan
import numpy as np
cimport numpy as np

from random import random

from plant_growth.world cimport World

from plant_growth import constants
from plant_growth cimport geometry

from meshpy.triangle import MeshInfo, build, refine

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
        self.max_i = 0

        self.cell_x = np.zeros(constants.MAX_CELLS)
        self.cell_y = np.zeros(constants.MAX_CELLS)

        self.cell_next_x = np.zeros(constants.MAX_CELLS)
        self.cell_next_y = np.zeros(constants.MAX_CELLS)

        self.cell_norm  = np.zeros((constants.MAX_CELLS, 2))
        self.cell_water = np.zeros(constants.MAX_CELLS)
        self.cell_light = np.zeros(constants.MAX_CELLS)
        self.cell_curvature = np.zeros(constants.MAX_CELLS)

        self.cell_flower = np.zeros(constants.MAX_CELLS, dtype='i')
        self.cell_alive  = np.zeros(constants.MAX_CELLS, dtype='i')

        self.cell_next = np.zeros(constants.MAX_CELLS, dtype='i')
        self.cell_prev = np.zeros(constants.MAX_CELLS, dtype='i')

        self.cell_order = np.zeros(constants.MAX_CELLS, dtype='i')
        self.cell_inputs = [0 for _ in range(constants.NUM_INPUTS+1)]

        self.grid = np.zeros((world.width, world.height), dtype='i')
        self.open_ids = []

    cpdef void update_attributes(self) except *:
        cdef double e_production, e_consumption

        self.polygon = self._make_polygon()
        self.volume = geometry.polygon_area(self.polygon)

        # self._calculate_mesh()
        self._calculate_norms()
        self._calculate_water()
        self._calculate_light()
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
        cdef double growth, x_new, y_new, x_prev, y_prev, x_next, y_next, cell_x, cell_y
        cdef bint flower, smooth
        cdef int i, cid, cid_prev, cid_next

        for i in range(self.n_cells):
            cid = self.cell_order[i]
            assert(self.cell_alive[cid])

            cell_x = self.cell_x[cid]
            cell_y = self.cell_y[cid]

            # Transfer values to cell_input buffer.
            self._cell_input(cid)

            # Compute feed-forward neteork results.
            output = self._output()

            # Three possible output actions.
            growth = output[0] * constants.CELL_MAX_GROWTH
            flower = output[1] > .5
            smooth = 0#output[2] > .5

            # An underground cell may not flower.
            if self.cell_water[cid]:
                self.cell_flower[cid] = False

            elif flower:
                self.cell_flower[cid] = True

            if smooth:# and self.cell_curvature[cid] < 0:
                # Move to 50% between self and neighbors.
                cid_prev = self.cell_prev[cid] # id of cell before
                cid_next = self.cell_next[cid] # id of cell after


                x_prev = self.cell_x[cid_prev]
                y_prev = self.cell_y[cid_prev]
                x_next = self.cell_x[cid_next]
                y_next = self.cell_y[cid_next]


                self.cell_x[cid] = cell_x/2.0 + (x_prev + x_next) / 4.0
                self.cell_y[cid] = cell_y/2.0 + (y_prev + y_next) / 4.0
                

            # Move Cell.
            x_new = cell_x + self.cell_norm[cid, 0] * growth
            y_new = cell_y + self.cell_norm[cid, 1] * growth
            
            if self._valid_growth(cid, x_new, y_new):
                self.cell_next_x[cid] = x_new
                self.cell_next_y[cid] = y_new

    cdef list split_links(self):
        cdef int cid, id_prev
        cdef double dist, x, y, dx, dy

        to_split = []
        inserted = []

        if self.n_cells >= constants.MAX_CELLS:
            return

        for cid in range(self.max_i):
            if self.cell_alive[cid]:
                id_prev = self.cell_prev[cid]

                dx = self.cell_x[cid] - self.cell_x[id_prev]
                dy = self.cell_y[cid] - self.cell_y[id_prev]
                dist = sqrt(dx*dx + dy*dy)

                if dist > constants.MAX_EDGE_LENGTH:
                    to_split.append(cid)

                # elif dist < constants.MIN_EDGE_LENGTH:
                #     self._destroy_cell(cid)

        for cid in to_split:
            id_prev = self.cell_prev[cid]

            if self.n_cells >= constants.MAX_CELLS:
                break

            x = (self.cell_x[cid] + self.cell_x[id_prev]) / 2.0
            y = (self.cell_y[cid] + self.cell_y[id_prev]) / 2.0
            inserted.append(self._create_cell(x, y, before=cid))

        return inserted

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

        if len(self.open_ids):
            cid = self.open_ids.pop()
            self.max_i = max(self.max_i, cid) + 1
        else:
            cid = self.n_cells
            self.max_i = self.n_cells + 1

        if self.cell_head == None:
            self.cell_head = cid

        self.n_cells += 1
        self.cell_alive[cid] = True
        self.cell_x[cid] = x
        self.cell_y[cid] = y

        if before:
            self._insert_before(before, cid)

        else:
            self._append(cid)

        return cid

    # cdef void _destroy_cell(self, int cid):
        # cdef int next_id = self.cell_next[cid]
        # cdef int prev_id = self.cell_prev[cid]

        # self.cell_next[prev_id] = next_id
        # self.cell_prev[next_id] = prev_id

        # if cid == self.cell_head:
        #     self.cell_head = next_id

        # self.cell_alive[cid] = False
        # self.open_ids.append(cid)

        # self.n_cells -= 1

    cdef void _cell_input(self, int cid):
        """ Map cell stats to nerual input in [-1, 1] range.
        """
        self.cell_inputs[0] = (self.cell_light[cid]*2) - 1
        self.cell_inputs[1] = (self.cell_water[cid]*2) - 1
        self.cell_inputs[2] = (self.cell_curvature[cid]/(M_PI)) - 1
        self.cell_inputs[3] = (self.cell_flower[cid]*2) - 1
        self.cell_inputs[4] = (self.consumption*2) - 1
        self.cell_inputs[5] = log(self.water / self.light)

        # self.cell_inputs[6] = sin(self.age)
        # self.cell_inputs[7] = sin(self.age/2.0)
        # self.cell_inputs[6] = (2 * self.age / self.max_age) - 1
        # self.cell_inputs[7] = random()
        self.cell_inputs[6] = 1 # The last input is always used as bias.

    cdef void order_cells(self):
        cdef int cid, i
        cid = self.cell_head

        for i in range(self.n_cells):
            assert(self.cell_alive[cid])
            self.cell_order[i] = cid
            cid = self.cell_next[cid]

    cdef list _output(self):
        self.network.Flush()
        self.network.Input(self.cell_inputs)
        self.network.ActivateFast()
        output = self.network.Output()
        return output

    cdef bint _valid_growth(self, int cid, double x, double y):
        cdef int cid_prev, cid_next
        cdef double x1, y1, x2, y2, angle, x_prev, y_prev, x_next, y_next
        cid_prev = self.cell_prev[cid] # id of cell before
        cid_next = self.cell_next[cid] # id of cell after
        
        x_prev = self.cell_x[cid_prev]
        y_prev = self.cell_y[cid_prev]
        x_next = self.cell_x[cid_next]
        y_next = self.cell_y[cid_next]

        if x < 0 or y < 0:
            return False

        if x >= self.world.width or y >= self.world.height:
            return False

        x1 = x_next - x
        y1 = y_next - y
        x2 = x_prev - x
        y2 = y_prev - y
        angle = geometry.angle_clockwise(x1, y1, x2, y2)

        if angle > constants.MAX_ANGLE:
            return False

        return True

    cdef object _make_polygon(self):
        cdef int i, cid
        polygon = []

        for i in range(self.n_cells):
            cid = self.cell_order[i]
            polygon.append((self.cell_x[cid], self.cell_y[cid]))

        return polygon

    cpdef void _calculate_mesh(self):
        mesh_info = MeshInfo()
        mesh_info.set_points(self.polygon)
        mesh_info.set_facets(round_trip_connect(0, len(self.polygon)-1))
        self.mesh = build(mesh_info)

    cdef void _calculate_norms(self):
        cdef int cid, cid_prev, cid_next
        cdef double x1, y1, x2, y2, norm_x, norm_y

        for cid in range(self.max_i):
            if self.cell_alive[cid]:
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

    cdef void _calculate_light(self) except *:
        cdef int cid
        cdef double angle, light
        self.world.calculate_light(self)

        for cid in range(self.max_i):
            if not self.cell_alive[cid]:
                continue

            if self.cell_light[cid] != 0:
                # angle in radians (will be no values > pi or < 0)
                angle = atan2(self.cell_norm[cid, 1], self.cell_norm[cid, 0])

                # map angle to [0, 1]
                light = 1 - abs(M_PI_2 - angle) / M_PI_2
                self.cell_light[cid] = light

                # Flowers do not contribute light.
                if not self.cell_flower[cid]:
                    self.light += light# * derp

    cdef void _calculate_water(self):
        cdef int cid
        self.water = 0

        for cid in range(self.max_i):
            if self.cell_alive[cid]:
                if self.cell_y[cid] < constants.SOIL_HEIGHT:
                    self.cell_water[cid] = 1
                    self.water += constants.MAX_EDGE_LENGTH*constants.WATER_EFFICIENCY
                else:
                    self.cell_water[cid] = 0

    cdef void _calculate_curvature(self):
        cdef int i, cid, id_prev, id_next
        cdef double x1, y1, x2, y2, angle

        for i in range(self.n_cells):
            cid = self.cell_order[i]
            if self.cell_alive[cid]:
                id_prev = self.cell_prev[cid]
                id_next = self.cell_next[cid]

                x1 = self.cell_x[id_next] - self.cell_x[cid]
                y1 = self.cell_y[id_next] - self.cell_y[cid]
                x2 = self.cell_x[id_prev] - self.cell_x[cid]
                y2 = self.cell_y[id_prev] - self.cell_y[cid]

                angle = geometry.angle_clockwise(x1, y1, x2, y2)
                if isnan(angle):
                    print('nan angle', (round(self.cell_x[cid], 5), round(self.cell_y[cid], 5)), (round(self.cell_x[id_next], 5), round(self.cell_y[id_next], 5)), (round(self.cell_x[id_prev], 5), round(self.cell_y[id_prev], 5)))
                    print(x1, y1, x2, y2)
                self.cell_curvature[cid] = angle

    cdef void _calculate_flowers(self):
        cdef int cid
        cdef bint flower
        cdef double y_cell

        self.num_flowers = 0

        for cid in range(self.max_i):
            if self.cell_alive[cid]:
                flower = self.cell_flower[cid]
                y_cell = self.cell_y[cid]

                if flower:
                    self.num_flowers += 1
                    self.total_flowering += y_cell - self.world.soil_height
