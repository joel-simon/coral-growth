# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True
from __future__ import division
from libc.math cimport acos, M_PI, sqrt, fmin, fmax

cdef double TWOPI = 2.0 * M_PI

cdef bint intersect(float p0_x, float p0_y, float p1_x, float p1_y,
                    float p2_x, float p2_y, float p3_x, float p3_y):
    cdef float s1_x, s1_y, s2_x, s2_y, s, t, d
    s1_x = p1_x - p0_x
    s1_y = p1_y - p0_y
    s2_x = p3_x - p2_x
    s2_y = p3_y - p2_y

    d = -s2_x * s1_y + s1_x * s2_y

    # Parallel (Consider co-linear as not intersecting)
    if d == 0.0:
        return False

    s = (-s1_y * (p0_x - p2_x) + s1_x * (p0_y - p2_y)) / d
    t = ( s2_x * (p0_y - p2_y) - s2_y * (p0_x - p2_x)) / d

    if (s >= 0 and s <= 1 and t >= 0 and t <= 1):
        return True
        # // Collision detected
        # if (i_x != NULL)
        #     *i_x = p0_x + (t * s1_x);
        # if (i_y != NULL)
        #     *i_y = p0_y + (t * s1_y);
        # return 1;
    return False

cdef double shoelace(list point_list):
    cdef int n, i, j
    cdef double area
    """ The shoelace algorithm for polgon area """
    area = 0.0
    n = len(point_list)
    for i in range(n):
        j = (i + 1) % n
        area += (point_list[j][0] - point_list[i][0]) * \
                (point_list[j][1] + point_list[i][1])
    return area

cdef double polygon_area(list point_list):
    return abs(shoelace(point_list)) / 2.0

cdef double angle(double x1, double y1, double x2, double y2):
    cdef double l1, l2, cosx
    l1 = sqrt(x1*x1 + y1*y1)
    l2 = sqrt(x2*x2 + y2*y2)
    cosx = (x1*x2 + y1*y2) / (l1*l2)

    return acos(cosx)

cdef double angle_clockwise(double x1, double y1, double x2, double y2):
    cdef double a, det
    a = angle(x1, y1, x2, y2)
    det = x1*y2 - y1*x2
    if det < 0:
        return a
    else:
        return TWOPI - a

# def tri_area(v1, v2, v3):
#     # shoelace for case n=3
#     return .5*abs(v1.x*v2.y - v3.x*v2.y + v3.x*v1.y - v1.x*v3.y + v2.x*v3.y - v2.x*v1.y)

