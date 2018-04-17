from __future__ import print_function
import time
import MultiNEAT as NEAT
from coral_growth.evolution import create_initial_population, evaluate, simulate_and_save

def evolve_neat(Form, params, generations, out_dir, run_id, pool):
    pop = create_initial_population(Form, params)
    max_ever = None
    t = time.time()

    for generation in range(generations):
        print(run_id, 'Starting generation', generation)
        genomes = NEAT.GetGenomeList(pop)

        if pool:
            data = [ (Form, g, g.GetGenomeTraits(), params) for g in genomes ]
            fitnesses = pool.starmap(evaluate, data)
        else:
            fitnesses = [ evaluate(Form, g, g.GetGenomeTraits(), params) for g in genomes ]

        NEAT.ZipFitness(genomes, fitnesses)

        maxf, meanf = max(fitnesses), sum(fitnesses) / float(len(fitnesses))
        runtime = time.time() - t
        t = time.time()

        print()
        print('Generation %i ran in %f, %f per coral' % \
                                    (generation, runtime, runtime/len(genomes)))
        print('Max fitness:', maxf, 'Mean fitness:', meanf)

        if max_ever is None or maxf > max_ever:
            best = pop.GetBestGenome()
            max_ever = maxf
            print('New best fitness.', best.NumNeurons(), best.NumLinks())
            coral = simulate_and_save(Form, best, params, out_dir, generation, maxf, meanf)[0]

        pop.Epoch()
        print('#'*80)

    print('Run Complete.')
