#!/usr/bin/env python3
""" For simulating a genome.
"""
import os, sys, random, argparse, pickle
sys.path.append(os.path.abspath('..'))
random.seed(123)
import ast
from tempfile import TemporaryDirectory
import MultiNEAT as NEAT
from coral_growth.coral import Coral
from coral_growth.simulate import simulate_genome
from coral_growth.viewer import AnimationViewer
from coral_growth.parameters import Parameters

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root_path", help="")
    parser.add_argument("generation", type=int, help="")
    parser.add_argument("--max_polyps", default=10000, help="Generations.", type=int)
    parser.add_argument("--max_steps", default=100, help="Output dir.", type=int)

    args = parser.parse_args()

    genome_path = os.path.join(args.root_path, 'genome_%i'%args.generation)
    trait_path = os.path.join(args.root_path, 'best_%i_traits.txt'%args.generation)
    params_path = os.path.join(args.root_path, 'sim_params.txt')


    traits = ast.literal_eval(open(trait_path, 'r').readlines()[0])
    genome = NEAT.Genome(genome_path)

    params = Parameters(params_path)
    params.max_steps = args.max_steps
    params.max_polyps = args.max_polyps

    with TemporaryDirectory() as tmp_dir:
        simulate_genome(genome, traits, [params], export_folder=tmp_dir, verbose=True)
        exported = os.path.join(tmp_dir, '0')
        files = [f for f in os.listdir(exported) if f.endswith('.coral.obj')]
        files = sorted(files, key=lambda f: int(f.split('.')[0]))
        files = [os.path.join(exported, f) for f in files]
        view = AnimationViewer(files, (1000, 1000))
        view.main_loop()
