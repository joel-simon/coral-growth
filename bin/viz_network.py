import MultiNEAT as NEAT
import os, sys
sys.path.append(os.path.abspath('..'))
from plant_growth import viz


# path = '/home/simonlab/Dropbox/plant_growth/bin/flowers/out_August_16_2017_17-41_CSSO/best_13'
# path = '/home/simonlab/Dropbox/plant_growth/bin/flowers/out_August_16_2017_17-40_A1UA/best_38'
# path = '/home/simonlab/Dropbox/plant_growth/bin/flowers/out_August_16_2017_16-23_Z78M/best_62'
path = sys.argv[1]
genome = NEAT.Genome(path)
network = NEAT.NeuralNetwork()
genome.BuildPhenotype(network)
viz.plot_nn(network)
