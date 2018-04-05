import MultiNEAT as NEAT
import os, sys
sys.path.append(os.path.abspath('..'))
from coral_growth.draw_net import draw_net
from coral_growth.parameters import Parameters
from coral_growth.coral import Coral

assert len(sys.argv) == 3

path = sys.argv[1]
params_path = sys.argv[2]

params = Parameters(params_path)
genome = NEAT.Genome(path)
network = NEAT.NeuralNetwork()
genome.BuildPhenotype(network)

in_names = ['Light', 'Collection', 'Energy', 'Gravity', 'Curvature']

out_names = ['Growth']

for i in range(params.n_morphogens):
    in_names.append('Morphogen%i U'%i)
    out_names.append('Morphogen%i V'%i)

for i in range(params.n_signals):
    in_names.append('Signal%i in'%i)
    out_names.append('Signal%i out'%i)

in_names.append('Bias')

n_in, n_out = Coral.calculate_inouts(params)

assert n_in == len(in_names)
assert n_out == len(out_names)

print(n_in, n_out)

draw_net(network, in_names, out_names, view=True, filename = path+'.digraph')
