import sys, os
import matplotlib.pyplot as plt
import numpy as np

path = sys.argv[1]
n = 100

x = np.arange(n)
y = np.zeros(n)

x2, y2 = [], []

for line in open(path).read().splitlines():
    line = line.split('\t')
    gen = int(line[0])
    fitness = float(line[1])

    y[gen] = fitness

    x2.append(gen)
    y2.append(fitness)

for i in range(1, n):
    if y[i] == 0:
        y[i] = y[i-1]

y /= y[0]

out_name = os.path.dirname(path) + '/evolution.png'

ax = plt.gca()
color = next(ax._get_lines.prop_cycler)['color']

plt.title('Coral Optimization')
plt.plot(x, y, color=color)
plt.plot(x2, [v/y2[0] for v in y2], 'o', color=color)
plt.xlabel('Generations')
plt.ylabel('Fitness fold-increase')
# plt.show()
plt.savefig(out_name)
