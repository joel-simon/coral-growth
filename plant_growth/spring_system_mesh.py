# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True

# from libc.math cimport sqrt
# import numpy as np
# cimport numpy as np

# cpdef int spring_simulation_mesh(mesh
#                              int iters, double delta, double gravity, \
#                              double damping, double[:] deformation,\
#                              object view=False) except -1:

from math import sqrt, isnan
import numpy as np
def spring_simulation_mesh(mesh, iters, delta, gravity, damping, view=None):
    """ Mass spring system with verlet integration.
    """
    # cdef:
    #     double delta2 = delta*delta
    #     int i_e, p_i, p_j
    #     double dx, dy, length, factor, correction_x, correction_y, new_x, new_y, x, y
    delta2 = delta*delta
    assert 0 <= damping <= 1

    for edge in mesh.edges:
        edge.target = edge.length()
        # print('target', edge.target)

    for _ in range(iters):
        print('#'*80)
        for edge in mesh.edges:
            v1, v2 = edge.verts()
            dx = v1.x - v2.x
            dy = v1.y - v2.y

            length = sqrt(dx*dx + dy*dy)

            print(length)

            if length == 0:
                raise ValueError('Zero edge length.')

            factor = (length - edge.target) / (length * 2.0)

            assert not isnan(factor), (length, edge.target, dx, dy)

            correction_x = dx * factor
            correction_y = dy * factor

            if not v1.fixed:
                v1.x += correction_x
                v1.y += correction_y

            if not v2.fixed:
                v2.x -= correction_x
                v2.y -= correction_y

        for vert in mesh.verts:
            if not vert.fixed:
                vert.accel_y += gravity

                vert.accel_x *= delta2
                vert.accel_y *= delta2

                x = vert.x
                y = vert.y

                # https://www.saylor.org/site/wp-content/uploads/2011/06/MA221-6.1.pdf
                new_x = (2-damping)*x - (1-damping)*vert.prev_x + vert.accel_x
                new_y = (2-damping)*y - (1-damping)*vert.prev_y + vert.accel_y

                assert not isnan(new_x), (new_x, vert.prev_x, vert.accel_x)
                assert not isnan(new_y), (new_y, vert.prev_y, vert.accel_y)

                vert.prev_x = x
                vert.prev_y = y

                vert.x = new_x
                vert.y = new_y

                vert.accel_x = 0
                vert.accel_y = 1

        if view:
            view(points, edges, deformation)

    return 1
