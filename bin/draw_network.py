import MultiNEAT as NEAT
import os, sys
sys.path.append(os.path.abspath('..'))
from coral_growth.draw_net import draw_net

assert len(sys.argv) == 2

path = sys.argv[1]
genome = NEAT.Genome(path)
network = NEAT.NeuralNetwork()
genome.BuildPhenotype(network)

in_names = ['Light', 'Curvature', 'Gravity', 'Chemical 1U', 'Chemical 2U', 'Bias']
out_names = ['Growth', 'Chemical 1V', 'Chemical 2V']

draw_net(network, in_names, out_names, view=True, filename = path+'.digraph')
