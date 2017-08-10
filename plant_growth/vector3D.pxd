# cdef struct Vect:
#     double x
#     double y
#     double z

# cdef inline Vect vadd(Vect a, Vect b)
# cdef inline Vect vsub(Vect a, Vect b)
# cdef inline Vect vmultf(Vect a, double f)
# cdef inline Vect vdivf(Vect a, double f) except *
# cdef inline double dot(Vect a, Vect b)
# cdef inline Vect cross(Vect a, Vect b)
# cdef inline double vdist(Vect a, Vect b)

# cdef inline void iset(Vect *a, Vect *b)
# cdef inline void inormalized(Vect *a)
# ctypedef double[3] Vect

cdef inline void vadd(double target[3], double a[3], double b[3])
cdef inline void vsub(double target[3], double a[3], double b[3])
cdef inline void vmultf(double target[3], double a[3], double f)
cdef inline void vdivf(double target[3], double a[3], double f) except *
cdef inline void cross(double target[3], double a[3], double b[3])
cdef inline void vset(double target[3], double a[3])
cdef inline void inormalized(double a[3])
cdef inline double dot(double a[3], double b[3])
cdef inline double vdist(double a[3], double b[3])
cdef double vangle(double a[3], double b[3])
