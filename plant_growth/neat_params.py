import MultiNEAT as NEAT

params = NEAT.Parameters()
params.PopulationSize = 100
# params.DynamicCompatibility = True
# params.WeightDiffCoeff = 4.0
# params.CompatTreshold = 2.0
# params.YoungAgeTreshold = 5
params.OldAgeTreshold = 6
params.SpeciesMaxStagnation = 10
params.MinSpecies = 2
params.MaxSpecies = 8
# params.RouletteWheelSelection = False

# params.RecurrentProb = 0.0
# params.OverallMutationRate = 0.8

# params.MutateWeightsProb = 0.90
# params.WeightMutationMaxPower = 2.5
# params.WeightReplacementMaxPower = 5.0
# params.MutateWeightsSevereProb = 0.5
# params.WeightMutationRate = 0.25

# params.MaxWeight = 8

# params.MutateAddNeuronProb = 0.03
# params.MutateAddLinkProb = 0.05
# params.MutateRemLinkProb = 0.0

# params.MinActivationA = 4.9
# params.MaxActivationA = 4.9

# params.ActivationFunction_SignedSigmoid_Prob = 0.0
# params.ActivationFunction_UnsignedSigmoid_Prob = 1.0
# params.ActivationFunction_Tanh_Prob = 0.0
# params.ActivationFunction_SignedStep_Prob = 0.0

# params.CrossoverRate = 0.75  # mutate only 0.25
# params.MultipointCrossoverRate = 0.4
# params.SurvivalRate = 0.3

# params.AllowLoops = False
