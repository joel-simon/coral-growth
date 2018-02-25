# cython: boundscheck=False
# cython: wraparound=True
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True
from __future__ import print_function
from libc.math cimport sqrt, floor, fmin
from collections import defaultdict
from cymesh.structures cimport Vert
from cymesh.vector3D cimport dot, vdist, vsub
import numpy as np
cimport numpy as np

cdef class MeshCollisionManager:
    def __init__(self, mesh, vertices, normals, r=1):
        self.mesh = mesh
        self.vertices = vertices
        self.normals = normals
        self.blocksize = 2*r
        self.r = r
        self.particles = np.zeros((vertices.shape[0], 3), dtype='int32')
        self.grid = defaultdict(set)

    cpdef int[:] getIndices(self, double[:] p) except *:
        """ Map the floating point position into voxel space.
        """
        cdef int[:] indices = np.zeros(3, dtype='i')
        indices[0] = <int>(floor((p[0]) / self.blocksize))
        indices[1] = <int>(floor((p[1]) / self.blocksize))
        indices[2] = <int>(floor((p[2]) / self.blocksize))
        return indices

    cpdef void newVert(self, Vert vert) except *:
        cdef int[:] ind = self.getIndices(vert.p)
        self.grid[ (ind[0], ind[1], ind[2]) ].add( vert.id )
        self.particles[vert.id, 0] = ind[0]
        self.particles[vert.id, 1] = ind[1]
        self.particles[vert.id, 2] = ind[1]

    cpdef bint attemptVertUpdate(self, Vert vert, double[:] p) except *:
        """ Update if it does not collide and return True, else False
        """
        cdef int ix, iy, iz, id_other
        cdef double dist
        cdef set block
        cdef int vid = vert.id
        cdef list neighbors = [v.id for v in vert.neighbors()]
        cdef int[:] old_ind = self.particles[vert.id]
        cdef int[:] new_ind = self.getIndices(p)
        cdef double[:] temp = np.zeros(3)

        for ix in range(new_ind[0]-1, new_ind[0]+2):
            for iy in range(new_ind[1]-1, new_ind[1]+2):
                for iz in range(new_ind[2]-1, new_ind[2]+2):
                    block = self.grid.get((ix, iy, iz), None)
                    if block is None:
                        continue

                    for id_other in block:
                        if vid == id_other or id_other in neighbors:
                            continue
                        dist = vdist(p, self.vertices[id_other])
                        if dist <= self.blocksize:
                            # Do a check that one is in front of the other and not behind.
                            vsub(temp, self.vertices[id_other], p)
                            if dot(temp, self.normals[vid]) > 0:
                                return False

        # Accept the update.
        vert.p[:] = p
        self.particles[vid, 0] = new_ind[0]
        self.particles[vid, 1] = new_ind[1]
        self.particles[vid, 2] = new_ind[2]

        if old_ind[0] != new_ind[0] or old_ind[1] != new_ind[1] or old_ind[2] != new_ind[2]:
            self.grid[(old_ind[0], old_ind[1], old_ind[2])].remove(vid)
            self.grid[(new_ind[0], new_ind[1], new_ind[2])].add(vid)

        return True
