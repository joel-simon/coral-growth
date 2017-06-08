from math import pi
#Genome
NUM_INPUTS = 6
NUM_OUTPUTS = 2

MAX_CELLS = 5000
NUM_GENERATIONS = 200
SIMULATION_STEPS = 300

WORLD_WIDTH = 1200
WORLD_HEIGHT = 800
SOIL_HEIGHT = 250

CELL_MAX_GROWTH = 3.0

SEED_SEGMENTS = 16
SEED_RADIUS = 8

__starting_volume = (pi*SEED_RADIUS**2)
__starting_production = SEED_SEGMENTS/4
PLANT_EFFICIENCY = (2*__starting_volume)/__starting_production # A starting seed is at 50% energy usage.

WATER_EFFICIENCY = .5
LIGHT_EFFICIENCY = 1

FLOWER_COST = 1.0

__default_length = (2*pi*SEED_RADIUS / SEED_SEGMENTS)
MAX_EDGE_LENGTH = 1.5 * __default_length
MIN_EDGE_LENGTH = .5 * __default_length
MAX_ANGLE = .97 * 2*pi

# WORLD_NUM_BUCKETS = 30
# WORLD_GROUP_WIDTH = MAX_EDGE_LENGTH * 1.5
# WORLD_BUCKET_SIZE = 500

CELL_SIZE = MAX_EDGE_LENGTH * 1.5
