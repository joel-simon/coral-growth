# cython: cdivision=True
# cython: linetrace=True

from __future__ import division
from libc.math cimport acos, M_PI, sqrt, fmin, fmax

cdef double pi2 = M_PI*2

cdef class Vec2D:
    def __init__(self, double x, double y):
        self.x = x
        self.y = y

    cdef inline Vec2D normed(Vec2D self):
        cdef double norm = self.norm()
        if norm == 0:
            return Vec2D(0, 0)
        else:
            return Vec2D(self.x/norm, self.y/norm)

    cdef inline double norm(Vec2D self):
        return sqrt(self.x*self.x + self.y*self.y)

    cdef inline double inner(Vec2D self, Vec2D other):
        return self.x*other.x + self.y*other.y

    cdef inline double angle(Vec2D self, Vec2D other):
        cdef double inn = (self.inner(other)) / (self.norm() * other.norm())
        return acos(fmin(1, fmax(-1, inn)))

    cdef inline double angle_clockwise(Vec2D self, Vec2D other):
        cdef double inner_angle = self.angle(other)
        cdef double determinant = self.x*other.y - self.y*other.x
        if determinant < 0:
            return inner_angle
        else:
            return pi2 - inner_angle

    # cpdef Vec2D copy(Vec2D self):
    #     return Vec2D(self.x, self.y)

    cdef inline Vec2D add(Vec2D self, Vec2D other):
        return Vec2D(self.x + other.x, self.y + other.y)

    cdef inline Vec2D sub(Vec2D self, Vec2D other):
        return Vec2D(self.x - other.x, self.y - other.y)

    cdef inline Vec2D addf(Vec2D self, double v):
        return Vec2D(self.x + v, self.y + v)

    cdef inline Vec2D subf(Vec2D self, double v):
        return Vec2D(self.x - v, self.y - v)

    cdef inline Vec2D multf(Vec2D self, double v):
        return Vec2D(self.x * v, self.y * v)

    cdef inline Vec2D divf(Vec2D self, double v):
        return Vec2D(self.x / v, self.y / v)


    def __str__(Vec2D self):
        return "V2D(%f, %f)" % (self.x, self.y)

    def __add__(Vec2D self, Vec2D other):
        return Vec2D(self.x + other.x, self.y+other.y)

    def __sub__(Vec2D self, Vec2D other):
        return Vec2D(self.x - other.x, self.y - other.y)

    def __mul__(Vec2D self, other):
        # Dot product. if other is Vec2D.
        if type(other) == type(self):
            return self.inner(other)
        else:
            return Vec2D(self.x * other, self.y * other)

    def __rmul__(Vec2D self, other):
        """ Called if 4*self for instance """
        return self.__mul__(other)

    def __truediv__(Vec2D self, double other):
        return Vec2D(self.x / other, self.y / other)

    def __iter__(Vec2D self):
        # Useful for x, y = V
        yield self.x
        yield self.y

    # def __rdiv__(self, other):
    #     return Vec2D(self.x / other, self.y / other)

