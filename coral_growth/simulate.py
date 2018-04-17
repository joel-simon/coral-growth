import os
import time
import MultiNEAT as NEAT



def export(form, folder, pi, s):
    path = os.path.join(folder, str(pi), '%i.form.obj'%s)
    form.export(path)

def simulate_network(Form, network, net_depth, traits, all_params, \
                     export_folder=None, verbose=False):
    forms = []
    for pi, params in enumerate(all_params):

        if params.seed_type == 0:
            obj_path = os.getcwd() + '/../data/half_sphere_smooth.obj'
        else:
            obj_path = os.getcwd() + '/../data/triangulated_sphere_3.obj'

        form = Form(obj_path, network, net_depth, traits, params)

        if export_folder:
            os.mkdir(os.path.join(export_folder, str(pi)))
            export(form, export_folder, pi, 0)

        if verbose:
            print('Initial Fitness', form.fitness())
            print()

        for s in range(params.max_steps):
            step_start = time.time()
            form.step()

            if export_folder:
                export(form, export_folder, pi, s+1)

            if verbose:
                print('Finished step %i: (%i nodes) (%04f)' % \
                    (s, form.n_nodes, time.time() - step_start))
                print('Fitness:', form.fitness())
                print()

            if form.n_nodes >= params.max_nodes:
                break

            if form.volume >= params.max_volume:
                break

        forms.append(form)

    return forms

def simulate_genome(Form, genome, traits, params, export_folder=None, verbose=False):
    network = NEAT.NeuralNetwork()
    genome.BuildPhenotype(network)
    genome.CalculateDepth()
    depth = genome.GetDepth()
    return simulate_network(Form, network, depth, traits, params, export_folder, verbose)
