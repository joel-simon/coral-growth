# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True

from coral_growth.growth_form cimport GrowthForm

cdef inline bint pnt_in_tri(double[:] p, double[:] p0, double[:] p1, double[:] p2) nogil:
    # https://stackoverflow.com/questions/2049582/how-to-determine-if-a-point-is-in-a-2d-triangle
    cdef double s = p0[1] * p2[0] - p0[0] * p2[1] + (p2[1] - p0[1]) * p[0] + \
                                                    (p0[0] - p2[0]) * p[1]
    cdef double t = p0[0] * p1[1] - p0[1] * p1[0] + (p0[1] - p1[1]) * p[0] + \
                                                    (p1[0] - p0[0]) * p[1]

    if (s < 0) != (t < 0):
        return False

    cdef double A = -p1[1] * p2[0] + p0[1] * (p2[0] - p1[0]) + p0[0] * \
                                     (p1[1] - p2[1]) + p1[0] * p2[1]

    if A < 0.0:
        s = -s
        t = -t
        A = -A

    return s > 0 and t > 0 and (s + t) <= A

cpdef void calculate_light(GrowthForm) except *
