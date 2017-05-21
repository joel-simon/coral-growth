# cython: cdivision=True

cdef class Vec2D:
    cdef public double x, y
    cpdef Vec2D normed(Vec2D self)
    cpdef double norm(Vec2D self)
    cpdef double inner(Vec2D self, Vec2D other)
    cpdef Vec2D cross(Vec2D self, Vec2D other)
    cpdef double angle(Vec2D self, Vec2D other)
    cpdef double angle_clockwise(Vec2D self, Vec2D other)
    cpdef Vec2D copy(Vec2D self)

    cdef Vec2D add(Vec2D self, Vec2D other)
    cdef Vec2D sub(Vec2D self, Vec2D other)

    cdef Vec2D addf(Vec2D self, double v)
    cdef Vec2D subf(Vec2D self, double v)
    cdef Vec2D multf(Vec2D self, double v)
    cdef Vec2D divf(Vec2D self, double v)

    # cpdef void iadd(Vec2D self, Vec2D other)
    # cpdef void isub(Vec2D self, Vec2D other)

    # cpdef void imultf(Vec2D self, double x)
    # cpdef void idivf(Vec2D self, double x)
