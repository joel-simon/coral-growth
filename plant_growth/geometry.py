from plant_growth.vec2D import Vec2D

from recordclass import recordclass

Point = recordclass('Point', ['x', 'y'])

def ccw(A, B, C):
    return (C.y-A.y) * (B.x-A.x) > (B.y-A.y) * (C.x-A.x)

# Return true if line segments AB and CD intersect
def intersect(A, B, C, D):
    return ccw(A,C,D) != ccw(B,C,D) and ccw(A,B,C) != ccw(A,B,D)

def segment_intersect(a, b):
    A, B = a
    C, D = b
    return intersect(A, B, C, D)

def point_in_polygon(pt, poly, inf=9999):
    result = False
    for i in range(len(poly)-1):
        if intersect(Vec2D(poly[i].x, poly[i].y), Vec2D( poly[i+1].x, poly[i+1].y), Vec2D(pt.x, pt.y), Vec2D(inf, pt.y)):
            result = not result
    if intersect(Vec2D(poly[-1].x, poly[-1].y), Vec2D(poly[0].x, poly[0].y), Vec2D(pt.x, pt.y), Vec2D(inf, pt.y)):
        result = not result
    return result

def lineIntersection (p1, p2, p3, p4):
    s = ((p4.x - p3.x) * (p1.y - p3.y) - (p4.y - p3.y) * (p1.x - p3.x)) / ((p4.y - p3.y) * (p2.x - p1.x) - (p4.x - p3.x) * (p2.y - p1.y))
    return Vec2D(p1.x + s * (p2.x - p1.x), p1.y + s * (p2.y - p1.y))


def shoelace(point_list):
    """ The shoelace algorithm for polgon area """
    area = 0.0
    n = len(point_list)
    for i in range(n):
        j = (i + 1) % n
        area += (point_list[j].x - point_list[i].x) * \
                (point_list[j].y + point_list[i].y)
    return area

def polygon_area(point_list):
    return abs(shoelace(point_list)) / 2
