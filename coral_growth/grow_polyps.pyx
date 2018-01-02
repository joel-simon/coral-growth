# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True
from __future__ import division
import numpy as np
cimport numpy as np
# from random import shuffle
# from cyrandom import shuffle
from libc.math cimport floor, fmin, fmax, fabs
from cymesh.vector3D cimport inormalized, vadd, vsub, vmultf, vset

cpdef void createPolypInputs(object coral) except *:
    """ Map polyp stats to nerual input in [-1, 1] range. """
    cdef int input_idx, i, mi, mbin
    cdef int n_morphogens = coral.morphogens.n_morphogens
    cdef int morph_thresholds = coral.morph_thresholds
    cdef double[:,:] morphogensU = coral.morphogens.U
    cdef double[:] polyp_light = coral.polyp_light
    cdef double[:] polyp_gravity = coral.polyp_gravity
    cdef double[:] polyp_collection = coral.polyp_collection
    cdef double[:,:] inputs = coral.polyp_inputs
    cdef unsigned int[:] polyp_memory = coral.polyp_memory
    cdef int num_inputs = coral.num_inputs

    inputs[:, :] = -1

    for i in range(coral.n_polyps):
        inputs[i, 0] = (polyp_light[i] * 2) - 1
        inputs[i, 1] = (coral.polyp_verts[i].curvature * 2)
        inputs[i, 2] = (polyp_gravity[i] * 2) - 1
        inputs[i, 3] = (polyp_collection[i] * 2) - 1

        input_idx = 4

        for mi in range(n_morphogens):
            mbin = <int>(floor(morphogensU[mi, i] * morph_thresholds))
            mbin = min(morph_thresholds - 1, mbin)

            if mbin > 0:
                inputs[i, input_idx + (mbin-1)] = 1

            input_idx += (morph_thresholds-1)

        for mi in range(coral.n_memory):
            if polyp_memory[i] & (1 << mi):
                inputs[i, input_idx] = 1
            input_idx += 1

        inputs[input_idx] = 1 # Bias Bit

        assert input_idx == (num_inputs-1)

cpdef void grow_polyps(object coral) except *:
    cdef int i, out_idx
    cdef unsigned int mi
    cdef int n_memory = coral.n_memory
    cdef int n_morphogens = coral.n_morphogens
    cdef list neighbors
    cdef object output
    cdef double[:,:] polyp_pos = coral.polyp_pos
    cdef double[:,:] polyp_normal = coral.polyp_normal
    cdef double[:,:] polyp_pos_next = coral.polyp_pos_next
    cdef double[:,:] morphogensV = coral.morphogens.V
    cdef unsigned int[:] polyp_memory = coral.polyp_memory
    cdef double growth_scalar = coral.growth_scalar
    cdef double growth
    cdef double target_edge_len = coral.target_edge_len
    cdef double spring_strength = coral.spring_strength
    cdef double[:] spring_target = np.zeros(3)
    cdef double[:] temp = np.zeros(3)
    cdef unsigned int net_depth = coral.net_depth

    createPolypInputs(coral)

    for i in range(coral.n_polyps):
        coral.network.Flush() # Compute feed-forward network results.
        coral.network.Input(coral.polyp_inputs[i])
        for _ in range(net_depth):
            coral.network.ActivateFast()
        output = coral.network.Output()

        assert len(output) == coral.num_outputs

        # Move in normal direction by growth amount.
        growth = output[0] * growth_scalar
        # polyp_pos_next[i, :] = polyp_pos[i] + growth * polyp_normal[i]
        polyp_pos_next[i, 0] = polyp_pos[i, 0] + growth * polyp_normal[i, 0]
        polyp_pos_next[i, 1] = polyp_pos[i, 1] + growth * polyp_normal[i, 1]
        polyp_pos_next[i, 2] = polyp_pos[i, 2] + growth * polyp_normal[i, 2]

        # Output morphogens.
        out_idx = 1
        for mi in range(n_morphogens):
            if output[out_idx] > 0.75:
                morphogensV[mi, i] = 1
            out_idx += 1

        for mi in range(n_memory):
            if output[out_idx] > 0.75:
                polyp_memory[i] |= ( 1 << mi )
            out_idx += 1

    # ordering = list(range(coral.n_polyps))
    # shuffle(ordering)
    # for i in ordering:

    for i in range(coral.n_polyps):
        vert = coral.mesh.verts[i]

        neighbors = vert.neighbors()

        vmultf(spring_target, spring_target, 0.0)

        for neighbor in neighbors:
            # spring_target += coral.target_edge_len * normed(np.array(neighbor.p) - vert.p)
            vsub(temp, neighbor.p, vert.p)
            inormalized(temp)
            vmultf(temp, temp, coral.target_edge_len)
            vadd(spring_target, spring_target, temp)

        vmultf(spring_target, spring_target, 1.0 / len(neighbors))
        vadd(spring_target, spring_target, vert.p)

        temp[0] = (1-spring_strength) * polyp_pos_next[i, 0] + spring_strength * spring_target[0]
        temp[1] = (1-spring_strength) * polyp_pos_next[i, 1] + spring_strength * spring_target[1]
        temp[2] = (1-spring_strength) * polyp_pos_next[i, 2] + spring_strength * spring_target[2]


        if temp[1] < 0:
            continue

        successful = coral.collisionManager.attemptVertUpdate(vert.id, temp)
        coral.polyp_collided[i] = not successful
