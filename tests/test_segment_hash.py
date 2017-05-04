# import pyximport; pyximport.install()
import sys
import math
import random
from collections import namedtuple

from plant_growth.segmenthashx import SegmentHash

from plant_growth.geometry import Point
from plant_growth.pygameDraw import PygameDraw
from plant_growth.plot import plot

import pygame
import numpy as np

width = 500
height = 500
center = Point(width/2, height/2)
view = PygameDraw(width, height)

segment_length = 20.0
num_segments = 100

sh = SegmentHash(width, height, 20, num_segments)

segments = []
for id in range(num_segments):
    p0 = Point(.1*width + random.random() * width*.8, .1*height+ random.random() * height*.8)
    a = random.random() * 2*3.14159
    p1 = Point(math.cos(a)*segment_length, math.sin(a)*segment_length)
    p1.x += p0.x
    p1.y += p0.y

    sh.add_segment(id, p0.x, p0.y, p1.x, p1.y)
    segments.append((p0, p1))

while True:
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        sys.exit()

    view.start_draw()


    mouse = Point(*pygame.mouse.get_pos())
    mouse.y = height - mouse.y

    for (i,j), v in np.ndenumerate(sh.data):
        if len(v):
            view.draw_rect((i*sh.d, j*sh.d, sh.d, sh.d), (100,100,0), width=0)
        view.draw_rect((i*sh.d, (j*sh.d), sh.d, sh.d), (0,0,0), width=1)

    # n = sh._segment_supercover(center, mouse)
    # for i in range(n):
    #     x = sh.buff[i, 0]
    #     y = sh.buff[i, 1]
    # # for x, y in sh._segment_supercover(center, mouse):
    #     view.draw_rect((x*sh.d, (y*sh.d), sh.d, sh.d), (0,200,0), width=0)

    view.draw_line(center, mouse, (0,0,0), width=2)

    for segment in segments:
       view.draw_line(segment[0], segment[1], (0,0,0), width=4)

    for id in sh.segment_intersect(center.x, center.y, mouse.x, mouse.y):
        view.draw_line(segments[id][0], segments[id][1], (200,0,0), width=4)

    view.end_draw()
