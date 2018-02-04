from __future__ import print_function
import time
import math
import numpy as np
import MultiNEAT as NEAT
from pykdtree.kdtree import KDTree

from coral_growth.simulate import simulate_genome
from coral_growth.evolution import create_initial_population, evaluate, simulate_and_save

def feature_vector(coral):
    """ Compute a descriptive feature vector for calculating novelty.
    """
    features = np.zeros(3)
    features[0] = coral.light
    features[1] = coral.collection
    features[2] = np.mean(coral.polyp_pos[:, 1]) # Mean height
    return features

    # d = np.sqrt(coral.polyp_pos[:coral.n_polyps, 0]**2 + coral.polyp_pos[:coral.n_polyps, 2]**2)
    # d = np.linalg.norm(self.polyp_pos[:self.n_polyps], axis=1)
    # c = np.array([v.defect for v in coral.mesh.verts])
    # bbox = coral.mesh.boundingBox()
    # bbox_area = (bbox[1]-bbox[0]) * (bbox[3]-bbox[2]) * (bbox[5]-bbox[4])
    # features[0] = np.mean(d) # Mean dist from center
    # features[1] = np.std(d) # Std of dist from center
    # features[2] = np.mean(coral.polyp_pos[:, 1]) # Mean height
    # features[4] = np.std(coral.polyp_pos[:, 1]) # Std height
    # features[2] = coral.mesh.volume() / bbox_area  # Density
    # features[3:8] = np.histogram(c, bins=5, range=None, normed=True)[0]
    # for i in range(params.n_morphogens):
    #     features[8+i] = np.mean(coral.morphogens.U[i, :coral.n_polyps])
    # for i in range(coral.n_morphogens):
        # features.append(np.mean(coral.morphogens.U[i, :coral.n_polyps]))
    # for i in range(coral.n_signals):
        # features.append(np.mean(coral.polyp_signals[:coral.n_polyps, i]))
    # return features

def evaluate_novelty(genome, traits, params):
    try:
        coral = simulate_genome(genome, traits, [params])[0]
        fitness = coral.fitness()
        print('.', end='', flush=True)
        return fitness, feature_vector(coral)

    except AssertionError as e:
        print('AssertionError:', e)
        fitness = 0
        return 0, np.zeros(3)

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
                   novelty_threshold=4.0, archive_stagnation=4, ns_K=10):
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