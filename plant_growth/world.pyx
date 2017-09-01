# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True

from __future__ import print_function, division
from libc.stdint cimport uintptr_t
from libc.math cimport M_PI, sin, cos

import numpy as np
cimport numpy as np

from cymem.cymem cimport Pool

from plant_growth.plant cimport Plant, Cell
from plant_growth import constants
from plant_growth.mesh cimport Mesh, Face, Node, Vert

from plant_growth.tri_hash_3d import TriHash3D
from plant_growth.tri_hash_2d import TriHash2D

from plant_growth.vector3D cimport vset, vangle

from plant_growth.tri_intersection cimport tri_tri_intersection

cdef class World:
    def __init__(self, object params):
        self.light_angle = params['light_angle']
        self.verbose = 'verbose' in params and params['verbose']

        self.li_cos = cos(self.light_angle)
        self.li_sin = sin(self.light_angle)
        self.light_vector[:] = [self.li_sin, self.li_cos, 0]

        # self.obstacle_grid = params['obstacle_grid']
        # self.obstacle_grid_size = params['obstacle_grid_size']

        self.mem = Pool()
        self.plants = []
        self.th3d = TriHash3D(cell_size=constants.HASH_CELL_SIZE,
                              world_size=constants.WORLD_SIZE)
        self.th2d = TriHash2D(cell_size=constants.HASH_CELL_SIZE,
                              world_size=constants.WORLD_SIZE)
        self.step = 0

        self.max_face_neighbors = 5000
        self.face_neighbors = <void **>self.mem.alloc(self.max_face_neighbors, sizeof(void *))

    cpdef int add_plant(self, str obj_path, object network) except -1:
        cdef Plant plant = Plant(self, obj_path, network)
        self.plants.append(plant)
        self.add_plant_to_hash(plant, 1)
        self.add_plant_to_hash(plant, 0)
        plant.update_attributes()
        return 1 # To eventually become plant id.

    cdef void add_plant_to_hash(self, Plant plant, int d) except *:
        cdef Face *face
        cdef (Vert *) v1, v2, v3
        cdef Node *fnode = plant.mesh.faces
        cdef double a[2], b[2], c[2]

        """ Add every mesh face to spatial hash. """
        while fnode != NULL:
            face = <Face *> fnode.data
            plant.mesh.face_verts(face, &v1, &v2, &v3)

            if d == 1:
                self.th3d.add_tri(face, v1.p, v2.p, v3.p)
            else:
                self.project_light(a, v1.p)
                self.project_light(b, v2.p)
                self.project_light(c, v3.p)
                self.th2d.add_tri(face, a, b, c)

            fnode = fnode.next

    cpdef void simulation_step(self) except *:
        """ The main function called from outside.
            We assume the plant attributes begin up to date.
        """
        cdef Plant plant
        self.th3d.initialize()
        self.th2d.initialize()

        for plant in self.plants:
            self.add_plant_to_hash(plant, 1)

        for plant in self.plants:
            if plant.alive:
                plant.grow()

        self.restrict_growth()

        for plant in self.plants:
            if plant.alive:
                plant.cell_division()
            self.add_plant_to_hash(plant, 0)

        for plant in self.plants:
            if plant.alive:
                plant.update_attributes()

            if plant.n_cells >= constants.MAX_CELLS:
                plant.alive = False


        if self.verbose:
            print('Step: ', self.step)
            print('\talive: ', plant.alive)
            print('\tlight: ', plant.light)
            print('\twater: ', plant.water)
            print('\tncells: ', str(plant.n_cells))
            print()

        self.step += 1

    cdef void restrict_growth(self) except *:
        cdef:
            Plant plant
            Face *face
            Cell *cell
            (Node *) fnode
            (Vert *) v, v1, v2, v3
            double old_p[3]
            uint grid_x, grid_y, grid_z
            size_t i
            # int key

        for plant in self.plants:
            if not plant.alive:
                continue

            # Check all vertex growth, in arbitrary order, for intersection.
            for i in range(plant.n_cells):
                cell = &plant.cells[i]

                # Store the old position, we reset to this if we intersect.
                vset(old_p, cell.vert.p)
                vset(cell.vert.p, cell.next_p)

                # Check obstacle grid first.
                # grid_x = <int>cell.vert.p[0] / self.obstacle_grid_size
                # grid_y = <int>cell.vert.p[1] / self.obstacle_grid_size
                # grid_z = <int>cell.vert.p[2] / self.obstacle_grid_size

                # Loop through the adjacent faces.
                fnode = plant.mesh.vert_faces(cell.vert)
                while True:
                    face = <Face *>fnode.data
                    if not self.valid_face_position(plant, face):
                        vset(cell.vert.p, old_p)
                        break
                    elif fnode.next == NULL:
                        break
                    else:
                        fnode = fnode.next

            # fnode = plant.mesh.faces
            # while True:
            #     face = <Face *>fnode.data
            #     assert self.valid_face_position(plant, face)

            #     if fnode.next == NULL:
            #         break
            #     else:
            #         fnode = fnode.next

    cdef int valid_face_position(self, Plant plant, Face *face) except -1:
        cdef:
            (Vert *) v1, v2, v3, v4, v5, v6
            Node *node
            Face *face2

        plant.mesh.face_verts(face, &v1, &v2, &v3)

        cdef uint m = self.max_face_neighbors
        cdef uint n = self.th3d.neighbors(v1.p, v2.p, v3.p, m, self.face_neighbors)

        if n == m:
            print('self.max_face_neighbors too small!')

        for i in range(n):
            face2 = <Face *>self.face_neighbors[i]

            plant.mesh.face_verts(face2, &v4, &v5, &v6)

            # Face cannot collide with self or neighbors.
            if face.id == face2.id:
                continue

            elif v1 == v4 or v1 == v5 or v1 == v6:
                continue

            elif v2 == v4 or v2 == v5 or v2 == v6:
                continue

            elif v3 == v4 or v3 == v5 or v3 == v6:
                continue

            elif tri_tri_intersection(v1.p, v2.p, v3.p, v4.p, v5.p, v6.p):
                return False

        return True

    cdef void project_light(self, double src[2], double p[3]):
        # Rotate around z axis and then only take x,z components.
        # https://www.siggraph.org/education/materials/HyperGraph/modeling/mod_tran/3drota.htm
        src[0] = p[0] * self.li_cos - p[1] * self.li_sin
        src[1] = p[2]

    cdef void calculate_light(self, Plant plant) except *:
        cdef:
            uint m, n
            (Vert *) v1, v2, v3
            Node *fnode = plant.mesh.faces
            Face *face
            double p[2], a[2], b[2], c[2]
            double total_light = 0
            size_t i, j
            double angle_to_light, cell_height, ah, bh, ch

        for i in range(plant.n_cells):
            cell = &plant.cells[i]
            cell.light = 1
            cell_height = cell.vert.p[0]*self.li_sin + cell.vert.p[1]*self.li_cos

            # Below ground
            if cell.vert.p[1] < 0:
                cell.light = 0
                continue

            self.project_light(p, cell.vert.p)
            angle_to_light = vangle(self.light_vector, cell.vert.normal) / M_PI

            if angle_to_light > .5:
                cell.light = 0
                continue

            m = self.max_face_neighbors
            n = self.th2d.neighbors(p, m, self.face_neighbors)

            for j in range(n):
                face = <Face *>self.face_neighbors[j]
                plant.mesh.face_verts(face, &v1, &v2, &v3)

                if v1 == cell.vert or v2 == cell.vert or v3 == cell.vert:
                    continue

                # If face is below vert, it does not block.
                ah = v1.p[0]*self.li_sin + v1.p[1]*self.li_cos
                bh = v2.p[0]*self.li_sin + v2.p[1]*self.li_cos
                ch = v3.p[0]*self.li_sin + v3.p[1]*self.li_cos

                if (ah + bh + ch) / 3.0 < cell_height:
                    continue

                self.project_light(a, v1.p)
                self.project_light(b, v2.p)
                self.project_light(c, v3.p)

                if pnt_in_tri(p, a, b, c):
                    cell.light = 0
                    break

            if cell.light > 0:
                cell.light = 1 - angle_to_light
                total_light += cell.light

        plant.light = total_light
