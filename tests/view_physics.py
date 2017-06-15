import pickle
import numpy as np
from plant_growth import constants
# from plant_growth.physics import spring_simulation, spring_simulation2
from plant_growth.spring_system import spring_simulation
from plant_growth.pygameDraw import PygameDraw

iters = 2000
delta = 1/50.
gravity = -5.0
damping = .1
mesh_dict = pickle.load(open('bin/plant_mesh.p', 'rb'))

view = PygameDraw(constants.WORLD_WIDTH, constants.WORLD_HEIGHT)
i = 0
def draw_func(points, edges):
    global i
    if i % 10 == 0:
        view.start_draw()
        for edge in edges:
            p1 = points[edge[0]]
            p2 = points[edge[1]]
            view.draw_line(p1, p2, (0,0,0), 1)
        view.end_draw()
    i += 1

points, edges = mesh_dict['points'], mesh_dict['edges']
fixed = np.array([p[1] < 10 for p in points], dtype='i')

spring_simulation(points, edges, fixed, iters, delta, gravity, damping, view=draw_func)

print('Simulation Done')

view.hold()
