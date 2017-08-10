from math import pi

USE_TIME_CYCLE = True
TIME_CYCLE = 100 #todo evovle
NUM_CELL_TYPES = 2

#Genome
# 2 in for light and curvature
# 1 out for growth
NUM_INPUTS = 2 + NUM_CELL_TYPES
NUM_OUTPUTS = 1 + NUM_CELL_TYPES

MAX_CELLS = 12000
NUM_GENERATIONS = 50
SIMULATION_STEPS = 40



SOIL_HEIGHT = 50
WORLD_SIZE = 100


PLANT_EFFICIENCY = 2.5#(2*__starting_volume)/__starting_production # A starting seed is at 50% energy usage.

# __default_length = (2*pi*SEED_RADIUS / SEED_SEGMENTS)
MAX_EDGE_LENGTH = 2#s2.0 * __default_length
# MIN_EDGE_LENGTH = .5 * __default_length
MAX_ANGLE = .98 * 2*pi


CELL_GROWTH_SCALAR = .5

HASH_CELL_SIZE = MAX_EDGE_LENGTH*.5

cell_min_energy = .1
# cell_growth_energy_usage = 1*(1-cell_min_energy) # Full growth will use 90% of energy.

cell_growth_energy_usage = .05


MAX_DEFORMATION = .02
PHYSICS_INTERVAL = 10
use_physics = False


