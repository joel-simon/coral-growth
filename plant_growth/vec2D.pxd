# cython: cdivision=True

cdef class Vec2D:
    cdef public float x, y
    cpdef Vec2D normed(Vec2D self)
    cpdef float norm(Vec2D self)
    cpdef float inner(Vec2D self, Vec2D other)
    cpdef Vec2D cross(Vec2D self, Vec2D other)
    cpdef float angle(Vec2D self, Vec2D other)
    cpdef float angle_clockwise(Vec2D self, Vec2D other)
    cpdef Vec2D copy(Vec2D self)
