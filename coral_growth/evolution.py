from __future__ import print_function
import random, os, sys, string, argparse, time
from datetime import datetime
from multiprocessing import Pool
import numpy as np
from tempfile import TemporaryDirectory
import MultiNEAT as NEAT

from coral_growth.simulate import simulate_network
from coral_growth.coral import Coral
from coral_growth.simulate import simulate_genome
from coral_growth.parameters import Parameters
from coral_growth.evolution import evolve_neat, evolve_novelty
from pykdtree.kdtree import KDTree

ns_K = 5
ns_P_min = 10.0
# ns_dynamic_Pmin = True
# ns_Pmin_min = 1.0
# ns_no_archiving_stagnation_threshold = 150
# ns_Pmin_lowering_multiplier = 0.9
# ns_Pmin_raising_multiplier = 1.1
# ns_quick_archiving_min_evals = 8

 # if not ns_on:
    #     for i in range(gens):
    #         # get best fitness in population and print it
    #         fitness_list = [x.GetFitness() for x in NEAT.GetGenomeList(pop)]
    #         best = max(fitness_list)

    #         if best > best_ever:
    #             sys.stdout.flush()
    #             print()
    #             print('NEW RECORD!')
    #             print('Evaluations:', i, 'Species:', len(pop.Species), 'Fitness:', best)
    #             best_gs.append(pop.GetBestGenome())
    #             best_ever = best
    #             hof.append(pickle.dumps(pop.GetBestGenome()))

def create_initial_population(params):
    # Create netowrk size based off coral and parameters.
    num_inputs = Coral.num_inputs + params.polyp_memory + \
                 params.n_morphogens*(params.morph_thresholds - 1)

    num_outputs = Coral.num_outputs + params.polyp_memory + params.n_morphogens

    genome_prototype = NEAT.Genome(
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
        genome_prototype, # Seed genome.
        params,
        True, # Randomize weights.
        1.0, # Random Range.
        int(time.time()) # Random number generator seed.
    )
    return genome_prototype, pop


def evaluate(genome, traits):
    try:
        coral = simulate_genome(genome, traits, [params])[0]
        fitness = coral.fitness()
    except AssertionError as e:
        print('Exception:', e)
        fitness = 0
    print('.', end='', flush=True)
    return fitness

# def evaluate_from_path(genome_path, traits):
#     """ Load a genome text file and run the simulation.
#     """
#     genome = NEAT.Genome(genome_path)
#     return evaluate(genome, traits)

# def evaluate_parallel(pool, genomes):
#     """ The genome object from MultiNEAT cannot be pickled :'(
#         So save to disk and pass path to subprocess.
#     """
#     with TemporaryDirectory() as tmp_dir:
#         t = time.time()
#         data = []
#         for i, genome in enumerate(genomes):
#             path = tmp_dir+'/'+str(i)
#             genome.Save(path)
#             data.append((path, genome.GetGenomeTraits()))

#         fitnesses = pool.starmap(evaluate_from_path, data)

#     return fitnesses


def simulate_and_save(genome, out_dir, generation, fitness):
    # best.Save(out_dir+'/best_%i' % generation)
    # best = NEAT.Genome(out_dir+'/best_%i' % generation)
    traits = genome.GetGenomeTraits()

    print('New best fitness.', best.NumNeurons(), best.NumLinks())

    with open(out_dir+'/scores.txt', "a") as f:
        f.write("%i\t%f\n"%(generation, fitness))

    with open(out_dir+'/best_%i_traits.txt' % generation, "w+") as f:
        f.write(str(traits))

    export_folder = os.path.join(out_dir, str(generation))
    os.mkdir(export_folder)
    simulate_genome(best, traits, [params], export_folder=export_folder)


def evolve_neat(params, generations, out_dir, run_id, n_cores):
    if n_cores > 1:
        pool = Pool(processes=n_cores)

    pop = create_initial_population(params)
    max_ever = 0.0
    t = time.time()

    for generation in range(generations):
        print(run_id, 'Starting generation', generation)
        genomes = NEAT.GetGenomeList(pop)

        if n_cores > 1:
            # fitnesses = evaluate_parallel(pool, genomes)
            # data.append((path, genome.GetGenomeTraits()))
            data = [ (g, g.GetGenomeTraits(), params) for g in genomes ]
            fitnesses = pool.starmap(evaluate_from_path, data)
        else:
            fitnesses = [ evaluate(g, g.GetGenomeTraits()) for g in genomes ]

        for genome, fitness in zip(genomes, fitnesses):
            genome.SetFitness(fitness)
            genome.SetEvaluated()

        maxf, meanf = max(fitnesses), sum(fitnesses) / float(len(fitnesses))
        runtime = time.time() - t
        t = time.time()
        print('\nGeneration %i ran in %f, %f per coral' % \
              (generation, runtime, runtime/len(genomes)))
        print('Max fitness:', maxf, 'Mean fitness:', meanf)

        if maxf > max_ever:
            max_ever = maxf
            best = pop.GetBestGenome()
            simulate_and_save(best, out_dir, generation, maxf)

        pop.Epoch()
        print('#'*80)

    print('Run Complete.')
    pool.close()
    pool.join()

def feature_vector(coral):
    """ Compute a desciptive feature vector for calculating novelty.
    """
    features = np.zeros(11)

    d = np.sqrt(coral.polyp_pos[:, 0]**2 + coral.polyp_pos[:, 2]**2)
    c = np.array([v.curvature for v in mesh.verts])

    bbox = coral.mesh.boundingBox()
    bbox_area = (bbox[1]-bbox[0]) * (bbox[3]-bbox[2]) * (bbox[4]-bbox[4])

    features[0] = np.mean(d) # Mean dist from center
    features[1] = np.std(d) # Std of dist from center
    features[2] = np.mean(coral.polyp_pos[:, 1]) # Mean height
    features[4] = np.std(coral.polyp_pos[:, 1]) # Std height
    features[5] = coral.spring_strength # Spring Strength
    features[6] = bbox_area / coral.mesh.volume # Density
    features[7:12] = np.histogram(c, 5, (-.5, .5), normed=True)[0]

    return features

def evaluate_novelty(genome, traits, params):
    try:
        coral = simulate_genome(genome, traits, [params])[0]
        fitness = coral.fitness()
    except AssertionError as e:
        print('Exception:', e)
        fitness = 0
    print('.', end='', flush=True)
    return fitness, feature_vector(coral)

def evolve_novelty(params, generations, out_dir, run_id, n_cores, \
                   novelty_threshold=10, archive_stagnation=4):
    max_ever = 0
    archive = []
    evals_since_last_archiving = 0

    def evaluate_genomes(genomes):
        if n_cores > 1:
            data = [ (g, g.GetGenomeTraits(), params) for g in genomes ]
            ff = pool.starmap(evaluate_novelty, data)
        else:
            ff = [ evaluate_novelty(g, g.GetGenomeTraits(), params) for g in genomes ]

        fitness_list, feature_list = zip(*ff)
        # corals = [ fn_simulate(g)[0] for g in genomes ]
        # fitness_list = [ c.fitness() for c in corals ]
        # features = np.array([fn_features(c) for c in corals])
        tree = KDTree(np.vstack(archive, feature_list))
        dists, _ = tree.query(np.array(feature_list), k=ns_K+1)
        sparseness_list = np.mean(dists[:, 1:], axis=1)
        print('Avg novelty:', np.mean(sparseness_list))
        return sparseness_list, fitness_list, feature_list

    # Create Initial Archive.
    genomes = NEAT.GetGenomeList(pop)
    _, _, feature_list = evaluate_genomes(genomes)
    archive.extend(feature_list)

    # #Main loop
    for generation in range(generations):
        genomes = NEAT.GetGenomeList(pop)
        sparseness_list, fitness_list, _ = evaluate_genomes()

        n_archive_added = 0

        for genome, sparseness in zip(genomes, sparseness_list):
            genome.SetFitness( sparse )
            genome.SetEvaluated()

            if sparseness > novelty_threshold:
                print('Novel genome found.')
                archive.append(fn_features(coral))
                n_archive_added += 1

        if not n_archive_added:
            evals_since_last_archiving += 1

        # Dynamic novelty_threshold
        if evals_since_last_archiving > archive_stagnation:
            novelty_threshold *= .9
        elif n_archive_added > 4:
            novelty_threshold *= 1.1

        maxf = max(fitness_list)
        if maxf > max_ever:
            max_ever = maxf
            best_genome = genomes[fitness_list.index(maxf)]
            simulate_and_save(best_genome, out_dir, generation, maxf)

