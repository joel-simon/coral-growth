from plant_growth.vector3D cimport vset, vsub
from plant_growth.ctri_intersection cimport tr_tri_intersect3D

cdef int tri_tri_intersection(double *P1, double *P2, double *P3,
                              double *Q1, double *Q2, double *Q3) except -1:
    cdef size_t i
    cdef double l1[3]
    cdef double l2[3]

    cdef double l3[3]
    cdef double l4[3]

    for i in range(3):
        l1[i] = P2[i] - P1[i]
        l2[i] = P3[i] - P1[i]

        l3[i] = Q2[i] - Q1[i]
        l4[i] = Q3[i] - Q1[i]

    return <bint>tr_tri_intersect3D(P1, l1, l2, Q1, l3, l4)

def py_tri_tri_intersection(a, b, c, d, e, f):
    pass
    # cdef Vect V0, V1, V2, U0, U1 ,U2
    # V0.x = a[0]
    # V0.y = a[1]
    # V0.z = a[2]

    # V1.x = b[0]
    # V1.y = b[1]
    # V1.z = b[2]

    # V2.x = c[0]
    # V2.y = c[1]
    # V2.z = c[2]

    # U0.x = d[0]
    # U0.y = d[1]
    # U0.z = d[2]

    # V1.x = e[0]
    # V1.y = e[1]
    # V1.z = e[2]

    # V2.x = f[0]
    # V2.y = f[1]
    # V2.z = f[2]

    # for i in range(3):
    #     V1[i] -= V0[i]
    #     V2[i] -= V0[i]

    #     U1[i] -= U0[i]
    #     U2[i] -= U0[i]

    # cdef double a[3]
    # cdef double b[3]
    # cdef double c[3]
    # cdef double d[3]
    # cdef double e[3]
    # cdef double f[3]

    # a[:] = [<double>V0[0], <double>V0[1], <double>V0[2]]
    # b[:] = [<double>V1[0], <double>V1[1], <double>V1[2]]
    # c[:] = [<double>V2[0], <double>V2[1], <double>V2[2]]

    # d[:] = [<double>U0[0], <double>U0[1], <double>U0[2]]
    # e[:] = [<double>U1[0], <double>U1[1], <double>U1[2]]
    # f[:] = [<double>U2[0], <double>U2[1], <double>U2[2]]

    # return tri_tri_intersection_test_3d(a, b, c, d, e, f, coplanar, source, target)
    # return tri_tri_intersection(&V0, &V1, &V2, &U0, &U1, &U2)

