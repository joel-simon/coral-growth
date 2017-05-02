import sys
from plant_growth import constants
from plant_growth.pygameDraw import PygameDraw
from plant_growth.plot import plot
from plant_growth.evaluate import evaluate
import MultiNEAT as NEAT

view = PygameDraw(constants.WORLD_WIDTH, constants.WORLD_HEIGHT)

def display_func(world):
    plot(view, world)

if __name__ == '__main__':
    assert(len(sys.argv) == 2)
    path = sys.argv[1]
    genome = NEAT.Genome(path)
    evaluate(genome, display=None)
    # view.hold()
