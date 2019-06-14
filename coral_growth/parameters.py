import MultiNEAT as NEAT

class Parameters(object):
    def __init__(self, path=None):
        self.traits_calculated = False

        # Evolution.
        self.neat = NEAT.Parameters()
        self.neat.PopulationSize = 80
        self.neat.OldAgeTreshold = 10
        self.neat.SpeciesMaxStagnation = 10
        self.neat.MinSpecies = 2
        self.neat.MaxSpecies = 8
        self.neat.OverallMutationRate = 0.6
        self.neat.MutateAddNeuronProb = 0.05
        self.neat.MutateAddLinkProb = 0.05
        self.neat.AllowLoops = False

        # Coral Growth.
        self.seed_type = 1 # 0 is flat bottom and 1 is round, use 0 with 'has_ground'

        self.max_nodes = 15000
        self.max_volume = 200.0
        self.max_steps = 150
        self.max_growth = .25
        self.max_defect = 1.5
        self.max_face_growth = 1.3
        self.C = .3

        self.n_signals = 2
        self.signal_thresholds = 3 # if n thresholds, n+1 options.

        self.n_memory = 2

        self.n_morphogens = 2
        self.morphogen_thresholds = 3
        self.morphogen_steps = 200

        self.use_gravity = True
        self.use_polar_direction = True
        self.has_ground = False

        # These are coral specific and should get re-factored somewhere...
        self.light_amount = 0.7
        self.gradient_height = 6.0
        self.gradient_bottom = 0.2
        self.collection_radius = 5

        self.addTrait('energy_diffuse_steps', (0, 8), 'int')

        if path:
            for line in open(path).readlines():
                key, value = line.strip().split('\t')
                if value == 'True': value = '1'
                if value == 'False': value = '0'
                setattr(self, key, float(value) if '.' in value else int(value))

    def addTrait(self, name, vrange, ttype='float'):
        trait = {
            'details': {
                'max': max(vrange),
                'min': min(vrange),
                'mut_power': abs(vrange[1] - vrange[0]) * .1,
                'mut_replace_prob': 0.1
            },
            'importance_coeff': 1.0,
            'mutation_prob': 0.2,
            'type': ttype
        }

        if ttype == 'int':
            trait['details']['mut_power'] = 1

        self.neat.SetGenomeTraitParameters(name, trait)

    def calculateTraits(self):
        assert not self.traits_calculated
        self.traits_calculated = True

        for i in range(self.n_morphogens):
            self.addTrait('K%i'%i, (.03, .08))
            self.addTrait('F%i'%i, (.01, .06))
            self.addTrait('diffU%i'%i, (.005, .02))
            self.addTrait('diffV%i'%i, (.0025, .01))

        for i in range(self.n_signals):
            # self.addTrait('signal_decay%i'%i, (0.0, .4))
            self.addTrait('signal_diffuse_steps%i'%i, (0, 8), ttype='int')

    def write(self, neat_path, sim_path):
        self.neat.Save(neat_path)
        with open(sim_path, 'w') as out:
            for key, value in sorted(vars(self).items()):
                if key != 'neat':
                    out.write(key+'\t'+str(value)+'\n')
