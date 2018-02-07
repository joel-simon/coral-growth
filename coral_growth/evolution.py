from __future__ import print_function
import time
import os
import MultiNEAT as NEAT
from coral_growth.coral import Coral
from coral_growth.simulate import simulate_genome

def create_initial_population(params):
    # Create network size based off coral and parameters.
    num_inputs = Coral.num_inputs + params.n_memory + params.n_signals +\
                 params.n_morphogens*(params.morphogen_thresholds - 1) + \
                 (4 * params.use_polar_direction)

    num_outputs = Coral.num_outputs + params.n_memory + params.n_signals + \
                  params.n_morphogens

    genome_prototype = NEAT.Genome(
        0, # ID
        num_inputs,
        10, # NUM_HIDDEN
        num_outputs,
        True, # FS_NEAT
        NEAT.ActivationFunction.UNSIGNED_SIGMOID, # Output activation function.
        NEAT.ActivationFunction.UNSIGNED_SIGMOID, # Hidden activation function.
        1, # Seed type, must be 1 to have hidden nodes.
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
    try:
        coral = simulate_genome(genome, traits, [params])[0]
        fitness = coral.fitness()
    except AssertionError as e:
        print('Exception:', e)
        fitness = 0
    print('.', end='', flush=True)
    return fitness

def simulate_and_save(genome, params, out_dir, generation, fitness, meanf):
    genome.Save(out_dir+'/genome_%i' % generation)
    traits = genome.GetGenomeTraits()
    with open(out_dir+'/scores.txt', "a") as f:
        f.write("%i\t%f\t%f\n"%(generation, fitness, meanf))
    with open(out_dir+'/best_%i_traits.txt' % generation, "w+") as f:
        f.write(str(traits))
    export_folder = os.path.join(out_dir, str(generation))
    os.mkdir(export_folder)
    return simulate_genome(genome, traits, [params], export_folder=export_folder)