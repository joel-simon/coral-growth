import os
import time
from coral_growth.coral import Coral
import MultiNEAT as NEAT

obj_path = os.getcwd()+'/../data/triangulated_sphere_3.obj'

def __export(coral, folder, w_i, s):
    out = open(os.path.join(folder, str(w_i), '%i.coral.obj'%s), 'w+')
    coral.export(out)

def simulate_network(steps, network, params, export_folder=None, verbose=False):
    corals = []

    for w_i, w_config in enumerate(params):
        coral = Coral(obj_path, network, w_config)

        if export_folder:
            os.mkdir(os.path.join(export_folder, str(w_i)))
            __export(coral, export_folder, w_i, 0)

        for s in range(steps):
            step_start = time.time()
            coral.step()

            if export_folder:
                __export(coral, export_folder, w_i, s+1)

            if verbose:
                print('Finished step %i: (%i polyps) (%04f)' % \
                    (s, coral.n_polyps, time.time() - step_start))

            if coral.n_polyps >= w_config['max_polyps']:
                break

        corals.append(coral)

    return corals

def simulate_genome(steps, genome, params, export_folder=None, verbose=False):
    network = NEAT.NeuralNetwork()
    genome.BuildPhenotype(network)
    return simulate_network(steps, network, params, export_folder, verbose)
