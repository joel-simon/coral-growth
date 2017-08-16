from math import pi, cos, sin
# import random
import os
import time

from plant_growth import constants
from plant_growth.world import World
from plant_growth.viewer import AnimationViewer

import MultiNEAT as NEAT
import os

obj_path = os.getcwd()+'/../data/triangulated_sphere_2.obj'

world_params = {
    'max_plants': 1,
    'use_physics': constants.use_physics,
    'verbose': False
}

def simulate_single(network, export_folder=None):
    world = World(world_params)
    world.add_plant(obj_path, network)

    if export_folder:
        out = open(os.path.join(export_folder, '0.plant.obj'), 'w+')
        world.plants[0].export(out)

    for s in range(constants.SIMULATION_STEPS):
        world.simulation_step()
        plant = world.plants[0]

        if export_folder:
            file_name = '%i.plant.obj' % (s+1)
            out = open(os.path.join(export_folder, file_name), 'w+')
            plant.export(out)

        if world.plants[0].alive == False:
            break

    # if display:
    #     print('Evalaution Finished in:', time.time() - t)
    #     # print('\tSteps =', s+1)
    #     print('\tn_cells =', world.plants[0].n_cells)
    #     print()

    return world.plants[0]

def evaluate_genome(genome, display=False, export_folder=None):
    network = NEAT.NeuralNetwork()
    genome.BuildPhenotype(network)
    plant = simulate_single(network, export_folder)
    return plant

