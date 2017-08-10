from math import pi, cos, sin
# import random
import time

from plant_growth import constants
from plant_growth.world import World
from plant_growth.viewer import AnimationViewer

import MultiNEAT as NEAT

obj_path = '/Users/joelsimon/Dropbox/plant_growth/data/triangulated_sphere_0.obj'
# obj_path = '/home/simonlab/Dropbox/plant_growth/data/triangulated_sphere_0.obj'

world_params = {
    'max_plants': 1,
    'use_physics': constants.use_physics,
    'verbose': False
}

def simulate_single(network, display=False):
    t = time.time()

    if display:
        world_params['verbose'] = True
    else:
        world_params['verbose'] = False

    world = World(world_params)
    world.add_plant(obj_path, network, constants.PLANT_EFFICIENCY)

    animation = [ [ world.plants[0].export() ] ]

    for s in range(constants.SIMULATION_STEPS):

        world.simulation_step()

        animation.append([ world.plants[0].export() ])

        if world.plants[0].alive == False:
            break

    if display:
        print('Evalaution Finished in:', time.time() - t)
        # print('\tSteps =', s+1)
        print('\tn_cells =', world.plants[0].n_cells)
        print()

        view = AnimationViewer(animation, (1000, 1000))
        view.main_loop()

    return world.plants[0]

def evaluate_genome(genome, display=False):
    network = NEAT.NeuralNetwork()
    genome.BuildPhenotype(network)
    plant = simulate_single(network, display)
    return plant

