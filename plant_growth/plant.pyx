# cython: boundscheck=True
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True
from __future__ import print_function
from libc.math cimport M_PI, M_PI_2, log, sqrt, fmin, fmax, acos, cos, sin, abs, atan2
from math import isnan
from random import random, shuffle

import numpy as np
cimport numpy as np
from meshpy.triangle import MeshInfo, build, refine

from plant_growth.world cimport World
from plant_growth import constants
from plant_growth cimport geometry

cdef class Plant:
    def __init__(self, world, network, efficiency):
        self.world = world
        self.network = network
        self.efficiency = efficiency

        self.volume = 0
        self.alive = True
        self.gametes = 0
        self.age = 0
        self.n_cells = 0
        self.max_cells = constants.MAX_CELLS
        self.energy = 0

        # Constants
        self.cell_min_energy  = constants.cell_min_energy
        self.cell_growth_energy_usage = constants.cell_growth_energy_usage
        self.cell_max_growth = constants.CELL_MAX_GROWTH

        # Cell data
        self.cell_x = np.zeros(self.max_cells)
        self.cell_y = np.zeros(self.max_cells)
        self.cell_next_x = np.zeros(self.max_cells)
        self.cell_next_y = np.zeros(self.max_cells)
        self.cell_norm  = np.zeros((self.max_cells, 2))
        self.cell_light = np.zeros(self.max_cells)
        self.cell_curvature = np.zeros(self.max_cells)
        # self.cell_energy = np.zeros(self.max_cells)
        self.cell_type = np.zeros(self.max_cells, dtype='i')
        self.cell_alive  = np.zeros(self.max_cells, dtype='i')
        self.cell_next = np.zeros(self.max_cells, dtype='i')
        self.cell_prev = np.zeros(self.max_cells, dtype='i')
        self.cell_order = np.zeros(self.max_cells, dtype='i')
        self.cell_inputs = [0 for _ in range(constants.NUM_INPUTS+1)]

        # self.mesh = create_mesh(self)

    cdef void grow(self) except *:
        """ Calculate the changes to plant by neural network.
            Set cell_next_x and cell_next_y values while decreasing cell_light.
        """
        cdef int i, cid
        cdef list output
        cdef double energy_demand, energy_supply, energy_spent, growth, new_x, new_y
        cdef double next_area, area_change, growth_scalar, energy_usage

        cdef bint verbose = False

        cdef double[:] growth_amounts = np.zeros(self.max_cells)

        cdef double mesh

        for i in range(self.n_cells):
            cid = self.cell_order[i]

            if not self.cell_alive[cid]:
                continue

            # Transfer values to cell_input buffer.
            self._cell_input(cid)

            # Compute feed-forward network results.
            output = self._output()

            # death = output[1] > .5

            if output[2] > output[3]:
                if output[2] > .5:
                    self.cell_type[cid] = 1
            else:
                if output[3] > .5:
                    self.cell_type[cid] = 2


            growth = output[0] * self.cell_max_growth
            growth_amounts[cid] = growth

            # if death:
            #     self.cell_alive[cid] = 0
            #     self.cell_next_x[cid] = self.cell_x[cid]
            #     self.cell_next_y[cid] = self.cell_y[cid]
            #     continue

            # energy_demand = output[0] * self.cell_growth_energy_usage
            # energy_supply = max(0, self.cell_energy[cid] - self.cell_min_energy)
            # energy_spent = min(energy_demand, energy_supply)
            # growth = (energy_spent / self.cell_growth_energy_usage) * self.cell_max_growth

            # print(output[0], energy_demand, energy_supply)
            # print(output[0], energy_supply, energy_spent, growth, self.cell_energy[cid])

            # assert growth >= 0

            # self.cell_energy[cid] -= energy_spent

            # # Move Cell.
            new_x = self.cell_x[cid] + self.cell_norm[cid, 0] * growth
            new_y = self.cell_y[cid] + self.cell_norm[cid, 1] * growth

            if self._valid_growth(cid, new_x, new_y):
                self.cell_next_x[cid] = new_x
                self.cell_next_y[cid] = new_y
            else:
                growth_amounts[cid] = 0
                self.cell_next_x[cid] = self.cell_x[cid]
                self.cell_next_y[cid] = self.cell_y[cid]

        # Calculate area of growth to see how much energy is needed.
        cdef list next_polygon = []
        for i in range(self.n_cells):
            cid = self.cell_order[i]
            next_polygon.append((self.cell_next_x[cid], self.cell_next_y[cid]))

        next_area = geometry.polygon_area(next_polygon)
        area_change = next_area - self.volume
        energy_demand = area_change * self.cell_growth_energy_usage

        assert area_change >= 0

        if energy_demand == 0:
            growth_scalar = 0
        else:
            growth_scalar = min(1, self.energy / energy_demand)

        energy_usage = energy_demand * growth_scalar
        energy_usage = min(energy_usage, self.energy) # This is just to deal with rounding errors.

        if verbose:
            print('Area Change:', area_change)
            print('Energy Demand:', energy_demand)
            print('Growth Scalar:', growth_scalar)
            print('Energy', self.energy)
            print('Energy usage', energy_usage)
            print()

        for i in range(self.n_cells):
            cid = self.cell_order[i]
            growth = growth_amounts[cid] * growth_scalar
            new_x = self.cell_x[cid] + self.cell_norm[cid, 0] * growth
            new_y = self.cell_y[cid] + self.cell_norm[cid, 1] * growth
            self.cell_next_x[cid] = new_x
            self.cell_next_y[cid] = new_y

        self.energy -= energy_usage
        assert self.energy >= 0
        self.gametes += self.energy

    cdef void update_attributes(self) except *:
        """ In each simulation step, grow is called on all plants. then update_attributes
            Grow has used upp all spare energy.
        """
        cdef int i, cid
        cdef double spare_energy
        # print('update attributes')
        self._make_polygon()
        self.volume = geometry.polygon_area(self.polygon) # Call after _make_polygon()
        # self._calculate_mesh()
        self._calculate_norms()
        self._calculate_light() # Call after _calculate_norms()
        self._calculate_curvature()
        self.energy = sum(self.cell_light[:self.n_cells]) # Call after _calculate_light()
        self.age += 1

        # For now the energy is simply the light value.
        # for i in range(self.n_cells):
        #     cid = self.cell_order[i]
        #     self.cell_energy[cid] = self.cell_light[cid]

        # spare_energy = self._calculate_energy_transfer()

        # for i in range(self.n_cells):
        #     cid = self.cell_order[i]
        #     if self.cell_y[cid] < constants.SOIL_HEIGHT:
        #         self.cell_alive[cid] = False

    cdef double _calculate_energy_transfer(self) except *:
        """
        """
        cdef int i, cid
        cdef double transfer
        cdef double plant_spare_energy = 0
        cdef double n_needy_cells = 0

        for i in range(self.n_cells):
            cid = self.cell_order[i]
            if not self.cell_alive[cid]:
                continue
            if self.cell_energy[cid] < self.cell_min_energy:
                n_needy_cells += 1
            else:
                plant_spare_energy += self.cell_energy[cid] - self.cell_min_energy

        # print('%i needy cells and %f spare'%(n_needy_cells, plant_spare_energy))
        cdef list cid_list = [self.cell_order[i] for i in range(self.n_cells)]
        shuffle(cid_list)

        for i in range(self.n_cells):
            # cid = self.cell_order[i]
            cid = cid_list[i]

            if not self.cell_alive[cid]:
                continue

            if self.cell_energy[cid] < self.cell_min_energy:
                transfer = self.cell_min_energy - self.cell_energy[cid]

                if transfer <= plant_spare_energy:
                    self.cell_energy[cid] += transfer
                    plant_spare_energy -= transfer
                else:
                    self.cell_alive[cid] = False

        return plant_spare_energy

    cdef list split_links(self):
        cdef int i, cid, id_prev
        cdef double dist, x, y, dx, dy

        to_split = []
        to_remove = []
        inserted = []

        if self.n_cells >= constants.MAX_CELLS:
            return []

        for i in range(self.n_cells):
            cid = self.cell_order[i]

            if not self.cell_alive[cid]:
                continue

            id_prev = self.cell_prev[cid]

            dx = self.cell_x[cid] - self.cell_x[id_prev]
            dy = self.cell_y[cid] - self.cell_y[id_prev]
            dist = sqrt(dx*dx + dy*dy)

            if dist > constants.MAX_EDGE_LENGTH:
                to_split.append(cid)

        for cid in to_split:
            id_prev = self.cell_prev[cid]

            if self.n_cells >= constants.MAX_CELLS:
                break

            x = (self.cell_x[cid] + self.cell_x[id_prev]) / 2.0
            y = (self.cell_y[cid] + self.cell_y[id_prev]) / 2.0
            inserted.append(self.create_cell(x, y, insert_before=cid))

        return inserted

    cpdef void create_circle(self, double x, double y, double r, int n):
        cdef int i
        cdef double a, xx, yy
        for i in range(n):
            a = 2 * i * M_PI / n
            xx = x + cos(a) * r
            yy = y + sin(a) * r
            self.create_cell(xx, yy)

    cdef void _insert_before(self, int node, int new_node):
        """ Called by create_cell
        """
        cdef int prev_node = self.cell_prev[node]
        self.cell_next[prev_node] = new_node
        self.cell_prev[new_node] = prev_node
        self.cell_next[new_node] = node
        self.cell_prev[node] = new_node

        if node == self.cell_head:
            self.cell_head = new_node

    cdef void _append(self, int new_node):
        """ Called by create_cell
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

    cpdef int create_cell(self, double x, double y, insert_before=None):
        cdef int cid
        assert self.n_cells <= constants.MAX_CELLS
        cid = self.n_cells

        if self.cell_head == None:
            self.cell_head = cid

        self.n_cells += 1
        self.cell_alive[cid] = True
        self.cell_x[cid] = x
        self.cell_y[cid] = y

        if insert_before:
            self._insert_before(insert_before, cid)

        else:
            self._append(cid)

        return cid

    cdef void _cell_input(self, int cid):
        """ Map cell stats to nerual input in [-1, 1] range.
        """
        self.cell_inputs[0] = (self.cell_light[cid]*2) - 1
        self.cell_inputs[1] = (self.cell_curvature[cid]/(M_PI)) - 1
        self.cell_inputs[2] = (self.energy_usage*2) - 1

        if self.cell_type[cid] == 1:
            self.cell_inputs[3] = 1

        elif self.cell_type[cid] == 2:
            self.cell_inputs[4] = 1

        self.cell_inputs[5] = 1 # The last input is always used as bias.
        # self.cell_inputs[7] = random()

    cdef void order_cells(self):
        cdef int cid, i
        cid = self.cell_head

        for i in range(self.n_cells):
            # assert(self.cell_alive[cid])
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

        # if x < 0 or y < 0:
        #     return False

        # if x >= self.world.width or y >= self.world.height:
        #     return False

        x1 = x_next - x
        y1 = y_next - y
        x2 = x_prev - x
        y2 = y_prev - y
        angle = geometry.angle_clockwise(x1, y1, x2, y2)
        # print(angle)
        if angle > constants.MAX_ANGLE:
            return False

        return True

    cdef void _make_polygon(self):
        cdef int i, cid
        self.polygon = []
        for i in range(self.n_cells):
            cid = self.cell_order[i]
            self.polygon.append((self.cell_x[cid], self.cell_y[cid]))

    cpdef void _calculate_mesh(self):
        # pass
        # def round_trip_connect(start, end):
        #     return
        mesh_info = MeshInfo()
        mesh_info.set_points(self.polygon)
        end = len(self.polygon)-1
        facets = [(i, i+1) for i in range(0, end)] + [(end, 0)]
        mesh_info.set_facets(facets)
        self.mesh = build(mesh_info)

    cdef void _calculate_norms(self):
        cdef int i, cid, cid_prev, cid_next
        cdef double x1, y1, x2, y2, norm_x, norm_y

        for i in range(self.n_cells):
            cid = self.cell_order[i]
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
        cdef int i, cid
        cdef double angle, light, height_percentage, light_min

        light_min = 0.5

        self.light = 0
        self.world.calculate_light(self)

        for i in range(self.n_cells):
            cid = self.cell_order[i]

            if not self.cell_alive[cid]:
                continue

            if self.cell_light[cid] > 0:

                height_percentage = self.cell_y[cid] / float(self.world.height)

                # angle in radians (will be no values > pi or < 0)
                angle = atan2(self.cell_norm[cid, 1], self.cell_norm[cid, 0])

                if angle < 0:
                    light = 0
                else:
                    # map angle to [0, 1]
                    light = 1 - abs(M_PI_2 - angle) / M_PI_2

                # Map value from min to 1 by height
                light = light_min + (1 - light_min)*light*height_percentage

                assert (0 <= light <= 1), light

                self.cell_light[cid] = light

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
                self.cell_curvature[cid] = angle
