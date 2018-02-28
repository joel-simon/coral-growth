from __future__ import print_function
import os, time, math
from os.path import join as pjoin
import MultiNEAT as NEAT
import numpy as np
from cymesh.shape_features import d2_features, a2_features
from coral_growth.coral import Coral
from coral_growth.simulate import simulate_genome

def create_initial_population(params):
    # Create network size based off coral and parameters.
    n_inputs, n_outputs = Coral.calculate_inouts(params)

    genome_prototype = NEAT.Genome(
        0, # ID
        n_inputs,
        0, # NUM_HIDDEN
        n_outputs,
        False, # FS_NEAT
        NEAT.ActivationFunction.UNSIGNED_SIGMOID, # Output activation function.
        NEAT.ActivationFunction.UNSIGNED_SIGMOID, # Hidden activation function.
        0, # Seed type, must be 1 to have hidden nodes.
        params.neat,
        0
    )
    pop = NEAT.Population(
        genome_prototype, # Seed genome.
        params.neat,
        True, # Randomize weights.
        1.0, # Random Range.
        int(time.time()) # Random number generator seed.
    )
    return pop

def evaluate(genome, traits, params):
    """ Run the simulation and return the fitness.
    """
    try:
        coral = simulate_genome(genome, traits, [params])[0]
        fitness = coral.fitness()
        assert math.isfinite(fitness), 'Not-finite'
        print('.', end='', flush=True)
        return fitness

    except AssertionError as e:
        print('Exception:', e, end='', flush=True)
        return 0

def shape_descriptor(coral):
    if coral is None:
        return np.zeros(64)
    else:
        d2 = d2_features(coral.mesh, n_points=2<<13, n_bins=32, hrange=(0.0, 3.0))
        a2 = a2_features(coral.mesh, n_points=2<<13, n_bins=32, hrange=(0.0, 3.0))
        return np.hstack((d2, a2))

def evaluate_novelty(genome, traits, params):
    """ Run the simulation and return the fitness and feature vector.
    """
    try:
        coral = simulate_genome(genome, traits, [params])[0]
        fitness = coral.fitness()
        assert math.isfinite(fitness), 'Not-finite'
        print('.', end='', flush=True)
        return fitness, shape_descriptor(coral)

    except AssertionError as e:
        print('AssertionError:', e, end='', flush=True)
        return 0, shape_descriptor(None)

def evaluate_genomes_novelty(genomes, params, pool):
    """ Evaluate all (parallel / serial wrapper """
    if pool:
        data = [ (g, g.GetGenomeTraits(), params) for g in genomes ]
        ff = pool.starmap(evaluate_novelty, data)
    else:
        ff = [ evaluate_novelty(g, g.GetGenomeTraits(), params) for g in genomes ]
    fitness_list, feature_list = zip(*ff)
    return fitness_list, feature_list

def simulate_and_save(genome, params, out_dir, generation, fitness, meanf):
    export_folder = pjoin(out_dir, str(generation))
    os.mkdir(export_folder)

    genome.Save(pjoin(export_folder, 'genome.txt'))

    with open(pjoin(out_dir, 'scores.txt'), "a") as f:
        f.write("%i\t%f\t%f\n"%(generation, fitness, meanf))

    traits = genome.GetGenomeTraits()
    with open(pjoin(export_folder, 'traits.txt'), "w+") as f:
        for k, v in sorted(traits.items()):
            f.write("%s\t%f\n"%(k, v))

    return simulate_genome(genome, traits, [params], export_folder=export_folder)