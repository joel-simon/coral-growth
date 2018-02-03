from __future__ import print_function
import time
import math
import os
import numpy as np
import MultiNEAT as NEAT
from pykdtree.kdtree import KDTree

from coral_growth.simulate import simulate_genome
from coral_growth.evolution import create_initial_population, evaluate, simulate_and_save

def feature_vector(coral):
    """ Compute a descriptive feature vector for calculating novelty.
    """
    height = np.mean( coral.polyp_pos[:, 1] )
    return [ coral.light, coral.collection, height ]

def evaluate(genome, traits, params):
    """ Run the simulation and return the fitness and feature vector.
    """
    try:
        coral = simulate_genome(genome, traits, [params])[0]
        fitness = coral.fitness()
        print('.', end='', flush=True)
        return fitness, feature_vector(coral)
    except AssertionError as e:
        print('AssertionError:', e)
        fitness = 0
        return 0, [0, 0, 0]

def evaluate_genomes(genomes, params, pool):
    """ Evaluate all (parallel / serial wrapper """
    if pool:
        data = [ (g, g.GetGenomeTraits(), params) for g in genomes ]
        ff = pool.starmap(evaluate, data)
    else:
        ff = [ evaluate(g, g.GetGenomeTraits(), params) for g in genomes ]
    fitness_list, feature_list = zip(*ff)
    return fitness_list, feature_list

class Archive(object):
    def __init__(self, max_size, k):
        self.max_size = max_size
        self.k = k
        self.genomes = []
        self.fitnesses = []
        self.features = []
        self.local_fitnesses = []

    def __calculateLocalFitness(self):
        self.local_fitnesses = []
        feature_arr = np.array(self.features)
        tree = KDTree( feature_arr )
        dists, neighbors = tree.query(feature_arr, k=self.k+1)
        for i in range(len(self.genomes)):
            fitness = self.fitnesses[i]
            local_fitness = 0
            for j in range(self.k):
                neighbor_fitness = self.fitnesses[neighbors[i, j+1]]
                local_fitness += (fitness - neighbor_fitness) / (1+dists[i, j+1])
            assert not np.isnan(local_fitness)
            self.local_fitnesses.append(local_fitness)

    def __cullArchive(self):
        """ Delete genomes with low local_fitnesses to maintain max_size.
        """
        if len(self.genomes) <= self.max_size:
            return

        n_delete = len(self.genomes) - self.max_size
        indices = sorted([(lf, i) for i,lf in enumerate(self.local_fitnesses)])
        to_delete = set( i for _, i in indices[:n_delete] )
        self.genomes = [g for i,g in enumerate(self.genomes) if i not in to_delete]
        self.fitnesses = [f for i,f in enumerate(self.fitnesses) if i not in to_delete]
        self.features = [f for i,f in enumerate(self.features) if i not in to_delete]
        self.local_fitnesses = [f for i,f in enumerate(self.local_fitnesses) if i not in to_delete]
        assert len(self.genomes) <= self.max_size
        assert len(self.genomes) == len(self.fitnesses)
        assert len(self.genomes) == len(self.features)
        assert len(self.genomes) == len(self.local_fitnesses)

    def calcLocalFitnessAndUpdate(self, genomes, fitnesses, features):
        self.genomes.extend(genomes)
        self.fitnesses.extend(fitnesses)
        self.features.extend(features)
        self.__calculateLocalFitness()
        new_local_fitness = self.local_fitnesses[-len(genomes):]
        self.__cullArchive()
        return new_local_fitness

    def topNGenomes(self, n):
        indices = sorted([(lf, i) for i,lf in enumerate(self.local_fitnesses)], reverse=True)
        return [  (lf, self.genomes[i]) for lf,i in indices[:n] ]

def evolve_local( params, generations, out_dir, run_id, pool, max_size=50, K=10):
    max_ever = None
    archive = Archive(max_size, K)
    pop = create_initial_population(params)

    # Main loop
    for generation in range(generations):
        print('\n'+'#'*80)
        print(run_id, 'Starting generation %i' % generation)

        genomes = NEAT.GetGenomeList(pop)
        fitness_list, feature_list = evaluate_genomes(genomes, params, pool)
        local_fitness_list = archive.calcLocalFitnessAndUpdate(genomes, fitness_list, feature_list)
        NEAT.ZipFitness(genomes, local_fitness_list)

        print()
        maxf, meanf = max(fitness_list), sum(fitness_list) / float(len(fitness_list))
        print('Fitness - avg: %f, max:%f' % (meanf, maxf))
        print('Local Fitness - avg: %f, max:%f' % (np.mean(local_fitness_list), max(local_fitness_list)))
        print('Top 10 Local Fitness', sorted(archive.local_fitnesses, reverse=True)[:10])

        root =  os.path.join(out_dir, str(generation))
        os.mkdir(root)

        for i, (local_fitness, genome) in enumerate(archive.topNGenomes(3)):
            export_folder = os.path.join(root, str(i))
            os.mkdir(export_folder)
            print('1')
            traits = genome.GetGenomeTraits()
            print('2')
            simulate_genome(genome, traits, [params], export_folder=export_folder)
            print('3')
            # simulate_and_save(genome, params, out_dir2, generation, maxf, meanf)

        # if max_ever is None or maxf > max_ever:
        #     max_ever = maxf
        #     best = genomes[fitness_list.index(maxf)]
        #     print('New best fitness.', best.NumNeurons(), best.NumLinks())
        #     simulate_and_save(best, params, out_dir, generation, maxf, meanf)

        pop.Epoch()