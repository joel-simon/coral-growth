import math
import random

from plant_growth import constants
from plant_growth.world import World

import MultiNEAT as NEAT

def simulate_single(network, display=None, break_early=True):

    world_params = {
        'width': constants.WORLD_WIDTH,
        'height': constants.WORLD_HEIGHT,
        'max_plants': 10,
    }

    world = World(world_params)

    x = constants.WORLD_WIDTH / 2.0
    y = constants.SEED_RADIUS
    r = constants.SEED_RADIUS
    world.add_plant(x, y, r, network, constants.PLANT_EFFICIENCY)

    # volumes = []

    for s in range(constants.SIMULATION_STEPS):
        world.simulation_step()

        if display:
            display(world)

        if break_early:
            if not world.plants[0].alive:
                break

            # if world.plants[0].volume == volumes[-1]:
            #     break

        # volumes.append(world.plants[0].volume)

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

