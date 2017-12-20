from __future__ import print_function
import random, os, sys, string, argparse, time
from datetime import datetime
from multiprocessing import Pool
import numpy as np
from tempfile import TemporaryDirectory
import MultiNEAT as NEAT
import dill

from coral_growth.simulate import simulate_network
from coral_growth.coral import Coral
from coral_growth.simulate import simulate_genome
from coral_growth.parameters import Parameters
from pykdtree.kdtree import KDTree

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
