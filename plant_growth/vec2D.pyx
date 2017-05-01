from libc.math cimport acos, M_PI, sqrt, fmin, fmax

cdef float pi2 = M_PI*2

cdef class Vec2D:
    cdef public float x, y
    def __init__(self, float x, float y):
        self.x = x
        self.y = y

    cpdef Vec2D normed(Vec2D self):
        cdef float norm = self.norm()
        if norm == 0:
            return Vec2D(0, 0)
        else:
            return Vec2D(self.x/norm, self.y/norm)

    cpdef float norm(Vec2D self):
        return sqrt(self.x*self.x + self.y*self.y)

    cpdef float inner(Vec2D self, Vec2D other):
        return self.x*other.x + self.y*other.y

    cpdef Vec2D cross(Vec2D self, Vec2D other):
        return Vec2D(other.y - self.y , -(other.x - self.x))

    cpdef float angle(Vec2D self, Vec2D other):
        cdef float inn = (self.inner(other)) / (self.norm() * other.norm())
        return acos(fmin(1, fmax(-1, inn)))

    cpdef float angle_clockwise(Vec2D self, Vec2D other):
        cdef float inner_angle = self.angle(other)
        cdef float determinant = self.x*other.y - self.y*other.x
        if determinant < 0:
            return inner_angle
        else:
            return pi2 - inner_angle

    cpdef Vec2D copy(self):
        return Vec2D(self.x, self.y)

    def __str__(self):
        return "V2D(%f, %f)" % (self.x, self.y)

    def __add__(self, other):
        return Vec2D(self.x + other.x, self.y+other.y)

    def __sub__(self, other):
        return Vec2D(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        # Dot product. if other is Vec2D.
        if type(other) == type(self):
            return self.inner(other)
        else:
            return Vec2D(self.x * other, self.y * other)

    def __rmul__(self, other):
        """ Called if 4*self for instance """
        return self.__mul__(other)

    def __truediv__(self, float other):
        return Vec2D(self.x / other, self.y / other)

    def __iter__(self):
        yield self.x
        yield self.y

    # def __rdiv__(self, other):
    #     return Vec2D(self.x / other, self.y / other)

