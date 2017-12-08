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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("max_polyps", default=10000, help="Generations.", type=int)
    parser.add_argument("time_steps", default=100, help="Output dir.", type=int)
    parser.add_argument("genome_path", help="")
    parser.add_argument("trait_path", help="")
    args = parser.parse_args()

    traits = ast.literal_eval(open(args.trait_path, 'r').readlines()[0])
    genome = NEAT.Genome(args.genome_path)

    print(traits)

    world_configs = {
        'max_polyps': args.max_polyps,
        'growth_scalar': .5,
        'max_face_growth': 1.0,
        'max_edge_growth': 1.5,
        'morphogen_steps': 200,
        'polyp_memory': 2,
        'morph_thresholds': 3,
    }

    with TemporaryDirectory() as tmp_dir:
        simulate_genome(args.time_steps, genome, traits, [world_configs],
                        export_folder=tmp_dir, verbose=True)
        exported = os.path.join(tmp_dir, '0')
        files = [f for f in os.listdir(exported) if '.coral.obj' in f]
        files = sorted(files, key=lambda f: int(f.split('.')[0]))
        files = [os.path.join(exported, f) for f in files]
        view = AnimationViewer(files, (1000, 1000))
        view.main_loop()
