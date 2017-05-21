# cython: cdivision=True

cdef class Vec2D:
    cdef public double x, y
    cdef inline Vec2D normed(Vec2D self)
    cdef inline double norm(Vec2D self)
    cdef inline double inner(Vec2D self, Vec2D other)
    # inline cdef Vec2D cross(Vec2D self, Vec2D other)
    cdef inline double angle(Vec2D self, Vec2D other)
    cdef inline double angle_clockwise(Vec2D self, Vec2D other)
    # inline cdef Vec2D copy(Vec2D self)

    cdef inline Vec2D add(Vec2D self, Vec2D other)
    cdef inline Vec2D sub(Vec2D self, Vec2D other)

    cdef inline Vec2D addf(Vec2D self, double v)
    cdef inline Vec2D subf(Vec2D self, double v)
    cdef inline Vec2D multf(Vec2D self, double v)
    cdef inline Vec2D divf(Vec2D self, double v)

    # cpdef void iadd(Vec2D self, Vec2D other)
    # cpdef void isub(Vec2D self, Vec2D other)

    # cpdef void imultf(Vec2D self, double x)
    # cpdef void idivf(Vec2D self, double x)
