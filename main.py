from __future__ import division, print_function
import math
import random
import time
from vec2D import Vec2D
from drawer import PygameDraw
from plot import plot
from world import World
from neat_params import params
import constants
import numpy as np

import MultiNEAT as NEAT
from MultiNEAT import EvaluateGenomeList_Serial
from MultiNEAT import GetGenomeList, ZipFitness

width = 1000
height = 750
soil_height = 350

num_segments = 16
radius = 20

link_rest = 2*math.pi*radius / num_segments
max_link_length = 1.3 * link_rest

view = PygameDraw(width, height)
light = math.pi / 4

def evaluate(genome, display=False):
    world = World(width, height, max_link_length, light, soil_height)
    net = NEAT.NeuralNetwork()
    genome.BuildPhenotype(net)

    random.seed(0)
    seed_polygon = []
    for i in range(num_segments):
        a = 2 * i * math.pi / num_segments
        x = width/2 + math.cos(a) * radius# + (random.random()-.5)
        y = soil_height + math.sin(a) * radius# + (random.random()-.5)
        seed_polygon.append(Vec2D(x, y))

    world.add_plant(seed_polygon, net, .001)

    for s in range(constants.SIMULATION_STEPS):
        world.calculate()

        # print(list(world.plants[0].cells))

        if display:
            plot(view, world)

        world.simulation_step()

        if world.plants[0].alive == False:
            break

        if s == 50:
            if world.plants[0].volume < 2000:
                break

    fitness = world.plants[0].volume

    if display:
        print('Evaluate finished.')
        print('\tFitness =', fitness)
        print('\tSteps =', s)
        print('\tNum cells =', len(world.plants[0].cells))
        print()

    return fitness


################################################################################

genome = NEAT.Genome(
    0, # ID
    constants.NUM_INPUTS,
    0, # NUM_HIDDEN
    constants.NUM_OUTPUTS,
    False, # FS_NEAT
    NEAT.ActivationFunction.UNSIGNED_SIGMOID, # Output activation function
    NEAT.ActivationFunction.UNSIGNED_SIGMOID, # Hidden activation function..
    0, # Seed type, must be 1 to have hidden nodes.
    params
)

pop = NEAT.Population(
    genome, # Seed genome.
    params,
    True, # Randomize weights.
    1.0, # Random Range.
    int(time.time()) # Random number generator seed.
)

test = False

if test:
    # genome_list = NEAT.GetGenomeList(pop)
    # genome = genome_list[1]
    # genome.Save('test_genome')

    genome = NEAT.Genome('benchmark_genome')
    for i in range(2):
        evaluate(genome, display=False)
        print(i)
    # view.hold()

else:
    for generation in range(constants.NUM_GENERATIONS):
        print('Starting generation', generation)

        genome_list = NEAT.GetGenomeList(pop)
        for genome in genome_list:
            fitness = evaluate(genome)
            genome.SetFitness(fitness)

        fitnesses = np.array([g.Fitness for g in genome_list])
        print('Max fitness', fitnesses.max(), 'Mean fitness: ', fitnesses.mean())
        print()
        best = pop.GetBestGenome()
        best.Save('out/best_%i' % generation)
        evaluate(best, display=True)
        pop.Epoch()
        print()


# genome = genome_list[8]
# net = NEAT.NeuralNetwork()
# genome.BuildPhenotype(net)


# seed_polygon = []
# for i in range(num_segments):
#     a = 2 * i * math.pi / num_segments
#     x = 3*width/4 + math.cos(a) * radius + (random.random()-.5)*5
#     y = height/10 + math.sin(a) * radius + (random.random()-.5)*5
#     seed_polygon.append(Vec2D(x, y))
# world.add_plant(seed_polygon, None)


#
# view.hold()

