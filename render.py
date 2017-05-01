import os
import sys
from plant_growth import constants
from plant_growth.pygameDraw import PygameDraw
from plant_growth.plot import plot
from plant_growth.evaluate import evaluate
import MultiNEAT as NEAT
from subprocess import call
from tempfile import TemporaryDirectory

view = PygameDraw(constants.WORLD_WIDTH, constants.WORLD_HEIGHT)
frame = 0

if __name__ == '__main__':
    assert(len(sys.argv) == 2)

    with TemporaryDirectory() as temp_dir:
        print('Created temp directory.')

        def display_func(world):
            global frame
            path = os.path.join(temp_dir, '{:04d}.jpg'.format(frame))
            plot(view, world)
            view.save(path)
            frame += 1

        file_path = sys.argv[1]
        assert(os.path.exists(file_path))
        genome = NEAT.Genome(file_path)
        print('Loaded', file_path)
        print('Generating images...')
        evaluate(genome, display=display_func)
        print('Finished generating images.')

        print('Generating movie...')
        call("ffmpeg -r 30 -f image2 -i "+temp_dir+"/%04d.jpg out2.mp4", shell=True)
        print('Finished generating movie.')