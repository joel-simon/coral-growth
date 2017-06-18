from math import pi
#Genome
NUM_INPUTS = 5
NUM_OUTPUTS = 4

MAX_CELLS = 3000
NUM_GENERATIONS = 100
SIMULATION_STEPS = 300

WORLD_WIDTH = 1200
WORLD_HEIGHT = 800
SOIL_HEIGHT = 50

SEED_SEGMENTS = 16#32
SEED_RADIUS = 64#32

USE_TIME_CYCLE = True
TIME_CYCLE = 100 #todo evovle

__starting_volume = (pi*SEED_RADIUS**2)
__starting_production = SEED_SEGMENTS/4
PLANT_EFFICIENCY = (2*__starting_volume)/__starting_production # A starting seed is at 50% energy usage.

__default_length = (2*pi*SEED_RADIUS / SEED_SEGMENTS)
MAX_EDGE_LENGTH = 2.0 * __default_length
MIN_EDGE_LENGTH = .5 * __default_length
MAX_ANGLE = .98 * 2*pi

CELL_MAX_GROWTH = .2 * SEED_RADIUS

CELL_SIZE = MAX_EDGE_LENGTH * 1.25

cell_min_energy = .1
# cell_growth_energy_usage = 1*(1-cell_min_energy) # Full growth will use 90% of energy.


cell_growth_energy_usage = .05


use_physics = False
