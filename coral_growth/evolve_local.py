from __future__ import print_function
import time
import math
import os
from os.path import join as pjoin
import numpy as np
import MultiNEAT as NEAT
from pykdtree.kdtree import KDTree

from coral_growth.simulate import simulate_genome
from coral_growth.evolution import *

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

            # Get the percent of nearest-neighbors this is more it than.
            local_fitness = 0
            for j in range(1, self.k+1):
                neighbor_fitness = self.fitnesses[neighbors[i, j]]
                if fitness > neighbor_fitness:
                    local_fitness += 1.0 / self.k

            # Multiply it by the distance to those nearest neighbors.
            local_fitness *= np.mean( dists[ i, 1: ] )
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
        self.genomes.extend([g.GetID() for g in genomes])
        self.fitnesses.extend(fitnesses)
        self.features.extend(features)
        self.__calculateLocalFitness()
        new_local_fitness = self.local_fitnesses[-len(genomes):]
        self.__cullArchive()
        return new_local_fitness

    def topNGenomes(self, n):
        indices = sorted([(lf, i) for i,lf in enumerate(self.local_fitnesses)], reverse=True)
        return [  (lf, self.genomes[i]) for lf,i in indices[:n] ]

def evolve_local( params, generations, out_dir, run_id, pool, max_size=400, K=10, N=5):
    max_ever = None
    archive = Archive(max_size, K)
    pop = create_initial_population(params)
    seen_genomes = set()

    corals_dir = pjoin(out_dir, 'corals')
    hist_dir = pjoin(out_dir, 'local_fitness_history')
    best_dir = pjoin(out_dir, 'best')
    os.mkdir(corals_dir)
    os.mkdir(hist_dir)
    os.mkdir(best_dir)

    # Main loop
    for generation in range(generations):
        print('\n'+'#'*80)
        print(run_id, 'Starting generation %i' % generation)

        genomes = NEAT.GetGenomeList(pop)
        fitness_list, feature_list = evaluate_genomes_novelty(genomes, params, pool)
        local_fitness_list = archive.calcLocalFitnessAndUpdate(genomes, fitness_list, feature_list)
        NEAT.ZipFitness(genomes, local_fitness_list)

        current = { g.GetID(): g for g in genomes }

        print()
        maxf, meanf = max(fitness_list), sum(fitness_list) / float(len(fitness_list))
        print('Fitness - avg: %f, max:%f' % (meanf, maxf))
        print('Local Fitness - avg: %f, max:%f' % (np.mean(local_fitness_list), max(local_fitness_list)))
        print('Top 5 Local Fitness', sorted(archive.local_fitnesses, reverse=True)[:5])

        np.save(pjoin(hist_dir, "%i"%generation), np.array(archive.local_fitnesses))
        top_n = archive.topNGenomes(N)

        avg_local_fitness = sum(f for f, gid in top_n)

        if max_ever is None or avg_local_fitness > max_ever:
            print('New best average best local fitness!', avg_local_fitness)
            max_ever = avg_local_fitness

            for i, (local_fitness, genome_id) in enumerate(top_n):
                # Only save a genome if we have not seen it before.
                if genome_id in current:
                    genome = current[ genome_id ]
                    traits = genome.GetGenomeTraits()

                    coral_dir = pjoin(corals_dir, "%i_%i"%(generation, genome_id))
                    os.mkdir(coral_dir)

                    genome.Save(pjoin(coral_dir, 'genome.txt'))

                    with open(pjoin(coral_dir, 'traits.txt'), "w+") as f:
                        for k, v in sorted(traits.items()):
                            f.write("%s\t%f\n"%(k, v))

                    simulate_genome(genome, traits, [params], export_folder=coral_dir)

            with open(pjoin(best_dir, '%i.txt'%generation), 'w+') as out:
                for local_fitness, genome_id in top_n:
                    out.write('%i\t%f\n'%(genome_id, local_fitness))

        pop.Epoch()