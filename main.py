from __future__ import division, print_function
import math, random, os, time

from plant_growth import constants, neat_params
from plant_growth.pygameDraw import PygameDraw
from plant_growth.plot import plot
from plant_growth.evaluate import evaluate

import MultiNEAT as NEAT

view = PygameDraw(constants.WORLD_WIDTH, constants.WORLD_HEIGHT)

genome = NEAT.Genome(
    0, # ID
    constants.NUM_INPUTS,
    0, # NUM_HIDDEN
    constants.NUM_OUTPUTS,
    False, # FS_NEAT
    NEAT.ActivationFunction.UNSIGNED_SIGMOID, # Output activation function
    NEAT.ActivationFunction.UNSIGNED_SIGMOID, # Hidden activation function..
    0, # Seed type, must be 1 to have hidden nodes.
    neat_params.params
)

pop = NEAT.Population(
    genome, # Seed genome.
    neat_params.params,
    True, # Randomize weights.
    1.0, # Random Range.
    int(time.time()) # Random number generator seed.
)

def display_func(world):
    plot(view, world)

if not os.path.exists('out'):
    os.makedirs('out')

last_fitness = 0.0
for generation in range(constants.NUM_GENERATIONS):
    print('Starting generation', generation)

    genome_list = NEAT.GetGenomeList(pop)
    for genome in genome_list:
        fitness = evaluate(genome)
        genome.SetFitness(fitness)

    fitnesses = [g.Fitness for g in genome_list]
    mean = sum(fitnesses) / float(len(fitnesses))
    maxf = max(fitnesses)
    print('Max fitness:', maxf, 'Mean fitness:', mean)

    if maxf != last_fitness:
        best = pop.GetBestGenome()
        best.Save('out/best_%i' % generation)
        evaluate(best, display=display_func)
        view.save('out/best_%i.jpg' % generation)
        last_fitness = maxf

    pop.Epoch()
    print()
