# cython: boundscheck=False
# cython: wraparound=True
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True

cimport numpy as np
import numpy as np
from cymem.cymem cimport Pool

from cymesh.structures cimport Vert

cdef class Morphogens:
    def __init__(self, coral, config, n_morphogens):
        self.mem = Pool()
        self.coral = coral
        self.mesh = coral.mesh
        self.n_morphogens = n_morphogens

        self.F = np.zeros(self.n_morphogens)
        self.K = np.zeros(self.n_morphogens)
        self.diffU = np.zeros(self.n_morphogens)
        self.diffV = np.zeros(self.n_morphogens)

        cdef size_t i
        for i in range(n_morphogens):
            self.F[i] = config['F%i'%i]
            self.K[i] = config['K%i'%i]
            self.diffU[i] = config['diffU%i'%i]
            self.diffV[i] = config['diffV%i'%i]

        self.U = np.ones((self.n_morphogens, coral.max_polyps))
        self.V = np.zeros((self.n_morphogens, coral.max_polyps))

        self.dU = np.zeros((coral.max_polyps))
        self.dV = np.zeros((coral.max_polyps))

        # self.n_neighbors = np.zeros(coral.max_polyps, dtype='uint16')
        self.neighbors = NULL

    cpdef void update(self, int steps) except *:
        cdef int n = self.coral.n_polyps
        cdef int i = 0
        cdef int c
        cdef Node *node
        cdef Vert vert, nvert

        self.neighbors = <Node **>self.mem.alloc(n, sizeof(Node *))

        for i in range(n):
            self.neighbors[i] = NULL
            vert = self.coral.polyp_verts[i]

            for nvert in vert.neighbors():
                node = <Node *>self.mem.alloc(1, sizeof(Node))
                node.key = nvert.id
                node.next = self.neighbors[i]
                self.neighbors[i] = node

        for i in range(self.n_morphogens):
            self.gray_scott(steps, i)

    cpdef void gray_scott(self, int steps, int mi) except *:
        cdef int i = 0
        cdef int n = self.coral.n_polyps
        cdef int nidx, nn
        cdef double uvv, u, v, lapU, lapV
        cdef Node *node
        cdef double[:] U = self.U[mi]
        cdef double[:] V = self.V[mi]
        cdef double diffU = self.diffU[mi]
        cdef double diffV = self.diffV[mi]
        cdef double F = self.F[mi]
        cdef double K = self.K[mi]

        for _ in range(steps):
            for i in range(n):
                u = U[i]
                v = V[i]
                node = self.neighbors[i]
                nn = 0
                uvv = u*v*v
                lapU = 0
                lapV = 0

                while node != NULL:
                    lapU += U[node.key]
                    lapV += V[node.key]
                    nn += 1
                    node = node.next

                lapU -= nn*u
                lapV -= nn*v

                self.dU[i] = diffU * lapU - uvv + F*(1 - u)
                self.dV[i] = diffV * lapV + uvv - (K+F)*v

            for i in range(n):
                U[i] += self.dU[i]
                V[i] += self.dV[i]
