from math import pi, cos, sin
import random

from plant_growth import constants
from plant_growth.world import World

import MultiNEAT as NEAT

def simulate_single(network, display=None, break_early=True):

    world_params = {
        'width': constants.WORLD_WIDTH,
        'height': constants.WORLD_HEIGHT,
        'max_plants': 10,
        'use_physics': constants.use_physics,
    }

    world = World(world_params)

    x = constants.WORLD_WIDTH / 2.0
    y = constants.SEED_RADIUS
    r = constants.SEED_RADIUS

    seed_poly = []
    for i in range(constants.SEED_SEGMENTS):
        a = 2 * i * pi / constants.SEED_SEGMENTS
        seed_poly.append(( x + cos(a)*r, y + sin(a)*r))

    world.add_plant(seed_poly, network, constants.PLANT_EFFICIENCY)

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

    # For creating a debug mesh.
    if False:
        import pickle
        # import numpy as np
        world.use_physics = True
        world.simulation_step()
        # mesh = dict()
        # mesh['points'] = np.array(world.plants[0].mesh.points)
        # mesh['edges'] = np.array(world.plants[0].mesh.faces)
        pickle.dump(world.plants[0].mesh.to_arrays(), open('plant_mesh1.p', 'wb'))
        display(world)
        print('Dumped mesh')

    return world.plants[0]

def evaluate_genome(genome, display=None, break_early=True):
    network = NEAT.NeuralNetwork()
    genome.BuildPhenotype(network)
    plant = simulate_single(network, display, break_early)
    return plant

