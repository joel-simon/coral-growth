# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True

from libc.math cimport cos, sin, round

import numpy as np
cimport numpy as np

from plant_growth.vec2D cimport Vec2D
from plant_growth.plant cimport Plant

from plant_growth import constants
from plant_growth cimport geometry

cdef class World:
    def __init__(self, int width, int height, double light, int soil_height):
        self.width = width
        self.height = height
        self.light = light
        self.soil_height = soil_height
        self.cos_light = cos(self.light)
        self.sin_light = sin(self.light)

        self.plants = []

        # Spatial hashing for lighting.
        # The width must be larger than the max edge size.
        self.group_width = constants.WORLD_GROUP_WIDTH
        self.num_buckets = constants.WORLD_NUM_BUCKETS
        self.bucket_max_n = constants.WORLD_BUCKET_SIZE
        self.hash_buckets = np.zeros((self.num_buckets, self.bucket_max_n), dtype='i')
        self.bucket_sizes = np.zeros(self.num_buckets, dtype='i')

    cpdef int add_plant(self, double x, double y, double r, network, double efficiency):
        cdef Plant plant = Plant(self, network, efficiency)
        plant.create_circle(x, y, r, constants.SEED_SEGMENTS)
        self.plants.append(plant)
        self.__update()
        plant.update_attributes()
        return 0 # To eventually become plant id.

    cpdef void simulation_step(self):
        """ The main function called from outside.
            We assume the plant attributes begin up to date.
        """
        cdef Plant plant

        for plant in self.plants:
            if plant.alive:
                plant.grow()

        # Update spatial hash based off of cell growth, update_attributes
        # uses this to calculate light values.
        self.__update()

        for plant in self.plants:
            if plant.alive:
                plant.update_attributes()

    cdef int __get_bucket(self, double x, double y):
        # First get spatial section.
        cdef int width = self.group_width
        cdef int q = int(width * round((x - y)/width))

        # Then, hash q to an existing bucket. (32 bit integer hash func)
        # http://stackoverflow.com/a/12996028/2175411
        q = (q ^ (q >> 16)) * 0x45d9f3b
        q = (q ^ (q >> 16)) * 0x45d9f3b
        q = q ^ (q >> 16)
        q = q % self.num_buckets

        return q

    cdef void __update(self):
        """ We place each cell polygon segment into a spatial hash for
            fast lookup later in single_light_collision method.
        """
        cdef int i, j, cid, id_prev
        cdef double x, y, c_x, c_y, p_x, p_y
        cdef Plant plant
        cdef int bucket_id1, bucket_id2, bucket_id3

        for i in range(self.bucket_sizes.shape[0]):
            self.bucket_sizes[i] = 0

        for plant in self.plants:
            for cid in range(plant.n_cells):
                id_prev = plant.cell_prev[cid]
                c_x = plant.cell_x[cid]
                c_y = plant.cell_y[cid]

                p_x = plant.cell_x[id_prev]
                p_y = plant.cell_y[id_prev]

                x = (c_x + p_x) / 2.0
                y = (c_y + p_y) / 2.0

                bucket_id1 = self.__get_bucket(x, y)
                bucket_id2 = self.__get_bucket(c_x, c_y)
                bucket_id3 = self.__get_bucket(p_x, p_y)

                j = self.bucket_sizes[bucket_id1]
                self.hash_buckets[bucket_id1, j] = cid
                self.bucket_sizes[bucket_id1] += 1
                
                if j >= self.bucket_max_n:
                    self.__double_bucket_size()

                if bucket_id2 != bucket_id1:
                    j = self.bucket_sizes[bucket_id2]
                    self.hash_buckets[bucket_id2, j] = cid
                    self.bucket_sizes[bucket_id2] += 1

                    if j >= self.bucket_max_n:
                        self.__double_bucket_size()

                elif bucket_id3 != bucket_id1:
                    j = self.bucket_sizes[bucket_id3]
                    self.hash_buckets[bucket_id3, j] = cid
                    self.bucket_sizes[bucket_id3] += 1

                    if j >= self.bucket_max_n:
                        self.__double_bucket_size()

                    # raise ValueError('Bucket Overflow.')
                # assert j <
    
    cdef void __double_bucket_size(self):
        print('doubling bucket size')
        # Create new buckets of double size.
        new = np.zeros((self.num_buckets, self.bucket_max_n*2), dtype='i')
        # Copy over old values.
        new[:, :self.bucket_max_n] = self.hash_buckets
        self.hash_buckets = new
        self.bucket_max_n *= 2

    cdef bint single_light_collision(self, Plant plant, double x0, double y0, int id_exclude):
        """ See if there is a segment that blocks the light to this point.
            Called by each plant from its update_attributes method.
        """
        cdef int i, cid, cid_prev, bucket_id
        cdef double x1, y1, x2, y2, x3, y3

        bucket_id = self.__get_bucket(x0, y0)

        x1 = x0 + 1000 * self.cos_light
        y1 = y0 + 1000 * self.sin_light

        for i in range(self.bucket_sizes[bucket_id]):
            cid = self.hash_buckets[bucket_id, i]

            if cid == id_exclude:
                continue

            cid_prev = plant.cell_prev[cid]
            x2 = plant.cell_x[cid]
            y2 = plant.cell_y[cid]
            x3 = plant.cell_x[cid_prev]
            y3 = plant.cell_y[cid_prev]

            # Do a quick test to see if segment is on other side.
            if x2 + y2 < x0 + y0 and x3 + y3 < x0 + y0:
                continue

            if geometry.intersect(x0, y0, x1, y1, x2, y2, x3, y3):
                return True

        return False
