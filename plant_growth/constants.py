from math import pi

USE_TIME_CYCLE = False
TIME_CYCLE = 100 #todo evovle
NUM_CELL_TYPES = 3
FLOWER_COST = 1
WATER_PER_CELL = .4

USE_AGE = False

MAX_CELLS = 12000
NUM_GENERATIONS = 100
SIMULATION_STEPS = 100
WORLD_SIZE = 100
CELL_GROWTH_SCALAR = .5

#Genome
# 3 in for light, water, flower and curvature
# 1 out for growth and is_flower
NUM_INPUTS = 4 + NUM_CELL_TYPES + USE_AGE
NUM_OUTPUTS = 2 + NUM_CELL_TYPES


PLANT_EFFICIENCY = 4

MAX_EDGE_LENGTH = 2
MAX_ANGLE = .98 * 2*pi


HASH_CELL_SIZE = MAX_EDGE_LENGTH*.5
# cell_min_energy = .1
# cell_growth_energy_usage = 1*(1-cell_min_energy) # Full growth will use 90% of energy.

# cell_growth_energy_usage = .05


MAX_DEFORMATION = .02
PHYSICS_INTERVAL = 10
use_physics = False


