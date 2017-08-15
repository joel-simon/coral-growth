from math import pi, cos, sin
# import random
import os
import time

from plant_growth import constants
from plant_growth.world import World
from plant_growth.viewer import AnimationViewer

import MultiNEAT as NEAT
# from StringIO import StringIO

obj_path = '/Users/joelsimon/Dropbox/plant_growth/data/triangulated_sphere_2.obj'
# obj_path = '/home/simonlab/Dropbox/plant_growth/data/triangulated_sphere_2.obj'

world_params = {
    'max_plants': 1,
    'use_physics': constants.use_physics,
    'verbose': False
}

def simulate_single(network, export_folder=None):
    # t = time.time()
    # animation = []/
    # if display:
    #     world_params['verbose'] = True
    # else:
    #     world_params['verbose'] = False

    world = World(world_params)
    world.add_plant(obj_path, network)

    # if display: out = StringIO()
    if export_folder:
        out = open(os.path.join(export_folder, '0.plant.obj'), 'w+')
        world.plants[0].export(out)
    # if out:

        # if display(animation.append(out))

    for s in range(constants.SIMULATION_STEPS):
        world.simulation_step()
        plant = world.plants[0]

        if export_folder:
            file_name = '%i.plant.obj' % (s+1)
            out = open(os.path.join(export_folder, file_name), 'w+')
            plant.export(out)

        # if display:
        #     animation.append([ world.[plants0].export() ])

        if world.plants[0].alive == False:
            # if display:
            #     print('Plant dead, ending simulation.')
            break

    # if display:
    #     print('Evalaution Finished in:', time.time() - t)
    #     # print('\tSteps =', s+1)
    #     print('\tn_cells =', world.plants[0].n_cells)
    #     print()

    #     view = AnimationViewer(animation, (1000, 1000))
    #     view.main_loop()

    return world.plants[0]

def evaluate_genome(genome, display=False, export_folder=None):
    network = NEAT.NeuralNetwork()
    genome.BuildPhenotype(network)
    plant = simulate_single(network, export_folder)
    return plant

