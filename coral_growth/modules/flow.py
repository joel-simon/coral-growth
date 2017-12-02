# cimport numpy as np
import numpy as np
import math
from .fluid_solver3D import py_dens_step, py_vel_step
import time

class Flow:
    def __init__(self, coral, nx, ny, nz, blocksize):
        self.coral = coral
        self.nx = nx
        self.ny = ny
        self.nz = nz
        self.blocksize = blocksize
        self.polyp_pos = coral.polyp_pos

        self.size = (nx+2) * (ny+2) * (nz+2)
        self.grid = np.zeros(self.size, dtype='i', order='C')
        self.u = np.zeros(self.size, dtype='float32', order='C')
        self.v = np.zeros(self.size, dtype='float32', order='C')
        self.w = np.zeros(self.size, dtype='float32', order='C')
        self.dens = np.zeros(self.size, dtype='float32', order='C')
        self.u_prev = np.zeros(self.size, dtype='float32', order='C')
        self.v_prev = np.zeros(self.size, dtype='float32', order='C')
        self.w_prev = np.zeros(self.size, dtype='float32', order='C')
        self.dens_prev = np.zeros(self.size, dtype='float32', order='C')

        self.dt = 0.2 # time delta
        self.diff = 0.0 # diffuse
        self.visc = 0.0 # viscosity
        self.force = 5.10  # added on keypress on an axis
        # self.source = 200.0 # density
        # self.source_alpha =  0.05 #for displaying density

    def IX(self, i, j, k):
        idx = ((i)+(self.nz+2)*(j) + (self.nz+2)*(self.ny+2)*(k))
        assert (idx >= 0 and idx < self.size), idx
        return idx

    def update(self, iters):
        wx = (self.blocksize * self.nx) / 2.0
        wy = (self.blocksize * self.ny) / 2.0
        wz = (self.blocksize * self.nz) / 2.0

        # for i in range(self.coral.n_polyps):
        #     p = self.polyp_pos[i]
        #     x = int(min(self.nx, max(0, (p[0]+wx)//self.blocksize)))
        #     y = int(min(self.nx, max(0, (p[1]+wy)//self.blocksize)))
        #     z = int(min(self.nx, max(0, (p[2]+wz)//self.blocksize)))
        #     self.grid[self.IX(x, y, z)] = 1
        # r = 5
        for x in range(self.ny):
            for y in range(self.ny):
                for z in range(self.ny):
                    if x > 5 and x < 8:
                        if y > 4 and y < 10 and z > 4 and z < 10:
                            self.grid[self.IX(x, y, z)] = 1
        #             if math.sqrt((x-self.nx//2)**2 + (y-self.ny//2)**2 + (z-self.nz//2)**2) < r:
        #                 self.grid[self.IX(x, y, z)] = 1

        total = 0#time.time()
        for _ in range(iters):

            for y in range(self.ny):
                for z in range(self.ny):
                    self.u[self.IX(1, y, z)] += self.force
            t1 = time.time()
            py_vel_step( self.nx, self.ny, self.nz, self.u, self.v, self.w, \
                      self.u_prev, self.v_prev, self.w_prev, self.visc, self.dt, \
                      self.grid)
            py_dens_step( self.nx, self.ny, self.nz, self.dens, self.dens_prev, \
                       self.u, self.v, self.w, self.diff, self.dt, self.grid)
            print(self.dens.min(), self.dens.max())

            total += time.time() - t1
        print(total)
