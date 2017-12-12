# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True
import numpy as np
cimport numpy as np
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
    cdef double[:,:] inputs = coral.polyp_inputs
    cdef unsigned int[:] polyp_memory = coral.polyp_memory

    inputs[:,:] = -1

    for i in range(coral.n_polyps):
        inputs[i, 0] = (polyp_light[i] * 2) - 1
        inputs[i, 1] = (coral.polyp_verts[i].curvature * 2)
        inputs[i, 2] = (polyp_gravity[i] * 2) - 1

        input_idx = 3

        for mi in range(n_morphogens):
            mbin = <int>(floor(morphogensU[mi, i] * morph_thresholds))
            mbin = min(morph_thresholds - 1, mbin)

            if mbin > 0:
                inputs[i, input_idx + (mbin-1)] = 1

            input_idx += (morph_thresholds-1)

        for mi in range(coral.n_memory):
            if polyp_memory[i] & (1 << mi):
                inputs[i, input_idx] = 1
            else:
                inputs[i, input_idx] = -1
            input_idx += 1

cpdef void grow_polyps(object coral) except *:
    cdef int i, out_idx
    cdef unsigned int mi
    cdef int n_memory = coral.n_memory
    cdef list output, neighbors
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

    createPolypInputs(coral)

    for i in range(coral.n_polyps):
        # coral.createPolypInputs(i)
        coral.network.Flush() # Compute feed-forward network results.
        coral.network.Input(coral.polyp_inputs[i])
        coral.network.ActivateFast()
        output = coral.network.Output()

        # Move in normal direction by growth amount.
        growth = output[0] * growth_scalar
        polyp_pos_next[i, 0] = polyp_pos[i, 0] + growth * polyp_normal[i, 0]
        polyp_pos_next[i, 1] = polyp_pos[i, 1] + growth * polyp_normal[i, 1]
        polyp_pos_next[i, 2] = polyp_pos[i, 2] + growth * polyp_normal[i, 2]

        # Output morphogens.
        out_idx = 1
        for mi in range(coral.morphogens.n_morphogens):
            if output[out_idx] > 0.5:
                morphogensV[mi, i] = 1
            out_idx += 1

        for mi in range(n_memory):
            if output[out_idx] > 0.5:
                polyp_memory[i] = polyp_memory[i] | ( 1 << mi )
            out_idx += 1

    for i in range(coral.n_polyps):
        vert = coral.mesh.verts[i]

        if vert.p[1] < 0:
            continue

        neighbors = vert.neighbors()

        vmultf(spring_target, spring_target, 0) # Reset to 0

        for neighbor in neighbors:
            # spring_target += target_edge_len * normed(neighbor.p - vert.p)
            vsub(temp, neighbor.p, vert.p)
            inormalized(temp)
            vmultf(temp, temp, target_edge_len)
            vadd(spring_target, spring_target, temp)

        vmultf(spring_target, spring_target, 1/len(neighbors))
        vadd(spring_target, spring_target, vert.p)

        # temp = (1-spring_strength) * (self.polyp_pos_next[i]) + (spring_strength * spring_target)
        vmultf(temp, polyp_pos_next[i],  1 - spring_strength)
        vmultf(spring_target, spring_target, spring_strength)
        vadd(temp, temp, spring_target)
        coral.collisionManager.attemptVertUpdate(vert.id, temp)
