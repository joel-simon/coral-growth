# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True

from __future__ import print_function, division
from libc.stdint cimport uintptr_t
from libc.math cimport M_PI

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
        self.max_plants  = params['max_plants']
        self.use_physics = params['use_physics']
        self.verbose = params['verbose']

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
        plant.update_attributes()
        # self.add_plant_to_hash(plant)
        return 1 # To eventually become plant id.

    cdef void add_plant_to_hash(self, Plant plant) except *:
        cdef Face *face
        cdef (Vert *) v1, v2, v3
        cdef Node *fnode = plant.mesh.faces
        cdef double a[2], b[2], c[2]

        a[2] = 0
        b[2] = 0
        c[2] = 0

        """ Add every mesh face to spatial hash. """
        while fnode != NULL:
            face = <Face *> fnode.data
            plant.mesh.face_verts(face, &v1, &v2, &v3)
            self.th3d.add_tri(face, v1.p, v2.p, v3.p)

            # Take only xz component.
            a[0] = v1.p[0]
            a[1] = v1.p[2]
            b[0] = v2.p[0]
            b[1] = v2.p[2]
            c[0] = v3.p[0]
            c[1] = v3.p[2]
            self.th2d.add_tri(face, a, b, c)

            fnode = fnode.next

    cpdef void simulation_step(self) except *:
        """ The main function called from outside.
            We assume the plant attributes begin up to date.
        """
        cdef Plant plant

        self.th3d.initialize()
        self.th2d.initialize()

        if self.verbose:
            print('Step: ', self.step)

        for plant in self.plants:
            if self.verbose:
                print('\talive: ', plant.alive)
                print('\tncells: ', str(plant.n_cells))

            if plant.alive:
                self.add_plant_to_hash(plant)

        for plant in self.plants:
            if plant.alive:
                plant.grow()

        self.restrict_growth()

        for plant in self.plants:
            if plant.alive:
                plant.cell_division()
                plant.update_attributes()

            if plant.n_cells >= constants.MAX_CELLS:
                plant.alive = False

        self.step += 1
        if self.verbose: print()

    cdef void restrict_growth(self) except *:
        cdef:
            Plant plant
            Face *face
            Cell *cell
            (Node *) fnode
            (Vert *) v, v1, v2, v3
            double old_p[3]
            size_t i
            # int key

        for plant in self.plants:
            if not plant.alive:
                continue

            """ Check all vertex growth, in arbitrary order, for intersection.
            """
            for i in range(plant.n_cells):
                cell = &plant.cells[i]

                """ Store the old position, we reset to this if we intersect.
                """
                vset(old_p, cell.vert.p)
                vset(cell.vert.p, cell.next_p)

                """ Loop through the adjacent faces.
                """
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
                # print()
                # # key = int(<uintptr_t>face)
                # plant.mesh.face_verts(face, &v1, &v2, &v3)
                    # bb_from = bb_from_tri(&v1.p, &v2.p, &v3.p)
                    # bb_to = bb_from_tri(&v1.next_p, &v2.next_p, &v3.next_p)
                    # self.sh.remove_object(key)
                    # self.sh.add_object(key, bb_to)
                    # vset(&v1.p, &v1.next_p)
                    # vset(&v2.p, &v2.next_p)
                    # vset(&v3.p, &v3.next_p)
                # else:
                #     print('blocked')

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

    cdef void calculate_light(self, Plant plant) except *:
        cdef:
            uint m, n
            (Vert *) v1, v2, v3#, v4, v5, v6
            Node *fnode = plant.mesh.faces
            Face *face
            double p[2], a[2], b[2], c[2]
            double light[3]
            double total_light = 0
            cdef size_t i, j
            cdef bint below
            cdef double angle_to_light

        light[:] = [0, 1.0, 0]

        for i in range(plant.n_cells):
            cell = &plant.cells[i]

            # Below ground
            if cell.vert.p[1] < 0:
                continue

            p[0] = cell.vert.p[0]
            p[1] = cell.vert.p[2]

            angle_to_light = vangle(light, cell.vert.normal) / M_PI

            if angle_to_light > .5:
                cell.light = 0
                continue

            cell.light = 1

            m = self.max_face_neighbors
            n = self.th2d.neighbors(p, m, self.face_neighbors)
#
            # while fnode != NULL:
            #     face = <Face *>fnode.data
            #     fnode = fnode.next
            for j in range(n):
                face = <Face *>self.face_neighbors[j]
                plant.mesh.face_verts(face, &v1, &v2, &v3)

                if v1 == cell.vert or v2 == cell.vert or v3 == cell.vert:
                    continue

                # If face is below vert, it does not block.
                if (v1.p[1] + v2.p[1] + v3.p[1]) / 3.0 < cell.vert.p[1]:
                    continue

                a[0] = v1.p[0]
                a[1] = v1.p[2]
                b[0] = v2.p[0]
                b[1] = v2.p[2]
                c[0] = v3.p[0]
                c[1] = v3.p[2]

                if pnt_in_tri(p, a, b, c):
                    cell.light = 0
                    break

            if cell.light > 0:
                cell.light = 1 - angle_to_light
                total_light += cell.light

            total_light += cell.light

        plant.light = total_light
