# cpdef void py_dens_step(int M, int N, int O, float[::1] x, float[::1] x0,
#                         float[::1] u, float[::1] v, float[::1] w, float diff,
#                         float dt, int[::1] bounds) except *:
#     dens_step(M, N, O, &x[0], &x0[0], &u[0], &v[0], &w[0], diff, dt, &bounds[0])

# cpdef void py_vel_step( int M, int N, int O, float[::1] u, float[::1] v,
#                         float[::1] w, float[::1] u0, float[::1] v0,
#                         float[::1] w0, float visc, float dt, int[::1] bounds ) except *:
#     vel_step( M, N, O, &u[0], &v[0], &w[0], &u0[0],  &v0[0],  &w0[0], visc, dt, &bounds[0])


