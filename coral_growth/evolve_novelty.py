from __future__ import print_function
import time
import math
import numpy as np
import MultiNEAT as NEAT
from pykdtree.kdtree import KDTree

from coral_growth.simulate import simulate_genome
from coral_growth.evolution import * #create_initial_population, evaluate, simulate_and_save, shape_descriptor
# from coral_growth.shape_features import d2_features

def evaluate_novelty(genome, traits, params):
    try:
        coral = simulate_genome(genome, traits, [params])[0]
        fitness = coral.fitness()
        print('.', end='', flush=True)
        return fitness, shape_descriptor(coral)
        # np.array(d2_features(coral.mesh, n_points=1<<13,bins=64))

    except AssertionError as e:
        print('AssertionError:', e)
        fitness = 0
        return 0, np.zeros(64)

def evaluate_genomes(genomes, params, pool):
    if pool:
        data = [ (g, g.GetGenomeTraits(), params) for g in genomes ]
        ff = pool.starmap(evaluate_novelty, data)
    else:
        ff = [ evaluate_novelty(g, g.GetGenomeTraits(), params) for g in genomes ]

    fitness_list, feature_list = zip(*ff)
    return fitness_list, feature_list

def calculate_sparseness(archive, feature_list, k):
    feature_arr = np.array(feature_list)
    tree = KDTree( np.vstack( (np.array(archive), feature_arr ) ) )
    dists, _ = tree.query(feature_arr, k=k+1)
    sparseness_list = np.mean(dists[:, 1:], axis=1)
    return sparseness_list

def evolve_novelty(params, generations, out_dir, run_id, pool, ls50=True, \
                   novelty_threshold=0.4, archive_stagnation=4, ns_K=10):
    max_ever = None
    archive = []
    evals_since_last_archiving = 0
    pop = create_initial_population(params)

    print('Creating initial archive.')
    genomes = NEAT.GetGenomeList(pop)
    _, feature_list = evaluate_genomes(genomes, params, pool)
    archive.extend(feature_list)

    # Main loop
    for generation in range(generations):
        print('\n'+'#'*80)
        print(run_id, 'Starting generation %i' % generation)
        print('Novelty threshold', novelty_threshold)

        genomes = NEAT.GetGenomeList(pop)
        fitness_list, feature_list = evaluate_genomes(genomes, params, pool)
        sparseness_list = calculate_sparseness(archive, feature_list, ns_K)

        print()
        print('Sparseness - avg: %f, max:%f' % (np.mean(sparseness_list), max(sparseness_list)))
        print('Fitness - avg: %f, max:%f' % (np.mean(fitness_list), max(fitness_list)))

        n_archive_added = 0

        for i, genome in enumerate(genomes):
            fitness = fitness_list[i]
            feature = feature_list[i]
            sparseness = sparseness_list[i]

            if ls50:
                genome.SetFitness( math.sqrt(sparseness * fitness) )
            else:
                genome.SetFitness( sparseness )

            genome.SetEvaluated()

            if sparseness > novelty_threshold:
                archive.append(feature)
                n_archive_added += 1

        print('Added %i to archive' % n_archive_added)
        print('Archive size is', len(archive))

        if not n_archive_added:
            evals_since_last_archiving += 1
        else:
            evals_since_last_archiving = 0

        # Dynamic novelty_threshold
        if evals_since_last_archiving > archive_stagnation:
            novelty_threshold *= .9
        elif n_archive_added > 4:
            novelty_threshold *= 1.1

        maxf, meanf = max(fitness_list), sum(fitness_list) / float(len(fitness_list))
        if max_ever is None or maxf > max_ever:
            max_ever = maxf
            best = genomes[fitness_list.index(maxf)]
            print('New best fitness.', best.NumNeurons(), best.NumLinks())
            simulate_and_save(best, params, out_dir, generation, maxf, meanf)

        pop.Epoch()