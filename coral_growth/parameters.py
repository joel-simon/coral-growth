import MultiNEAT as NEAT

class Parameters(NEAT.Parameters):
    def __init__(self):
        super(Parameters, self).__init__()
        # Evolution.
        self.PopulationSize = 60
        self.OldAgeTreshold = 6
        self.SpeciesMaxStagnation = 10
        self.MinSpecies = 2
        self.MaxSpecies = 8
        self.OverallMutationRate = 0.8
        self.MutateAddNeuronProb = 0.05
        self.MutateAddLinkProb = 0.05

        # Coral Growth.
        self.max_polyps = 10000
        self.max_steps = 100
        self.growth_scalar = .20
        self.max_face_growth = 1.5
        self.polyp_memory = 2

        self.n_morphogens = 0 # Dont manually change.
        self.morphogen_thresholds = 3
        self.morphogen_steps = 200
        self.morph_thresholds = 3
        self.vc = .5
        # self.light_fitness_percent = .5

        self.addTrait('spring_strength', (.1, .7))

        # Coral enviornment
        self.light_amount = 1.0
        # light = light_bottom + ( 1 - light_bottom ) * polyp_height / world_depth
        # self.world_depth = 5
        # self.light_decay = .15 # Percent of light lost every unit height.

    def addTrait(self, name, vrange, type='float'):
        trait = {
            'details': {
                'max': max(vrange),
                'min': min(vrange),
                'mut_power': abs(vrange[1] - vrange[0]) / 4,
                'mut_replace_prob': 0.1
            },
            'importance_coeff': 1.0,
            'mutation_prob': 0.3,
            'type': 'float'
        }
        self.SetGenomeTraitParameters(name, trait)

    def addMorphogen(self):
        i = self.n_morphogens
        self.addTrait('K%i'%i, (.03, .08))
        self.addTrait('F%i'%i, (.01, .06))
        self.addTrait('diffU%i'%i, (.005, .02))
        self.addTrait('diffV%i'%i, (.0025, .01))
        self.n_morphogens += 1
