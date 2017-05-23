cdef bint intersect(float p0_x, float p0_y, float p1_x, float p1_y,
                    float p2_x, float p2_y, float p3_x, float p3_y)

cdef double shoelace(list point_list)

cdef double polygon_area(list point_list)

cdef double angle(double x1, double y1, double x2, double y2)

cdef double angle_clockwise(double x1, double y1, double x2, double y2)
