# import math

# from coral_growth import constants, neat_params
# from coral_growth.world import World
# from coral_growth.pygameDraw import PygameDraw
# from coral_growth.plot import plot

# import MultiNEAT as NEAT

# genome = NEAT.Genome(
#     0, # ID
#     constants.NUM_INPUTS,
#     0, # NUM_HIDDEN
#     constants.NUM_OUTPUTS,
#     False, # FS_NEAT
#     NEAT.ActivationFunction.UNSIGNED_SIGMOID, # Output activation function
#     NEAT.ActivationFunction.UNSIGNED_SIGMOID, # Hidden activation function..
#     0, # Seed type, must be 1 to have hidden nodes.
#     neat_params.params
# )

# constants.SEED_SEGMENTS = 128

# net = NEAT.NeuralNetwork()
# genome.BuildPhenotype(net)

# world_params = {
#     'width': constants.WORLD_WIDTH,
#     'height': constants.WORLD_HEIGHT,
#     'soil_height': constants.SOIL_HEIGHT,
#     'max_corals': 1,
# }

# world = World(world_params)

# world.add_coral(300, 300, 100, net, 1)

# view = PygameDraw(600, 600)
# for _ in range(1):
#     # print('.')
#     world.simulation_step()
#     plot(view, world)
# view.hold()
