from __future__ import division, print_function
import math, random, os, time, sys
sys.path.append(os.path.abspath('..'))

from plant_growth import constants, neat_params
from plant_growth.evaluate import evaluate

import MultiNEAT as NEAT

neat_params.params.PopulationSize = 50

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

for generation in range(5):
    print('Starting generation', generation)

    genome_list = NEAT.GetGenomeList(pop)
    for genome in genome_list:
        plant = evaluate(genome)
        fitness = plant.total_flowering
        genome.SetFitness(fitness)

    fitnesses = [g.Fitness for g in genome_list]
    mean = sum(fitnesses) / float(len(fitnesses))
    maxf = max(fitnesses)
    print('Max fitness:', maxf, 'Mean fitness:', mean)
    pop.Epoch()
