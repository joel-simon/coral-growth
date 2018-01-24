import MultiNEAT as NEAT

class Parameters(NEAT.Parameters):
    def __init__(self, path=None):
        super(Parameters, self).__init__()
        self.traits_calculated = False

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
        self.max_defect = 1.0

        self.max_face_growth = 1.5
        self.n_memory = 1
        self.n_signals = 1

        self.n_morphogens = 0
        self.morphogen_thresholds = 3
        self.morphogen_steps = 200

        self.height_boost = 1

        # Coral enviornment
        self.light_amount = 0.5
        self.C = 10

        if path:
            for line in open(path).readlines():
                key, value = line.strip().split('\t')
                if value == 'True': value = '1'
                if value == 'False': value = '0'
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

    def calculateTraits(self):
        assert not self.traits_calculated
        self.traits_calculated = True

        for i in range(self.n_morphogens):
            self.addTrait('K%i'%i, (.03, .08))
            self.addTrait('F%i'%i, (.01, .06))
            # self.addTrait('diffU%i'%i, (.005, .02))
            # self.addTrait('diffV%i'%i, (.0025, .01))
            self.addTrait('diffU%i'%i, (.01, .01))
            self.addTrait('diffV%i'%i, (.005, .005))

        for i in range(self.n_memory):
            self.addTrait('mem_decay%i'%i, (0.0, 1.0))
