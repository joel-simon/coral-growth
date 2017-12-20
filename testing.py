from cymesh.mesh import Mesh
import numpy as np
import matplotlib.pyplot as plt

# mesh = Mesh.from_obj('/Users/joelsimon/Dropbox/coral_out/NRHL__December_18_2017_20_28/99/0/12.coral.obj')
mesh = Mesh.from_obj('/Users/joelsimon/Dropbox/coral_out/63RS__December_18_2017_20_28/9/0/45.coral.obj')
mesh.calculateNormals()
mesh.calculateCurvature()

c = np.array([v.curvature for v in mesh.verts])

# plt.hist(c, bins=30)
# plt.show()
# print(c.mean(), c.std())
# print(c.min(), c.max())
print(np.histogram(c, 5, (-.5, .5), normed=True)[0])
