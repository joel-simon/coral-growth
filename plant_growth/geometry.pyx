from plant_growth.vec2D cimport Vec2D

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

# cpdef bint point_in_polygon(poly, Vec2D p):
#     cdef int nvert = len(poly)
#     cdef int i, j
#     cdef bint res = 0
#     for (i = 0, j = nvert-1; i < nvert; j = i++):

#         if ( ((poly[i].y>p.y) != (poly[j].y>p.y)) and
#             (p.x < (vertx[j]-vertx[i]) * (p.y-poly[i].y) / (poly[j].y-poly[i].y) + vertx[i]))
#                 res = not res
#     return res
def point_inside_polygon(x, y, poly):
    n = len(poly)
    inside =False

    p1x,p1y = poly[0]
    for i in range(n+1):
        p2x,p2y = poly[i % n]
        if y > min(p1y,p2y):
            if y <= max(p1y,p2y):
                if x <= max(p1x,p2x):
                    if p1y != p2y:
                        xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x,p1y = p2x,p2y

    return inside

def lineIntersection(p1, p2, p3, p4):
    s = ((p4.x - p3.x) * (p1.y - p3.y) - (p4.y - p3.y) * (p1.x - p3.x)) / ((p4.y - p3.y) * (p2.x - p1.x) - (p4.x - p3.x) * (p2.y - p1.y))
    return Vec2D(p1.x + s * (p2.x - p1.x), p1.y + s * (p2.y - p1.y))


def shoelace(point_list):
    """ The shoelace algorithm for polgon area """
    area = 0.0
    n = len(point_list)
    for i in range(n):
        j = (i + 1) % n
        area += (point_list[j][0] - point_list[i][0]) * \
                (point_list[j][1] + point_list[i][1])
    return area

def polygon_area(point_list):
    return abs(shoelace(point_list)) / 2
