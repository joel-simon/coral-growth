cdef extern from 'ctri_intersection.h':
    int tr_tri_intersect3D (double *C1, double *P1, double *P2,
                            double *D1, double *Q1, double *Q2)
