import os
import time
from coral_growth.coral import Coral
import MultiNEAT as NEAT

obj_path = os.getcwd() + '/../data/half_sphere_smooth.obj'

def export(coral, folder, w_i, s):
    path = os.path.join(folder, str(w_i), '%i.coral.obj'%s)
    # out = open(path, 'w+')
    coral.export(path)

def simulate_network(network, net_depth, traits, params, export_folder=None, verbose=False):
    corals = []

    for w_i, w_config in enumerate(params):
        coral = Coral(obj_path, network, net_depth, traits, w_config)

        if export_folder:
            os.mkdir(os.path.join(export_folder, str(w_i)))
            export(coral, export_folder, w_i, 0)

        if verbose:
            print('Initial Fitness', coral.fitness())
            print()

        for s in range(w_config.max_steps):
            step_start = time.time()

            coral.step()

            if export_folder:
                export(coral, export_folder, w_i, s+1)

            if verbose:
                print('Finished step %i: (%i polyps) (%04f)' % \
                    (s, coral.n_polyps, time.time() - step_start))
                print('Fitness', coral.fitness(verbose))
                print()

            if coral.n_polyps >= w_config.max_polyps:
                break

        corals.append(coral)

    return corals

def simulate_genome(genome, traits, params, export_folder=None, verbose=False):
    network = NEAT.NeuralNetwork()
    genome.BuildPhenotype(network)

    genome.CalculateDepth()
    depth = genome.GetDepth()
    return simulate_network(network, depth, traits, params, export_folder, verbose)
