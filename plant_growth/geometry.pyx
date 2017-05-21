# from plant_growth.vec2D cimport Vec2D
# from __future__ import
cdef bint intersect(float p0_x, float p0_y, float p1_x, float p1_y,
                    float p2_x, float p2_y, float p3_x, float p3_y):
    cdef float s1_x, s1_y, s2_x, s2_y, s, t, d
    s1_x = p1_x - p0_x
    s1_y = p1_y - p0_y
    s2_x = p3_x - p2_x
    s2_y = p3_y - p2_y

    d = -s2_x * s1_y + s1_x * s2_y

    # Parallel (Consider co-linear as not intersecting)
    if d == 0.0:
        return False

    s = (-s1_y * (p0_x - p2_x) + s1_x * (p0_y - p2_y)) / d
    t = ( s2_x * (p0_y - p2_y) - s2_y * (p0_x - p2_x)) / d

    if (s >= 0 and s <= 1 and t >= 0 and t <= 1):
        return True
        # // Collision detected
        # if (i_x != NULL)
        #     *i_x = p0_x + (t * s1_x);
        # if (i_y != NULL)
        #     *i_y = p0_y + (t * s1_y);
        # return 1;
    return False

cdef double shoelace(list point_list):
    cdef int n, i, j
    cdef double area
    """ The shoelace algorithm for polgon area """
    area = 0.0
    n = len(point_list)
    for i in range(n):
        j = (i + 1) % n
        area += (point_list[j][0] - point_list[i][0]) * \
                (point_list[j][1] + point_list[i][1])
    return area

cdef double polygon_area(list point_list):
    return abs(shoelace(point_list)) / 2.0

# def tri_area(v1, v2, v3):
#     # shoelace for case n=3
#     return .5*abs(v1.x*v2.y - v3.x*v2.y + v3.x*v1.y - v1.x*v3.y + v2.x*v3.y - v2.x*v1.y)


# def segment_intersect(a, b):
#     A, B = a
#     C, D = b
#     return intersect(A, B, C, D)

# cpdef bint point_in_polygon(poly, Vec2D p):
#     cdef int nvert = len(poly)
#     cdef int i, j
#     cdef bint res = 0
#     for (i = 0, j = nvert-1; i < nvert; j = i++):

#         if ( ((poly[i].y>p.y) != (poly[j].y>p.y)) and
#             (p.x < (vertx[j]-vertx[i]) * (p.y-poly[i].y) / (poly[j].y-poly[i].y) + vertx[i]))
#                 res = not res
#     return res

# def point_inside_polygon(x, y, poly):
#     n = len(poly)
#     inside =False

#     p1x,p1y = poly[0]
#     for i in range(n+1):
#         p2x,p2y = poly[i % n]
#         if y > min(p1y,p2y):
#             if y <= max(p1y,p2y):
#                 if x <= max(p1x,p2x):
#                     if p1y != p2y:
#                         xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
#                     if p1x == p2x or x <= xinters:
#                         inside = not inside
#         p1x,p1y = p2x,p2y

#     return inside

# def lineIntersection(p1, p2, p3, p4):
#     s = ((p4.x - p3.x) * (p1.y - p3.y) - (p4.y - p3.y) * (p1.x - p3.x)) / ((p4.y - p3.y) * (p2.x - p1.x) - (p4.x - p3.x) * (p2.y - p1.y))
#     return Vec2D(p1.x + s * (p2.x - p1.x), p1.y + s * (p2.y - p1.y))
