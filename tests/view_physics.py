import pickle
import numpy as np
from plant_growth import constants
# from plant_growth.physics import spring_simulation, spring_simulation2
from plant_growth.spring_system import spring_simulation
from plant_growth.pygameDraw import PygameDraw

# import matplotlib.pyplot as plt

iters = 3000
delta = 1/100.
gravity = -2.0
damping = 0.01
mesh_dict = pickle.load(open('bin/plant_mesh1.p', 'rb'))

view = PygameDraw(constants.WORLD_WIDTH, constants.WORLD_HEIGHT)
i = 0

derp = []
def draw_func(points, edges, deformation):
    global i, last
    sumd = sum(abs(d) for d in deformation)
    meand = sumd / float(len(deformation))
    derp.append(sumd)

    if i %100 == 0:
        print(i)
    if i % 25 == 0:
        # print(sumd, meand)
        print(max(deformation))
        view.start_draw()
        for edge, d in zip(edges, deformation):
            p1 = points[edge[0]]
            p2 = points[edge[1]]
            if d != 0:
                d = .5 * abs(d) / meand
            r = min(255, max(0, int(d*255.0)))
            color = (r, 0, 0)
            view.draw_line(p1, p2, color, 1)
        view.end_draw()
    # if max(derp) > 100:
    #     print('break', i)
    i += 1

points, edges = mesh_dict['points'], mesh_dict['edges']
deformation = np.zeros(edges.shape[0])
fixed = np.array([p[1] < 10 for p in points], dtype='i')

spring_simulation(points, edges, fixed, iters, delta, gravity, damping, deformation, view=draw_func)

print('Simulation Done')

view.hold()
# plt.plot(derp)
# plt.show()
