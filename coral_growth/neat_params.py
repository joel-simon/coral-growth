import MultiNEAT as NEAT

params = NEAT.Parameters()
params.PopulationSize = 40

params.OldAgeTreshold = 6
params.SpeciesMaxStagnation = 10
params.MinSpecies = 2
params.MaxSpecies = 5

params.OverallMutationRate = 0.8

params.MutateAddNeuronProb = 0.05
params.MutateAddLinkProb = 0.05

# TRAITS
n_thresholds = 3
params.MutateGenomeTraitsProb = 0.3

for i in range(n_morphogens):
    K = {'details': {'max': .08, 'min': .03, 'mut_power': .01, 'mut_replace_prob': 0.1},
         'importance_coeff': 0.5, 'mutation_prob': 0.1, 'type': 'float'
        }

    F = { 'details': {'max': .06, 'min': .01, 'mut_power': .01, 'mut_replace_prob': 0.1 },
          'importance_coeff': 0.5, 'mutation_prob': 0.1, 'type': 'float'
        }

    params.SetGenomeTraitParameters('K%i' %i, K)
    params.SetGenomeTraitParameters('F%i' %i, F)
