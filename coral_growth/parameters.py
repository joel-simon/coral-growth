import MultiNEAT as NEAT

class Parameters(NEAT.Parameters):
    def __init__(self, path=None):
        super(Parameters, self).__init__()
        # Evolution.

        self.PopulationSize = 60
        self.OldAgeTreshold = 10
        self.SpeciesMaxStagnation = 10
        self.MinSpecies = 3
        self.MaxSpecies = 8
        self.OverallMutationRate = 0.6
        self.MutateAddNeuronProb = 0.05
        self.MutateAddLinkProb = 0.05
        self.AllowLoops = False

        # Coral Growth.
        self.max_polyps = 10000
        self.max_steps = 40
        self.max_growth = .5

        self.max_face_growth = 1.5
        self.polyp_memory = 2

        self.n_morphogens = 0 # Dont manually change.
        self.morphogen_thresholds = 3
        self.morphogen_steps = 200
        self.morph_thresholds = 3

        # self.spring_strength = .5
        self.addTrait('spring_strength', (.15, .5))

        # Coral enviornment
        self.light_amount = 0.5
        self.C = 10

        if path:
            for line in open(path).readlines():
                key, value = line.strip().split('\t')
                setattr(self, key, float(value) if '.' in value else int(value))

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

    #TODO add calculate_traits

# p = Parameters()
# print(p.DontUseBiasNeuron)
