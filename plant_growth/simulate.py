import os
import time
from plant_growth.plant import Plant
import MultiNEAT as NEAT

obj_path = os.getcwd()+'/../data/triangulated_sphere_3.obj'

def __export(plant, folder, w_i, s):
    out = open(os.path.join(folder, str(w_i), '%i.plant.obj'%s), 'w+')
    plant.export(out)

def simulate_network(steps, network, params, export_folder=None, verbose=False):
    plants = []

    for w_i, w_config in enumerate(params):
        plant = Plant(obj_path, network, w_config)

        if export_folder:
            os.mkdir(os.path.join(export_folder, str(w_i)))
            __export(plant, export_folder, w_i, 0)

        for s in range(steps):
            step_start = time.time()
            plant.step()

            if export_folder:
                __export(plant, export_folder, w_i, s+1)

            if verbose:
                print('Finished step %i: (%i polyps) (%04f)' % \
                    (s, plant.n_cells, time.time() - step_start))

            if plant.n_cells >= w_config['max_cells']:
                break

        plants.append(plant)

    return plants

def simulate_genome(steps, genome, params, export_folder=None, verbose=False):
    network = NEAT.NeuralNetwork()
    genome.BuildPhenotype(network)
    return simulate_network(steps, network, params, export_folder, verbose)
