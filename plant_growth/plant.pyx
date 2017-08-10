# cython: boundscheck=False
# cython: wraparound=True
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True

from __future__ import print_function
from libc.math cimport M_PI, M_PI_2, log, sqrt, acos, cos, sin, abs, atan2
from math import isnan
from random import random, shuffle
import colorsys
import numpy as np
cimport numpy as np
from cymem.cymem cimport Pool

from plant_growth.world cimport World
from plant_growth import constants
from plant_growth.mesh cimport Mesh, Node, Vert, Face, Edge
from plant_growth.exceptions import MaxCellsException
from plant_growth.vector3D cimport vadd, vmultf

cdef class Plant:
    def __init__(self, world, obj_path, network):
        self.mem = Pool()
        self.world = world
        self.mesh = Mesh.from_obj(obj_path)
        self.mesh0 = Mesh.from_obj(obj_path)
        self.network = network

        self.efficiency = constants.PLANT_EFFICIENCY #params['efficiency']
        self.cell_types = constants.NUM_CELL_TYPES #params['cell_types']

        self.volume = 0
        self.alive = True
        self.gametes = 0
        self.age = 0
        self.n_cells = 0
        self.max_cells = constants.MAX_CELLS
        self.energy = 0

        self.cells = <Cell *>self.mem.alloc(self.max_cells, sizeof(Cell))
        # Constants
        self.cell_min_energy  = constants.cell_min_energy
        self.cell_growth_energy_usage = constants.cell_growth_energy_usage
        self.growth_scalar = constants.CELL_GROWTH_SCALAR

        self.cell_inputs = [0 for _ in range(constants.NUM_INPUTS+1)]
        cdef Node *node = self.mesh.verts
        cdef Vert *vert
        for i in range(self.mesh.n_verts):
            vert = <Vert *>node.data
            self.create_cell(vert)
            node = node.next
        self.update_attributes()

    cdef void grow(self) except *:
        """ Calculate the changes to plant by neural network.
            Set cell_next_x and cell_next_y values while decreasing cell_light.
        """
        cdef:
            int i, cid
            list output
            double energy_demand, energy_supply, energy_spent, growth, new_x, new_y
            double next_area, area_change, growth_scalar, energy_usage
            bint verbose = False
            unsigned int ctype_mask
            double[:] growth_amounts = np.zeros(self.max_cells)
            Cell *cell

        for i in range(self.n_cells):
            cell = &self.cells[i]

            if not cell.alive:
                continue

            """ Compute feed-forward network results. """
            output = self.cell_output(cell)

            """ Act on outputs """
            out_i = 0
            # Move in nomral direction by growth amount.
            growth = output[out_i] * self.growth_scalar
            out_i += 1

            """ next_p = p + (norm * growth) """
            vmultf(cell.next_p, cell.vert.normal, growth)
            vadd(cell.next_p, cell.next_p, cell.vert.p)

            ctype_mask = 1
            for _ in range(self.cell_types):
                if output[out_i] > 0.5:
                    cell.ctype |= ctype_mask
                ctype_mask = ctype_mask << 1
                out_i += 1

        """ Calculate area of growth to see how much energy is needed.
            Scale overall growth down depending on available energy.
        """
        # cdef list next_polygon = []
        # for i in range(self.n_cells):
        #     cid = self.cell_order[i]
        #     next_polygon.append((self.cell_next_x[cid], self.cell_next_y[cid]))

        # next_area = geometry.polygon_area(next_polygon)
        # area_change = next_area - self.volume
        # energy_demand = area_change * self.cell_growth_energy_usage

        # assert area_change >= 0

        # if energy_demand == 0:
        #     growth_scalar = 0
        # else:
        #     growth_scalar = min(1, self.energy / energy_demand)

        # energy_usage = energy_demand * growth_scalar
        # energy_usage = min(energy_usage, self.energy) # This is just to deal with rounding errors.

        # if verbose:
        #     print('Area Change:', area_change)
        #     print('Energy Demand:', energy_demand)
        #     print('Growth Scalar:', growth_scalar)
        #     print('Energy', self.energy)
        #     print('Energy usage', energy_usage)
        #     print()

        # for i in range(self.n_cells):
        #     cid = self.cell_order[i]
        #     growth = growth_amounts[cid] * growth_scalar
        #     new_x = self.cell_x[cid] + self.cell_norm[cid, 0] * growth
        #     new_y = self.cell_y[cid] + self.cell_norm[cid, 1] * growth
        #     self.cell_next_x[cid] = new_x
        #     self.cell_next_y[cid] = new_y

        # """ If all growth can be afforded, put excess into gamete production.
        # """
        # self.energy -= energy_usage
        # assert self.energy >= 0
        # self.gametes += self.energy

    cdef void update_attributes(self) except *:
        """ In each simulation step, grow is called on all plants then
            update_attributes. Grow has used up all spare energy.
        """
        self.volume = self.mesh.volume()
        self.mesh.calculate_normals()
        self.mesh.calculate_curvature()
        self.world.calculate_light(self)
        self.energy = self.light
        self.age += 1

        if self.volume > self.efficiency * self.energy:
            self.alive = False



    cdef double _calculate_energy_transfer(self) except *:
        pass
        # """
        # """
        # cdef int i, cid
        # cdef double transfer
        # cdef double plant_spare_energy = 0
        # cdef double n_needy_cells = 0

        # for i in range(self.n_cells):
        #     cid = self.cell_order[i]
        #     if not self.cell_alive[cid]:
        #         continue
        #     if self.cell_energy[cid] < self.cell_min_energy:
        #         n_needy_cells += 1
        #     else:
        #         plant_spare_energy += self.cell_energy[cid] - self.cell_min_energy

        # # print('%i needy cells and %f spare'%(n_needy_cells, plant_spare_energy))
        # cdef list cid_list = [self.cell_order[i] for i in range(self.n_cells)]
        # shuffle(cid_list)

        # for i in range(self.n_cells):
        #     # cid = self.cell_order[i]
        #     cid = cid_list[i]

        #     if not self.cell_alive[cid]:
        #         continue

        #     if self.cell_energy[cid] < self.cell_min_energy:
        #         transfer = self.cell_min_energy - self.cell_energy[cid]

        #         if transfer <= plant_spare_energy:
        #             self.cell_energy[cid] += transfer
        #             plant_spare_energy -= transfer
        #         else:
        #             self.cell_alive[cid] = False

        # return plant_spare_energy

    cdef int create_cell(self, Vert *vert) except -1:
        if self.n_cells == constants.MAX_CELLS:
            raise MaxCellsException()
        cdef Cell *cell
        cell = &self.cells[self.n_cells]
        cell.vert = vert
        cell.id = self.n_cells
        self.n_cells += 1
        cell.light = 0
        cell.curvature = 0
        cell.strain = 0
        cell.ctype = 0
        cell.alive = 1

        return cell.id

    cdef list cell_output(self, Cell *cell):
        """ Map cell stats to nerual input in [-1, 1] range. """
        cdef unsigned int i = 2
        cdef unsigned int ctype_mask = 1

        self.cell_inputs[0] = (cell.light * 2) - 1
        self.cell_inputs[1] = (cell.curvature * 2) - 1

        # self.cell_inputs[2] = (self.energy_usage*2) - 1
        # self.cell_inputs[3] = (cell.strain*2) - 1

        for _ in range(self.cell_types):
            self.cell_inputs[i] = (cell.ctype & ctype_mask) != 0
            ctype_mask = ctype_mask << 1
            i += 1

        self.cell_inputs[i] = 1 # The last input is always used as bias.
        self.network.Flush()
        self.network.Input(self.cell_inputs)
        self.network.ActivateFast()
        output = self.network.Output()

        return output

    cdef list cell_division(self):
        """ Update the mesh and create new cells.
            This is called after growth has occured.
            Return new cell ids
        """
        cdef:
            int i, id
            (Vert *) vert, v1, v2
            Node *node = self.mesh.edges
            Edge *edge
            # list new_cells = []

        for i in range(self.mesh.n_edges):
            edge = <Edge *>node.data
            node = node.next

            if self.mesh.edge_length(edge) > constants.MAX_EDGE_LENGTH:
                vert = self.mesh.edge_split(edge)
                try:
                    id = self.create_cell(vert)
                    # new_cells.append(id)

                except MaxCellsException:
                    break

        # self.mesh.smooth()

        # return new_cells
        return []

    cdef void _calculate_light(self) except *:
        pass

    def export(self):
        cdef Node *vnode = self.mesh.verts
        cdef Vert *vert
        cdef int i = 0
        cdef int j = 0
        cdef Cell *cell

        vert_colors = np.zeros((self.n_cells, 3))

        id_to_indx = {}
        while vnode != NULL:
            vert = <Vert *> vnode.data
            id_to_indx[vert.id] = i
            vnode = vnode.next
            i += 1

        for j in range(self.n_cells):
            cell = &self.cells[j]
            color = colorsys.hsv_to_rgb(100.0/360, .70, .3 + .7*cell.light)
            vert_colors[id_to_indx[cell.vert.id]] = list(color)

        mesh_data = self.mesh.export()
        mesh_data['vert_colors'] = vert_colors
        return mesh_data
        # cells [{ 'id': c.id, 'light': light }]
