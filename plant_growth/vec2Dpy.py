import math
pi2 = math.pi *2

class Vec2D(object):
    __slots__ = ['x', 'y']
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def normed(self):
        norm = self.norm()
        if norm == 0:
            return Vec2D(0, 0)
        return Vec2D(self.x/norm, self.y/norm)

    def norm(self):
        return math.sqrt(self.x**2 + self.y**2)

    def inner(self, other):
        return self.x*other.x + self.y*other.y

    def cross(self, other):
        return Vec2D(other.y - self.y , -(other.x - self.x))

    def angle(self, other):
        inner = (self*other) / (self.norm() * other.norm())
        return math.acos(min(1, max(-1, inner)))

    def angle_clockwise(self, other):
        inner_angle = self.angle(other)
        determinant = self.x*other.y - self.y*other.x
        if determinant < 0:
            return inner_angle
        else:
            return pi2 - inner_angle

    def copy(self):
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

    def __truediv__(self, other):
        return Vec2D(self.x / other, self.y / other)

    def __iter__(self):
        yield self.x
        yield self.y

    # def __rdiv__(self, other):
    #     return Vec2D(self.x / other, self.y / other)

