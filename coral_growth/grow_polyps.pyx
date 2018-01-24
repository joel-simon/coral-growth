# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True
from __future__ import division, print_function
import numpy as np
cimport numpy as np
from random import shuffle
# from cyrandom import shuffle
from libc.math cimport floor, fmin, fmax, fabs
from cymesh.vector3D cimport inormalized, vadd, vsub, vmultf, vset, dot

cpdef void createPolypInputs(object coral) except *:
    """ Map polyp stats to nerual input in [-1, 1] range. """
    cdef int input_idx, i, mi, mbin
    cdef int n_morphogens = coral.morphogens.n_morphogens
    cdef int morphogen_thresholds = coral.morphogen_thresholds
    cdef double[:,:] morphogensU = coral.morphogens.U
    cdef double[:] polyp_light = coral.polyp_light
    cdef double[:] polyp_gravity = coral.polyp_gravity
    cdef double[:] polyp_collection = coral.polyp_collection
    cdef double[:,:] polyp_signals = coral.polyp_signals
    cdef double[:,:] inputs = coral.polyp_inputs
    cdef double[:, :] polyp_memory = coral.polyp_memory
    cdef int num_inputs = coral.num_inputs
    cdef list neighbors
    cdef double signal_sum

    inputs[:, :] = -1

    for i in range(coral.n_polyps):
        inputs[i, 0] = (polyp_light[i] * 2) - 1
        inputs[i, 1] = (polyp_gravity[i] * 2) - 1
        inputs[i, 2] = (polyp_collection[i] * 2) - 1

        input_idx = 3

        # Morphogens
        for mi in range(n_morphogens):
            mbin = <int>(floor(morphogensU[mi, i] * morphogen_thresholds))
            mbin = min(morphogen_thresholds - 1, mbin)

            if mbin > 0:
                inputs[i, input_idx + (mbin-1)] = 1

            input_idx += (morphogen_thresholds-1)

        # Memory
        for mi in range(coral.n_memory):
            # if polyp_memory[i] & (1 << mi):
            #     inputs[i, input_idx] = 1
            if polyp_memory[i, mi] > 0.5:
                inputs[i, input_idx] = 1
            input_idx += 1

        # Signals
        neighbors = coral.polyp_verts[i].neighbors()
        for mi in range(coral.n_signals):
            signal_sum = 0
            for v in neighbors:
                signal_sum += polyp_signals[v.id, mi]
            inputs[i, input_idx] = ((signal_sum / len(neighbors)) > 0.5)
            input_idx += 1

        inputs[i, input_idx] = 1 # Bias Bit

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
    cdef double[:,:] pos_next = coral.polyp_pos_next
    cdef double[:,:] morphogensV = coral.morphogens.V
    cdef double[:, :] polyp_memory = coral.polyp_memory
    cdef double[:] mem_decay = coral.mem_decay
    cdef double[:] growth = np.zeros(coral.n_polyps)
    cdef double target_edge_len = coral.target_edge_len

    cdef unsigned int net_depth = coral.net_depth
    cdef double max_growth = coral.max_growth
    cdef double growth_scalar, g
    cdef double total_growth = 0

    cdef double[:,:] polyp_pos_past = coral.polyp_pos_past

    polyp_pos_past[:coral.n_polyps,:] = polyp_pos[:coral.n_polyps, :]

    createPolypInputs(coral)

    cdef double old_volume = coral.mesh.volume()

    for i in range(coral.n_polyps):
        coral.polyp_signals[i] = 0

    for i in range(coral.n_polyps):
        # Compute feed-forward network results.
        coral.network.Flush()
        coral.network.Input(coral.polyp_inputs[i])
        for _ in range(net_depth): coral.network.ActivateFast()
        output = coral.network.Output()

        # Move in normal direction by growth amount.
        growth[i] = output[0]
        polyp_pos[i, 0] += growth[i] * polyp_normal[i, 0]
        polyp_pos[i, 1] += growth[i] * polyp_normal[i, 1]
        polyp_pos[i, 2] += growth[i] * polyp_normal[i, 2]

        # Output morphogens.
        out_idx = 1
        for mi in range(n_morphogens):
            if output[out_idx] > 0.5:
                morphogensV[mi, i] = 1
            out_idx += 1

        # Memory
        for mi in range(n_memory):
            # if output[out_idx] > 0.5:
            #     polyp_memory[i] |= ( 1 << mi )
            polyp_memory[i, mi] *= mem_decay[mi]
            polyp_memory[i, mi] += output[out_idx]
            out_idx += 1

        # Signals
        for mi in range(coral.n_signals):
            if output[out_idx] > 0.5:
                coral.polyp_signals[out_idx, mi] = 1.0
            else:
                coral.polyp_signals[out_idx, mi] = 0.0
            out_idx += 1

    cdef double new_volume = coral.mesh.volume()
    coral.mesh.calculateDefect()

    polyp_pos[:coral.n_polyps, :] = polyp_pos_past[:coral.n_polyps,:]

    total_growth = new_volume - old_volume

    if total_growth == 0:
        growth_scalar = 0.0
    else:
        growth_scalar = coral.C * coral.energy / total_growth

    for i in range(coral.n_polyps):
        g = min(growth[i] * growth_scalar, max_growth)

        pos_next[i, 0] = polyp_pos[i, 0] + g * polyp_normal[i, 0]
        pos_next[i, 1] = polyp_pos[i, 1] + g * polyp_normal[i, 1]
        pos_next[i, 2] = polyp_pos[i, 2] + g * polyp_normal[i, 2]

    # ordering = list(range(coral.n_polyps))
    # shuffle(ordering)

    # cdef double[:] AB = np.zeros(3)

    # # for i in ordering:
    # for i in range(coral.n_polyps):
    #     vert = coral.mesh.verts[i]

    #     neighbors = vert.neighbors()

    #     # Calculate a spring target based off neighbors positions.
    #     vmultf(spring_target, spring_target, 0.0)
    #     for neighbor in neighbors:
    #         # spring_target += target_edge_len * normed(neighbor.p - vert.p)
    #         vsub(temp, polyp_pos[neighbor.id], vert.p)
    #         inormalized(temp)
    #         vmultf(temp, temp, coral.target_edge_len)
    #         vadd(spring_target, spring_target, temp)

    #     vmultf(spring_target, spring_target, 1.0 / len(neighbors))
    #     vadd(spring_target, spring_target, vert.p)

    #     # Calculate the smoothed target position.
    #     temp[0] = (1-spring_strength) * pos_next[i, 0] + spring_strength * spring_target[0]
    #     temp[1] = (1-spring_strength) * pos_next[i, 1] + spring_strength * spring_target[1]
    #     temp[2] = (1-spring_strength) * pos_next[i, 2] + spring_strength * spring_target[2]

    #     # Check if the smoothed position is actually behind where we are
    #     # currently. If so, don't include smoothing term.
    #     vsub(AB, temp, vert.p)
    #     if dot(AB, vert.normal) < 0:
    #         temp[:] = pos_next[i,:]

    #     if temp[1] < 0:
    #         temp[1] = 0

    #     pos_next[i, :] = temp

    # for i in range(coral.n_polyps):
    #     vert = coral.mesh.verts[i]
    #     if pos_next[i, 1] < 0:
    #         continue

    #     if abs(coral.polyp_verts[i].defect) > coral.params.max_defect:
    #         coral.polyp_collided[i] = True
    #         continue

    #     coral.polyp_collided[i] = False
    #     successful = coral.collisionManager.attemptVertUpdate(vert.id, pos_next[i])
    #     # coral.polyp_collided[i] = not successful