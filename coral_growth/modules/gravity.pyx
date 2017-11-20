# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True

from libc.math cimport M_PI
from cymesh.vector3D cimport vangle
import numpy as np

cpdef void calculate_gravity(coral) except *:
    """ Calculate the light on each polyp of a coral.
    """
    cdef int i = 0
    # Memeoryviews of coral.
    cdef double[:] polyp_gravity = coral.polyp_gravity
    cdef double[:,:] polyp_normal = coral.polyp_normal
    cdef double[:] down = np.array([0, -1.0, 0], dtype='float64')

    for i in range(coral.n_polyps):
        polyp_gravity[i] = vangle(down, polyp_normal[i]) / M_PI
