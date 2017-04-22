from __future__ import division, print_function
import math
import random
from vector import Vector
from drawer import PygameDraw
from plot import plot
from world import World
import pyvisgraph as vg
import neat
from geometry import Point


width = 750
height = 750
soil_height = 200

num_segments = 16
radius = 40

link_rest = 2*math.pi*radius / num_segments
max_link_length = 1.3 * link_rest

view = PygameDraw(width, height)
light = Point(width-10, height-10)

world = World(width, height, max_link_length, light, soil_height)

################################################################################

# indx = indexer.InnovationIndexer(0)
# conf = config.Config('config.txt')
# genome = genome.Genome.create_unconnected(0, conf)
# genome.connect_full(indx)
# net = nn.create_feed_forward_phenotype(genome)
net = None

seed_polygon = []
for i in range(num_segments):
    a = 2 * i * math.pi / num_segments
    x = width/2 + math.cos(a) * radius + (random.random()-.5)*10
    y = soil_height + math.sin(a) * radius + (random.random()-.5)*10
    seed_polygon.append(Vector(x, y))
world.add_plant(seed_polygon, net)


# seed_polygon = []
# for i in range(num_segments):
#     a = 2 * i * math.pi / num_segments
#     x = 3*width/4 + math.cos(a) * radius + (random.random()-.5)*5
#     y = height/10 + math.sin(a) * radius + (random.random()-.5)*5
#     seed_polygon.append(Vector(x, y))
# world.add_plant(seed_polygon, None)

for s in range(400):
    plot(view, world)
    world.simulation_step()
    if s % 10 == 0:
        print(s)

#
view.hold()

