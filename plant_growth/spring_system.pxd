cpdef int spring_simulation(double[:,:] points, long[:,:] edges, int[:] fixed, \
                             int iters, double delta, double gravity, \
                             double damping, double[:] deformation,\
                             object view=*) except -1