from random import random as rand
import matplotlib.pyplot as plt
import numpy as np
from plant_growth.tri_hash_2d import TriHash2D

max_length = .2
th2d = TriHash2D(.2, 1)

n_tris = 200

def rand_tri(x, y):
    return [[x + rand()*max_length, y + rand()*max_length] for _ in range(3)]

points = []
for _ in range(n_tris):
    for _ in range(3):
        points.extend(rand_tri(rand()*(1-max_length), rand()*(1-max_length)))

points = np.array(points)
tris = []
for i in range(0, n_tris*3, 3):
    tris.append([i, i+1, i+2])
tris = np.array(tris)


##############################


for i, (a, b, c) in enumerate(tris):
    th2d.py_add_tr(i, list(points[a]), list(points[b]), list(points[c]))

neighbors = th2d.py_neighbors([.5, .5])

x = points[:, 0]
y = points[:, 1]
plt.grid(color='black', linestyle='-', linewidth=1)
plt.triplot(x, y, tris, 'g-')
plt.triplot(x, y, [tris[i] for i in neighbors], 'r-')
plt.show()
