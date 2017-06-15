# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True

from libc.math cimport sqrt
import numpy as np
cimport numpy as np

cpdef int spring_simulation(double[:,:] points, long[:,:] edges, int[:] fixed, \
                             int iters, double delta, double gravity, \
                             double damping, object view=False) except -1:
    """ Mass spring system with verlet integration.
    """
    cdef:
        int n_p = points.shape[0]
        int n_e = edges.shape[0]
        double delta2 = delta*delta
        int i_e, p_i, p_j
        double dx, dy, length, factor, correction_x, correction_y, new_x, new_y, x, y
    cdef:
        double[:, :] previous = np.copy(points)
        double[:] target = np.zeros(n_e)
        double[:,:] acceleration = np.zeros((n_p, 2))

    assert 0 <= damping <= 1

    for i_e in range(n_e):
        p_i = edges[i_e, 0]
        p_j = edges[i_e, 1]
        dx = points[p_j, 0] - points[p_i, 0]
        dy = points[p_j, 1] - points[p_i, 1]
        length = sqrt(dx*dx + dy*dy)
        target[i_e] = length

    for _ in range(iters):
        for i_e in range(n_e):
            # Resolve joint.
            p_i = edges[i_e, 0]
            p_j = edges[i_e, 1]

            dx = points[p_j, 0] - points[p_i, 0]
            dy = points[p_j, 1] - points[p_i, 1]


            length = sqrt(dx*dx + dy*dy)

            assert length > 0

            factor = (length - target[i_e]) / (length * 2.0)
            correction_x = dx * factor
            correction_y = dy * factor

            if not fixed[p_i]:
                points[p_i, 0] += correction_x
                points[p_i, 1] += correction_y

            if not fixed[p_j]:
                points[p_j, 0] -= correction_x
                points[p_j, 1] -= correction_y

        for i_p in range(n_p):
            if not fixed[i_p]:
                acceleration[i_p, 1] += gravity

                acceleration[i_p, 0] *= delta2
                acceleration[i_p, 1] *= delta2

                x = points[i_p, 0]
                y = points[i_p, 1]

                # https://www.saylor.org/site/wp-content/uploads/2011/06/MA221-6.1.pdf
                new_x = (2-damping)*x - (1-damping)*previous[i_p, 0] + acceleration[i_p, 0]
                new_y = (2-damping)*y - (1-damping)*previous[i_p, 1] + acceleration[i_p, 1]

                previous[i_p, 0] = x
                previous[i_p, 1] = y

                points[i_p, 0] = new_x
                points[i_p, 1] = new_y

                acceleration[i_p, 0] = 0
                acceleration[i_p, 1] = 1

        if view:
            view(points, edges)

    return 1
