from __future__ import division, print_function
import math, random, os, time, sys, string, argparse
from multiprocessing import Pool
from tempfile import TemporaryDirectory

sys.path.append(os.path.abspath('..'))
import MultiNEAT as NEAT
from coral_growth.simulate import simulate_genome
from coral_growth.coral import Coral

def evaluate_from_path(genome_path, traits, params):
    """ Load a genome text file and run the simulation.
    """
    genome = NEAT.Genome(genome_path)

    try:
        coral = simulate_genome(time_steps, genome, traits, [params])[0]
        fitness = coral.fitness()

    except AssertionError as e:
        print('Exception:', e)
        fitness = 0

    print('.', end='', flush=True)
    return fitness

def evaluate_parallel(pool, genomes, params):
    """ The genome object from MultiNEAT cannot be pickled :'(
        So save to disk and pass path to subprocess.
    """
    with TemporaryDirectory() as tmp_dir:
        t = time.time()
        data = []
        for i, genome in enumerate(genomes):
            path = tmp_dir+'/'+str(i)
            genome.Save(path)
            data.append((path, genome.GetGenomeTraits(), params))
        fitnesses = pool.starmap(evaluate_from_path, data)
    return fitnesses

def evolve_neat(params, generations, out_dir, run_id, n_cores):
    pool = Pool(processes=n_cores)

    num_inputs = Coral.num_inputs + params['polyp_memory'] + \
                 params.n_morphogens*(world_configs['morph_thresholds'] - 1)

    num_outputs = Coral.num_outputs + params['polyp_memory'] + params.n_morphogens

    genome_prototye = NEAT.Genome(
        0, # ID
        num_inputs,
        0, # NUM_HIDDEN
        num_outputs,
        False, # FS_NEAT
        NEAT.ActivationFunction.UNSIGNED_SIGMOID, # Output activation function.
        NEAT.ActivationFunction.UNSIGNED_SIGMOID, # Hidden activation function.
        0, # Seed type, must be 1 to have hidden nodes.
        params
    )

    pop = NEAT.Population(
        genome_prototye, # Seed genome.
        params,
        True, # Randomize weights.
        1.0, # Random Range.
        int(time.time()) # Random number generator seed.
    )

    last_fitness = 0.0
    t = time.time()

    for generation in range(generations):
        print(run_id, 'Starting generation', generation)

        genomes = NEAT.GetGenomeList(pop)
        fitnesses = evaluate_parallel(pool, genomes, params)

        for genome, fitness in zip(genomes, fitnesses):
            genome.SetFitness(fitness)
            genome.SetEvaluated()

        mean = sum(fitnesses) / float(len(fitnesses))
        maxf = max(fitnesses)

        runtime = time.time() - t
        t = time.time()

        print('\nGeneration %i ran in %f, %f per coral' % \
                                    (generation, runtime, runtime/len(genomes)))
        print('Max fitness:', maxf, 'Mean fitness:', mean)

        if maxf != last_fitness:
            last_fitness = maxf

            best = pop.GetBestGenome()
            best.Save(out_dir+'/best_%i' % generation)
            best = NEAT.Genome(out_dir+'/best_%i' % generation)
            traits = genome.GetGenomeTraits()

            print('New best fitness.', best.NumNeurons(), best.NumLinks())

            with open(out_dir+'/scores.txt', "a") as f:
                f.write("%i\t%f\n"%(generation, maxf))

            with open(out_dir+'/best_%i_traits.txt' % generation, "w+") as f:
                f.write(str(traits))

            export_folder = os.path.join(out_dir, str(generation))
            os.mkdir(export_folder)
            simulate_genome(time_steps, best, traits, [world_configs], \
                                                export_folder=export_folder)
        pop.Epoch()
        print('#'*80)

    print('Run Complete.')
    pool.close()
    pool.join()


# def write_genome_from_array(arr, path, n_in, n_out, n_traits):
#     assert len(arr) == n_in + n_out + n_traits

#     with open(path, 'w') as out:
#         out.write('GenomeStart 0\n')
#         for i in range(n_in + n_out):
#             out.write('Neuron %i %i %f %i %f %f %f %f\n' % (i, ))

# def evaluate_parallel_cmaes(pool, solutions):
#     with TemporaryDirectory() as tmp_dir:
#         t = time.time()
#         data = []

#         for i, genome in enumerate(genomes):
#             path = tmp_dir+'/'+str(i)
#             genome.Save(path)
#             data.append((path, genome.GetGenomeTraits()))

#         fitnesses = pool.starmap(evaluate_from_path, data)

#     return fitnesses

# def evaluate_serial(genomes):
#     fitnesses = []
#     for genome in genomes:
#         fitnesses.append(evaluate(genome))

#     return fitnesses

# def evolve_cmaes(generations, out_dir, run_id, n_cores=3):
#     import cma

#     n_inputs = Coral.num_inputs + neat_params.n_morphogens
#     n_outputs = Coral.num_outputs + neat_params.n_morphogens
#     n_dimensions = n_inputs + n_outputs

#     start = [(random.random()*2) - 1 for _ in range(n_inputs)]
#     es = cma.CMAEvolutionStrategy(start, 0.5)

#     pool = Pool(processes=n_cores)

#     last_fitness = 0.0
#     t = time.time()

#     for generation in range(generations):
#         print(run_id, 'Starting generation', generation)

#         solutions = es.ask()
#         fitnesses = evaluate_parallel_cmaes(solutions)
#         es.tell(solutions, fitnesses)

#         mean = sum(fitnesses) / float(len(fitnesses))
#         maxf = max(fitnesses)

#         runtime = time.time() - t
#         t = time.time()

#         print('\nGeneration %i ran in %f, %f per coral' % \
#                                     (generation, runtime, runtime/len(genomes)))
#         print('Max fitness:', maxf, 'Mean fitness:', mean)

#         if maxf != last_fitness:
#             last_fitness = maxf

#             best = pop.GetBestGenome()
#             best.Save(out_dir+'/best_%i' % generation)
#             best = NEAT.Genome(out_dir+'/best_%i' % generation)
#             traits = genome.GetGenomeTraits()

#             print('New best fitness.', best.NumNeurons(), best.NumLinks())

#             with open(out_dir+'/scores.txt', "a") as f:
#                 f.write("%i\t%f\n"%(generation, maxf))

#             with open(out_dir+'/best_%i_traits.txt' % generation, "w+") as f:
#                 f.write(str(traits))

#             os.mkdir(os.path.join(out_dir, str(generation)))
#             try:
#                 simulate_genome(time_steps, best, traits, [world_configs], \
#                                 export_folder=os.path.join(out_dir, str(generation)))
#             except AssertionError as e:
#                 print('WTF??', e)

#         pop.Epoch()
#         print('#'*80)

#     print('Run Complete.')
#     pool.close()
#     pool.join()
