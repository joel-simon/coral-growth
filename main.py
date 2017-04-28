from __future__ import division, print_function
import math
import random
import time
from vector import Vector
from drawer import PygameDraw
from plot import plot
from world import World
import pyvisgraph as vg
from geometry import Point
from neat_params import params

import MultiNEAT as NEAT
from MultiNEAT import EvaluateGenomeList_Serial
from MultiNEAT import GetGenomeList, ZipFitness

width = 750
height = 750
soil_height = 200

num_segments = 12
radius = 25

link_rest = 2*math.pi*radius / num_segments
max_link_length = 1.3 * link_rest

view = PygameDraw(width, height)
light = Point(width-10, height-10)

def evaluate(genome, display=False):
    world = World(width, height, max_link_length, light, soil_height)
    net = NEAT.NeuralNetwork()
    genome.BuildPhenotype(net)


    seed_polygon = []
    for i in range(num_segments):
        a = 2 * i * math.pi / num_segments
        x = width/2 + math.cos(a) * radius# + (random.random()-.5)
        y = soil_height + math.sin(a) * radius# + (random.random()-.5)
        seed_polygon.append(Vector(x, y))

    world.add_plant(seed_polygon, net, .002)

    for s in range(400):
        world.calculate()
        if display:
            plot(view, world)
        world.simulation_step()
        if world.plants[0].alive == False:
            # print(s)
            break
    # print(int(world.plants[0].volume))
    return world.plants[0].volume



################################################################################


#(id, num_in, hidden out)
genome = NEAT.Genome(0, 5, 0, 1, False, NEAT.ActivationFunction.UNSIGNED_SIGMOID,
                    NEAT.ActivationFunction.UNSIGNED_SIGMOID, 0, params)

pop = NEAT.Population(genome, params, True, 1.0, 0)
pop.RNG.Seed(int(time.time()))
# genome_list = NEAT.GetGenomeList(pop)


for generation in range(100):
    genome_list = NEAT.GetGenomeList(pop)
    fitness_list = EvaluateGenomeList_Serial(genome_list, evaluate, display=False)
    NEAT.ZipFitness(genome_list, fitness_list)
    pop.Epoch()
    best = max(fitness_list)
    mean = sum(fitness_list)/ float(len(fitness_list))

    print()
    print(int(best), int(mean))
    evaluate(pop.Species[0].GetLeader(), display=True)
    print()


# genome = genome_list[8]
# net = NEAT.NeuralNetwork()
# genome.BuildPhenotype(net)


# seed_polygon = []
# for i in range(num_segments):
#     a = 2 * i * math.pi / num_segments
#     x = 3*width/4 + math.cos(a) * radius + (random.random()-.5)*5
#     y = height/10 + math.sin(a) * radius + (random.random()-.5)*5
#     seed_polygon.append(Vector(x, y))
# world.add_plant(seed_polygon, None)


#
view.hold()

