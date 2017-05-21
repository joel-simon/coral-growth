import math
import random

from plant_growth import constants
from plant_growth.vec2D import Vec2D
from plant_growth.world import World

import MultiNEAT as NEAT

def evaluate(genome, display=None, break_early=True):
    net = NEAT.NeuralNetwork()
    genome.BuildPhenotype(net)
    world = World(constants.WORLD_WIDTH, constants.WORLD_HEIGHT,
                    constants.LIGHT_ANGLE,
                    constants.SOIL_HEIGHT)

    random.seed(0)
    # seed_polygon = []

    # for i in range(constants.SEED_SEGMENTS):
    #     a = 2 * i * math.pi / constants.SEED_SEGMENTS
    x = constants.WORLD_WIDTH/2# + math.cos(a) * constants.SEED_RADIUS
    y = constants.SOIL_HEIGHT# + math.sin(a) * constants.SEED_RADIUS
    #     seed_polygon.append(Vec2D(x, y))
    r = constants.SEED_RADIUS
    world.add_plant(x, y, r, net, constants.PLANT_EFFICIENCY)

    for s in range(constants.SIMULATION_STEPS):
        world.simulation_step()

        if display:
            display(world)

        if break_early:
            if not world.plants[0].alive:
                break

            if s==50 and world.plants[0].volume < 2000:
                break

    if display:
        print('Evaluate finished.')
        print('\tSteps =', s+1)
        print('\tn_cells =', world.plants[0].n_cells)
        print()

    return world.plants[0]
