# cdef extern from 'cfluid_solver3d.c':
#     void dens_step( int M, int N, int O, float * x, float * x0, float * u,
#                      float * v, float * w, float diff, float dt, int * bounds)

#     void vel_step( int M, int N, int O, float * u, float * v,  float * w,
#                   float * u0, float * v0, float * w0, float visc, float dt,
#                   int * bounds)



# cpdef void py_dens_step(int M, int N, int O, float[::1] x, float[::1] x0,
#                         float[::1] u, float[::1] v, float[::1] w, float diff,
#                         float dt, int[::1] bounds) except *

# cpdef void py_vel_step( int M, int N, int O, float[::1] u, float[::1] v,
#                         float[::1] w, float[::1] u0, float[::1] v0,
#                         float[::1] w0, float visc, float dt, int[::1] bounds ) except *
