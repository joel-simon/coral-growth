
import numpy as np
import time
from coral_growth.modules.flow import Flow
from coral_growth.viewer import Viewer

from cymesh.mesh import Mesh

mesh = Mesh.from_obj('/Users/joelsimon/Dropbox/coral_temp/coral_growth/output/batch1/out_November_22_2017_16_25_R5BF/5/0/28.coral.obj')
# mesh = Mesh.from_obj('data/triangulated_sphere_3.obj')
data = mesh.export()

class FakeCoral(object):
    polyp_pos = data['vertices']
    n_polyps = data['vertices'].shape[0]

start = time.time()
nx, ny, nz = 16, 16, 16
bb = mesh.boundingBox()

sim = Flow(FakeCoral, nx, ny, nz, blocksize = 2 * (bb[1] - bb[0]) / (nx))
sim.update(50)

print('finished in %f seconds' % (time.time() - start))

# print(sim.came_from)
view = Viewer((1000, 1000))
view.start_draw()
print(sim.dens_prev.min(), sim.dens_prev.max())
lines = []
for xi in range(nx):
    for yi in range(ny):
        for zi in range(nz):
            x = xi - nx//2 + .5
            y = yi - nx//2 + .5
            z = zi - nx//2 + .5
            i = sim.IX(xi, yi, zi)

            if sim.grid[i]:
                view.draw_cube(x, y, z, s=1)

            else:
                # r = .2
                r = sim.dens[i]
                p1 = (x, y, z)
                p2 = (x-sim.u[i]*r, y-sim.v[i]*r, z-sim.w[i]*r)
                lines.append((p1, p2))

view.draw_lines(lines, color=(0, 0, 1.0))
view.end_draw()
view.main_loop()
