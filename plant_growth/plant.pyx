# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True
# cython: linetrace=True

import math
from libc.math cimport M_PI, log, sqrt, fmin, fmax, acos, cos, sin, abs

from plant_growth.vec2D cimport Vec2D
from plant_growth.world cimport World

from plant_growth import constants
from plant_growth cimport geometry

import numpy as np
cimport numpy as np

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

        self.n_cells = 0
        self.cell_p = np.empty(constants.MAX_CELLS, dtype=object)
        # self.cell_x = np.empty(constants.MAX_CELLS)
        # self.cell_y = np.empty(constants.MAX_CELLS)

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
        cdef double growth
        cdef bint flower, death
        cdef double[:] inputs
        cdef int cid, cid_prev, cid_next
        cdef Vec2D v_cell, v_prev, v_next, Va, Vb, v_new

        for cid in range(self.n_cells):
            cid_prev = self.cell_prev[cid]
            cid_next = self.cell_next[cid]

            v_cell = self.cell_p[cid]
            v_prev = self.cell_p[cid_prev]
            v_next = self.cell_p[cid_next]

            self._cell_input(cid)
            output = self._output()

            growth = output[0] * constants.CELL_MAX_GROWTH
            flower = output[1] > .5
            death  = output[2] > .5

            # An underground cell may not flower.
            if self.cell_water[cid]:
                self.cell_flower[cid] = False
                flower = False

            if death:
                self.cell_p[cid].x = (v_prev.x + v_next.x) / 2.0
                self.cell_p[cid].y = (v_prev.y + v_next.y) / 2.0

            if not self.cell_water[cid] and flower:
                if self.energy >= constants.FLOWER_COST:
                    self.energy -= constants.FLOWER_COST
                    self.cell_flower[cid] = True

            new_p = Vec2D(
                v_cell.x + self.cell_norm[cid, 0] * 3 * growth,
                v_cell.y + self.cell_norm[cid, 1] * 3 * growth
            )

            if self._valid_growth(new_p, v_prev, v_next):
                self.cell_p[cid].x += self.cell_norm[cid, 0] * growth
                self.cell_p[cid].y += self.cell_norm[cid, 1] * growth

        self._split_links()
        self._order_cells()

    cpdef void create_circle(self, double x, double y, double r, int n):
        cdef int i
        cdef double a, xx, yy
        for i in range(n):
            a = 2 * i * math.pi / n
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
        self.cell_p[cid] = Vec2D(x, y)

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
        self.cell_inputs[5] = log(self.water/self.light)
        self.cell_inputs[6] = 1 # The last input is always used as bias.

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

    cdef bint _valid_growth(self, Vec2D v_cell, Vec2D v_prev, Vec2D v_next):
        cdef Vec2D Sa, Sb
        cdef int x, y

        if v_cell.x < 0 or v_cell.y < 0:
            return False

        if v_cell.x >= self.world.width or v_cell.x >= self.world.height:
            return False

        Sa = v_next - v_cell
        Sb = v_prev - v_cell
        if Sa.angle_clockwise(Sb) > constants.MAX_ANGLE:
            return False

        # x1, y1 = cell.prev.vector
        # x2, y2 = v_cell
        # for id in self.world.sh.segment_intersect(x1, y1, x2, y2):
        #     if id != cell.id:
        #         return False
        x = <int>v_cell.x
        y = <int>v_cell.y
        if self.grid[x, y]:
            return False

        x = <int>((v_cell.x + v_prev.x) / 2.)
        y = <int>((v_cell.y + v_prev.y) / 2.)
        if self.grid[x, y]:
            return False

        x = <int>((v_cell.x + v_next.x) / 2.)
        y = <int>((v_cell.y + v_next.y) / 2.)
        if self.grid[x, y]:
            return False

        return True

    cdef object _make_polygon(self):
        cdef int i, cid
        cdef Vec2D v
        polygon = []

        for i in range(self.n_cells):
            cid = self.ordered_cell[i]
            v = self.cell_p[cid]
            polygon.append((v.x, v.y))

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

            x1 = self.cell_p[cid_prev].x - self.cell_p[cid].x
            y1 = self.cell_p[cid_prev].y - self.cell_p[cid].y

            x2 = self.cell_p[cid_next].x - self.cell_p[cid].x
            y2 = self.cell_p[cid_next].y - self.cell_p[cid].y

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
        cdef double dist, x, y
        cdef Vec2D v_cell, v_prev

        inserts = []

        if self.n_cells >= constants.MAX_CELLS:
            return

        for cid in range(self.n_cells):
            id_prev = self.cell_prev[cid]

            v_cell = self.cell_p[cid]
            v_prev = self.cell_p[id_prev]

            dist = v_cell.sub(v_prev).norm()

            if dist > constants.MAX_EDGE_LENGTH:
                inserts.append(cid)

        for cid in inserts:
            id_prev = self.cell_prev[cid]
            v_cell = self.cell_p[cid]
            v_prev = self.cell_p[id_prev]

            if self.n_cells >= constants.MAX_CELLS:
                break

            x, y = (v_cell + v_prev) / 2.0
            self._create_cell(x, y, before=cid)

    cdef void _calculate_collision_grid(self):
        img = Image.new('L', (self.world.width, self.world.height), 0)
        ImageDraw.Draw(img).polygon(self.polygon, outline=0, fill=1)
        np.copyto(np.asarray(self.grid).T, img)
        # self.grid = np.asarray(img, dtype=np.uint8).T

    cdef void _calculate_light(self):
        cdef int cid, id_prev
        cdef double light
        cdef Vec2D P, v_cell, v_prev, v_light, v_segment

        self.light = 0.0

        for cid in range(self.n_cells):
            id_prev = self.cell_prev[cid]
            v_cell = self.cell_p[cid]
            v_prev = self.cell_p[id_prev]

            P = v_cell.add(v_prev).divf(2.0)

            if self.cell_flower[cid]:
                self.cell_light[cid] = 0.0

            # Underground out_verts do not get sunlight.
            elif v_cell.y <= constants.SOIL_HEIGHT:
                self.cell_light[cid] = 0.0

            # Cast a ray to the center of every segment.
            elif not self.world.single_light_collision(P.x, P.y, cid):
                v_light   = Vec2D(cos(self.light), sin(self.light))
                v_segment = P.sub(v_prev)
                angle = v_light.angle(v_segment)
                light = 1 - (abs(angle - M_PI / 2.0)) / (M_PI / 2.0)

                self.cell_light[cid] += light / 2.0
                self.cell_light[id_prev] += light / 2.0
                self.light += light*constants.MAX_EDGE_LENGTH*constants.LIGHT_EFFICIENCY
            else:
                self.cell_light[cid] = 0

    cdef void _calculate_water(self):
        cdef int cid
        cdef Vec2D v_cell

        self.water = 0
        for cid in range(self.n_cells):

            v_cell = self.cell_p[cid]

            if v_cell.y < constants.SOIL_HEIGHT:
                self.cell_water[cid] = 1
                self.water += constants.MAX_EDGE_LENGTH*constants.WATER_EFFICIENCY
            else:
                self.cell_water[cid] = 0

    cdef void _calculate_curvature(self):
        cdef int cid, id_prev, id_next
        cdef Vec2D v_cell, v1, v2, v_next, v_prev

        for cid in range(self.n_cells):
            id_prev = self.cell_prev[cid]
            id_next = self.cell_next[cid]
            v_cell = self.cell_p[cid]
            v_next = self.cell_p[id_next]
            v_prev = self.cell_p[id_prev]
            v1 = v_next.sub(v_cell)
            v2 = v_prev.sub(v_cell)
            self.cell_curvature[cid] = v1.angle_clockwise(v2)

    cdef void _calculate_flowers(self):
        cdef int cid
        cdef bint flower
        cdef Vec2D v_cell

        self.num_flowers = 0

        for cid in range(self.n_cells):
            v_cell = self.cell_p[cid]
            flower = self.cell_flower[cid]

            if flower:
                self.num_flowers += 1
                self.total_flowering += v_cell.y - self.world.soil_height
