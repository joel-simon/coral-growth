import math
class Vector(object):
    __slots__ = ['x', 'y']
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def normed(self):
        norm = self.norm()
        if norm == 0:
            return Vector(0, 0)
        return Vector(self.x/norm, self.y/norm)

    def norm(self):
        return math.sqrt(self.x**2 + self.y**2)

    def inner(self, other):
        return self.x*other.x + self.y*other.y

    def cross(self, other):
        return Vector(other.y - self.y , -(other.x - self.x))

    def angle(self, other):
        return math.acos((self*other) / (self.norm() * other.norm()))

    def copy(self):
        return Vector(self.x, self.y)

    def __str__(self):
        return "[%f, %f]" % (self.x, self.y)

    def __add__(self, other):
        return Vector(self.x + other.x, self.y+other.y)

    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        # Dot product. if other is vector.
        if type(other) == type(self):
            return self.inner(other)
        else:
            return Vector(self.x * other, self.y * other)

    def __rmul__(self, other):
        """ Called if 4*self for instance """
        return self.__mul__(other)

    def __truediv__(self, other):
        return Vector(self.x / other, self.y / other)

    def __iter__(self):
        yield self.x
        yield self.y

    # def __rdiv__(self, other):
    #     return Vector(self.x / other, self.y / other)

