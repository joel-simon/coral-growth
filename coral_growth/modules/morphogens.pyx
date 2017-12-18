# cython: boundscheck=False
# cython: wraparound=True
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True

cimport numpy as np
import numpy as np

from cymesh.structures cimport Vert

cdef class Morphogens:
    def __init__(self, coral, config, n_morphogens):
        self.coral = coral
        self.mesh = coral.mesh
        self.n_morphogens = n_morphogens

        self.F = np.zeros(self.n_morphogens)
        self.K = np.zeros(self.n_morphogens)
        self.diffU = np.zeros(self.n_morphogens)
        self.diffV = np.zeros(self.n_morphogens)

        for i in range(n_morphogens):
            self.F[i] = config['F%i'%i]
            self.K[i] = config['K%i'%i]
            self.diffU[i] = config['diffU%i'%i]
            self.diffV[i] = config['diffV%i'%i]

        self.U = np.ones((self.n_morphogens, coral.max_polyps))
        self.V = np.zeros((self.n_morphogens, coral.max_polyps))

        self.dU = np.zeros((coral.max_polyps))
        self.dV = np.zeros((coral.max_polyps))

        self.n_neighbors = np.zeros(coral.max_polyps, dtype='uint16')
        self.neighbors = []

    cpdef void update(self, int steps) except *:
        self.neighbors = []
        cdef size_t i = 0

        for i in range(self.coral.n_polyps):
            vert = self.coral.polyp_verts[i]
            self.neighbors.append([])
            for nvert in vert.neighbors():
                self.neighbors[i].append(nvert.id)
            self.n_neighbors[i] = len(self.neighbors[i])

        for i in range(self.n_morphogens):
            self.gray_scott(steps, i)

    cpdef void gray_scott(self, int steps, int mi) except *:
        cdef int i = 0
        cdef int n = self.coral.n_polyps
        cdef int nidx, nn
        cdef double uvv, u, v, lapU, lapV

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
                nn = self.n_neighbors[i]
                uvv = u*v*v
                lapU = -(nn*u)
                lapV = -(nn*v)

                for nidx in self.neighbors[i]:
                    lapU += U[nidx]
                    lapV += V[nidx]

                self.dU[i] = diffU * lapU - uvv + F*(1 - u)
                self.dV[i] = diffV * lapV + uvv - (K+F)*v

            for i in range(self.coral.n_polyps):
                U[i] += self.dU[i]
                V[i] += self.dV[i]
