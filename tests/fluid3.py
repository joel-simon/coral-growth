# 3D Lattice Boltzmann (BGK) model of a fluid.
## D3Q19 model. At each timestep, particle densities propagate
## outwards in the directions indicated in the figure. An
## equivalent 'equilibrium' density is found, and the densities
## relax towards that state, in a proportion governed by omega.
##               Iain Haslam, March 2006.
import random
import numpy as np
import time
import sys

t1 = 1/3.0
t2 = 1/18.0
t3 = 1/36.0
deltaU = 1e-6

class FluidSimulation(object):
    def __init__(self, nx, ny, nz, omega=1, density=1):
        self.nx = nx
        self.ny = ny
        self.nz = nz
        self.omega = omega
        self.density = density

        self.F = np.zeros((19,nx,ny,nz), dtype=float)
        self.FEQ = np.zeros((19,nx,ny,nz), dtype=float)
        self.T = np.zeros((19,nx,ny,nz), dtype=float)
        self.F[:,:,:,:] += self.density/19.0
        self.FEQ[:,:,:,:] += self.density/19.0

        #Create the scenery.
        self.BOUND = np.zeros((nx,ny,nz), dtype=float)
        self.BOUNDi = np.zeros((nx,ny,nz), dtype=float)
        self.BOUNDi += 1#ones

        self.BOUND [:,0,:] = 1.0
        self.BOUNDi[:,0,:] = 0.0
        self.BOUND [:,:,0] = 1.0
        self.BOUNDi[:,:,0] = 0.0

    def run(self, steps):
        F = self.F
        FEQ = self.FEQ
        T = self.T

        for _ in range(steps):
            # Streaming step
            T[:] = F
            #nearest-neighbours
            F[1,:,:,0]   = T[1,:,:,-1]
            F[1,:,:,1:]  = T[1,:,:,:-1]
            F[2,:,:,:-1] = T[2,:,:,1:]
            F[2,:,:,-1]  = T[2,:,:,0]
            F[3,:,0,:]   = T[3,:,-1,:]
            F[3,:,1:,:]  = T[3,:,:-1,:]
            F[4,:,:-1,:] = T[4,:,1:,:]
            F[4,:,-1,:]  = T[4,:,0,:]
            F[5,0,:,:]   = T[5,-1,:,:]
            F[5,1:,:,:]  = T[5,:-1,:,:]
            F[6,:-1,:,:] = T[6,1:,:,:]
            F[6,-1,:,:]  = T[6,0,:,:]

            #next-nearest neighbours
            F[7,0 ,0 ,:] = T[7,-1 , -1,:]
            F[7,0 ,1:,:] = T[7,-1 ,:-1,:]
            F[7,1:,0 ,:] = T[7,:-1, -1,:]
            F[7,1:,1:,:] = T[7,:-1,:-1,:]

            F[8,0 ,:-1,:] = T[8,-1 ,1:,:]
            F[8,0 , -1,:] = T[8,-1 ,0 ,:]
            F[8,1:,:-1,:] = T[8,:-1,1:,:]
            F[8,1:, -1,:] = T[8,:-1,0 ,:]

            F[9,:-1,0 ,:] = T[9,1:, -1,:]
            F[9,:-1,1:,:] = T[9,1:,:-1,:]
            F[9,-1 ,0 ,:] = T[9,0 ,  0,:]
            F[9,-1 ,1:,:] = T[9,0 ,:-1,:]

            F[10,:-1,:-1,:] = T[10,1:,1:,:]
            F[10,:-1, -1,:] = T[10,1:,0 ,:]
            F[10,-1 ,:-1,:] = T[10,0 ,1:,:]
            F[10,-1 , -1,:] = T[10,0 ,0 ,:]

            F[11,0 ,:,0 ] = T[11,0  ,:, -1]
            F[11,0 ,:,1:] = T[11,0  ,:,:-1]
            F[11,1:,:,0 ] = T[11,:-1,:, -1]
            F[11,1:,:,1:] = T[11,:-1,:,:-1]

            F[12,0 ,:,:-1] = T[12, -1,:,1:]
            F[12,0 ,:, -1] = T[12, -1,:,0 ]
            F[12,1:,:,:-1] = T[12,:-1,:,1:]
            F[12,1:,:, -1] = T[12,:-1,:,0 ]

            F[13,:-1,:,0 ] = T[13,1:,:, -1]
            F[13,:-1,:,1:] = T[13,1:,:,:-1]
            F[13, -1,:,0 ] = T[13,0 ,:, -1]
            F[13, -1,:,1:] = T[13,0 ,:,:-1]

            F[14,:-1,:,:-1] = T[14,1:,:,1:]
            F[14,:-1,:, -1] = T[14,1:,:,0 ]
            F[14,-1 ,:,:-1] = T[14,0 ,:,1:]
            F[14,-1 ,:, -1] = T[14,0 ,:,0 ]

            F[15,:,0 ,0 ] = T[15,:, -1, -1]
            F[15,:,0 ,1:] = T[15,:, -1,:-1]
            F[15,:,1:,0 ] = T[15,:,:-1, -1]
            F[15,:,1:,1:] = T[15,:,:-1,:-1]

            F[16,:,0 ,:-1] = T[16,:, -1,1:]
            F[16,:,0 , -1] = T[16,:, -1,0 ]
            F[16,:,1:,:-1] = T[16,:,:-1,1:]
            F[16,:,1:, -1] = T[16,:,:-1,0 ]

            F[17,:,:-1,0 ] = T[17,:,1:, -1]
            F[17,:,:-1,1:] = T[17,:,1:,:-1]
            F[17,:, -1,0 ] = T[17,:,0 , -1]
            F[17,:, -1,1:] = T[17,:,0 ,:-1]

            F[18,:,:-1,:-1] = T[18,:,1:,1:]
            F[18,:,:-1, -1] = T[18,:,1:,0 ]
            F[18,:,-1 ,:-1] = T[18,:,0 ,1:]
            F[18,:,-1 , -1] = T[18,:,0 ,0 ]

            #Densities bouncing back at next timestep
            BB = np.zeros(F.shape, dtype=float)
            T[:] = F

            T[1:,:,:,:] *= self.BOUND[np.newaxis,:,:,:]
            BB[2 ,:,:,:] += T[1 ,:,:,:]
            BB[1 ,:,:,:] += T[2 ,:,:,:]
            BB[4 ,:,:,:] += T[3 ,:,:,:]
            BB[3 ,:,:,:] += T[4 ,:,:,:]
            BB[6 ,:,:,:] += T[5 ,:,:,:]
            BB[5 ,:,:,:] += T[6 ,:,:,:]
            BB[10,:,:,:] += T[7 ,:,:,:]
            BB[9 ,:,:,:] += T[8 ,:,:,:]
            BB[8 ,:,:,:] += T[9 ,:,:,:]
            BB[7 ,:,:,:] += T[10,:,:,:]
            BB[14,:,:,:] += T[11,:,:,:]
            BB[13,:,:,:] += T[12,:,:,:]
            BB[12,:,:,:] += T[13,:,:,:]
            BB[11,:,:,:] += T[14,:,:,:]
            BB[18,:,:,:] += T[15,:,:,:]
            BB[17,:,:,:] += T[16,:,:,:]
            BB[16,:,:,:] += T[17,:,:,:]
            BB[15,:,:,:] += T[18,:,:,:]

            # Relax calculate equilibrium state (FEQ) with equivalent speed and density to F
            DENSITY = np.add.reduce(F)

            T1 = F[5,:,:,:]+F[7,:,:,:]+F[8,:,:,:]+F[11,:,:,:]+F[12,:,:,:]
            T2 = F[6,:,:,:]+F[9,:,:,:]+F[10,:,:,:]+F[13,:,:,:]+F[14,:,:,:]
            UX = (T1-T2)/DENSITY

            T1 = F[3,:,:,:]+F[7,:,:,:]+F[9,:,:,:]+F[15,:,:,:]+F[16,:,:,:]
            T2 = F[4,:,:,:]+F[8,:,:,:]+F[10,:,:,:]+F[17,:,:,:]+F[18,:,:,:]
            UY = (T1-T2)/DENSITY

            T1 = F[1,:,:,:]+F[11,:,:,:]+F[13,:,:,:]+F[15,:,:,:]+F[17,:,:,:]
            T2 = F[2,:,:,:]+F[12,:,:,:]+F[14,:,:,:]+F[16,:,:,:]+F[18,:,:,:]
            UZ = (T1-T2)/DENSITY

            UX[0,:,:] += deltaU #Increase inlet pressure

            #Set bourderies to zero.
            UX[:,:,:] *= self.BOUNDi
            UY[:,:,:] *= self.BOUNDi
            UZ[:,:,:] *= self.BOUNDi
            DENSITY[:,:,:] *= self.BOUNDi

            U_SQU = UX*UX + UY*UY + UZ*UZ
            U8 = UX+UY
            U9 = UX-UY
            U10 = -UX+UY
            U11 = -U8
            U12 = UX+UZ
            U13 = UX-UZ
            U14 = -U13
            U15 = -U12
            U16 = UY+UZ
            U17 = UY-UZ
            U18 = -U17
            U19 = -U16

            # Calculate equilibrium distribution: stationary
            FEQ[0,:,:,:] = (t1*DENSITY)*(1.0-3.0*U_SQU/2.0)
            # nearest-neighbours
            T1 = 3.0/2.0*U_SQU
            tDENSITY = t2*DENSITY
            FEQ[1,:,:,:]=tDENSITY*(1.0 + 3.0*UZ + 9.0/2.0*UZ**2 - T1)
            FEQ[2,:,:,:]=tDENSITY*(1.0 - 3.0*UZ + 9.0/2.0*UZ**2 - T1)
            FEQ[3,:,:,:]=tDENSITY*(1.0 + 3.0*UY + 9.0/2.0*UY**2 - T1)
            FEQ[4,:,:,:]=tDENSITY*(1.0 - 3.0*UY + 9.0/2.0*UY**2 - T1)
            FEQ[5,:,:,:]=tDENSITY*(1.0 + 3.0*UX + 9.0/2.0*UX**2 - T1)
            FEQ[6,:,:,:]=tDENSITY*(1.0 - 3.0*UX + 9.0/2.0*UX**2 - T1)
            # next-nearest neighbours
            T1 = 3.0*U_SQU/2.0
            tDENSITY = t3*DENSITY
            FEQ[7,:,:,:] =tDENSITY*(1.0 + 3.0*U8  + 9.0/2.0*(U8)**2  - T1)
            FEQ[8,:,:,:] =tDENSITY*(1.0 + 3.0*U9  + 9.0/2.0*(U9)**2  - T1)
            FEQ[9,:,:,:] =tDENSITY*(1.0 + 3.0*U10 + 9.0/2.0*(U10)**2 - T1)
            FEQ[10,:,:,:]=tDENSITY*(1.0 + 3.0*U11 + 9.0/2.0*(U11)**2 - T1)
            FEQ[11,:,:,:]=tDENSITY*(1.0 + 3.0*U12 + 9.0/2.0*(U12)**2 - T1)
            FEQ[12,:,:,:]=tDENSITY*(1.0 + 3.0*U13 + 9.0/2.0*(U13)**2 - T1)
            FEQ[13,:,:,:]=tDENSITY*(1.0 + 3.0*U14 + 9.0/2.0*(U14)**2 - T1)
            FEQ[14,:,:,:]=tDENSITY*(1.0 + 3.0*U15 + 9.0/2.0*(U15)**2 - T1)
            FEQ[15,:,:,:]=tDENSITY*(1.0 + 3.0*U16 + 9.0/2.0*(U16)**2 - T1)
            FEQ[16,:,:,:]=tDENSITY*(1.0 + 3.0*U17 + 9.0/2.0*(U17)**2 - T1)
            FEQ[17,:,:,:]=tDENSITY*(1.0 + 3.0*U18 + 9.0/2.0*(U18)**2 - T1)
            FEQ[18,:,:,:]=tDENSITY*(1.0 + 3.0*U19 + 9.0/2.0*(U19)**2 - T1)

            F *= (1.0-self.omega)
            F += self.omega * FEQ

            #Densities bouncing back at next timestep
            F[1:,:,:,:] *= self.BOUNDi[np.newaxis,:,:,:]
            F[1:,:,:,:] += BB[1:,:,:,:]

        return (UX * -1), UY, UZ


nx, ny, nz = 30, 30, 30
sim = FluidSimulation(nx, ny, nz)

for i in range(nx):
    for j in range(ny):
        for k in range(nz):
            if ((i-10)**2+(j-10)**2+(k-10)**2) < 40:
                sim.BOUND[i,j,k] = 1.0
                sim.BOUNDi[i,j,k] = 0.0

start = time.time()
UX, UY, UZ = sim.run(100)

print('finished in %f seconds' % (time.time() - start))

# from coral_growth.viewer import Viewer
# view = Viewer((1000, 1000))
# view.start_draw()
# lines = []

# for xi in range(UY.shape[0]):
#     for yi in range(UY.shape[1]):
#         for zi in range(UY.shape[2]):

#             x = xi * .1
#             y = yi * .1
#             z = zi * .1
#             s = 100

#             p1 = (x, y, z)
#             p2 = (x+UX[xi, yi, zi]*s, y+UY[xi, yi, zi]*s, z+UX[xi, yi, zi]*s)
#             lines.append((p1, p2))

#             if BOUND[xi, yi, zi] == 1:
#                 view.draw_cube(x, y, z, s=.1)
# #
# view.draw_lines(lines, color=(0,0,1.0))
# view.end_draw()
# view.main_loop()

import matplotlib.pyplot as plt
plt.quiver(UY[:,10,:],UX[10,:,:], pivot='middle')

plt.show()

# plt.imshow(BOUND[:,5,:])
# print(BOUND)
# print(T[, :, :, : ])
