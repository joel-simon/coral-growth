from __future__ import print_function
from libc.math cimport sqrt, floor, fmin
from collections import defaultdict
from cymesh.vector3D cimport dot
import numpy as np
cimport numpy as np

cdef class MeshCollisionManager:
    def __init__(self, mesh, vertices, r=1):
        self.mesh = mesh
        self.vertices = vertices
        self.blocksize = 2*r
        self.r = r
        self.particles = np.zeros((vertices.shape[0], 3), dtype='uint32')
        self.grid = defaultdict(set)

    cdef bint collides(self, int id1, int id2):
        cdef double[:] p1 = self.vertices[id1]
        cdef double[:] p2 = self.vertices[id2]

        cdef double dx = p1[0] - p2[0]
        cdef double dy = p1[1] - p2[1]
        cdef double dz = p1[2] - p2[2]
        cdef double d = sqrt(dx*dx + dy*dy + dz*dz)

        if d > self.blocksize:
            return False

        # Do a check that one is in front of the other and not behind.
        cdef double[:] AB = np.array(p2) - p1
        cdef bint is_in_front = dot(AB, self.mesh.verts[id1].normal) > 0

        return is_in_front

    cpdef void newVert(self, int id) except *:
        """ Return True if add was accepted and False otherwise.
        """
        assert id >= 0 and id < self.particles.shape[0]

        vert = self.mesh.verts[id]

        cdef double[:] p = vert.p
        cdef int xc = <int>(floor(p[0] / self.blocksize))
        cdef int yc = <int>(floor(p[1] / self.blocksize))
        cdef int zc = <int>(floor(p[2] / self.blocksize))

        self.grid[(xc, yc, zc)].add(id)
        self.particles[id][0] = xc
        self.particles[id][1] = yc
        self.particles[id][2] = zc

    cpdef bint attemptVertUpdate(self, int id, double[:] p) except *:
        """ Update if it does not collide and return True, else False
        """
        cdef int ix, iy, iz
        cdef set block
        cdef object vert = self.mesh.verts[id]
        cdef set neighbors = set()

        cdef int xc0 = self.particles[id, 0]
        cdef int yc0 = self.particles[id, 1]
        cdef int zc0 = self.particles[id, 2]

        cdef int xc = <int>(floor(p[0] / self.blocksize))
        cdef int yc = <int>(floor(p[1] / self.blocksize))
        cdef int zc = <int>(floor(p[2] / self.blocksize))

        for other in vert.neighbors():
            neighbors.add(other.id)

        for ix in range(xc-1, xc+2):
            for iy in range(yc-1, yc+2):
                for iz in range(zc-1, zc+2):
                    block = self.grid.get((ix, iy, iz), set())

                    for id_other in block:
                        if id != id_other and id_other not in neighbors and self.collides(id, id_other):
                            return False

        # Accept the update.
        vert.p[:] = p
        self.particles[id][0] = xc
        self.particles[id][1] = yc
        self.particles[id][2] = zc

        if xc0 != xc or yc0 != yc or zc0 != zc:
            self.grid[(xc0, yc0, zc0)].remove(id)
            self.grid[(xc, yc, zc)].add(id)

        return True

    # def removeParticle(self, id):
    #     x, y, r, ix, iy, iz = self.particles[id]
    #     del self.particles[id]
    #     self.grid[(ix, iy, iz)].remove(id)
