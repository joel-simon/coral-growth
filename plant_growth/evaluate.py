import math
import random

from plant_growth import constants
from plant_growth.world import World

import MultiNEAT as NEAT

random.seed(0)

def simulate_single(network, display=None, break_early=True):
    world_params = {
        'width': constants.WORLD_WIDTH,
        'height': constants.WORLD_HEIGHT,
        'soil_height': constants.SOIL_HEIGHT,
        'max_plants': 1,
    }

    world = World(world_params)

    x = constants.WORLD_WIDTH / 2.0
    y = constants.SOIL_HEIGHT
    r = constants.SEED_RADIUS
    world.add_plant(x, y, r, network, constants.PLANT_EFFICIENCY)

    for s in range(constants.SIMULATION_STEPS):
        world.simulation_step()

        if display:
            display(world)

        if break_early:
            if not world.plants[0].alive:
                break

    if display:
        print('Evaluate finished.')
        print('\tSteps =', s+1)
        print('\tn_cells =', world.plants[0].n_cells)
        print()

    return world.plants[0]

def evaluate_genome(genome, display=None, break_early=True):
    network = NEAT.NeuralNetwork()
    genome.BuildPhenotype(network)
    plant = simulate_single(network, display, break_early)
    return plant

