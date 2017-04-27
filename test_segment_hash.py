from modules.segmenthash import SegmentHash
from collections import namedtuple
import math, sys
import random
from geometry import Point
from drawer import PygameDraw
from plot import plot
import pygame
import numpy as np
segment = namedtuple('segment', ['id', 'p1', 'p2'])

width = 500
height = 500
center = Point(width/2, height/2)
view = PygameDraw(width, height)

segment_length = 20.0
num_segments = 1

sh = SegmentHash(width, height, 20)

segments = []
for id in range(num_segments):
    p1 = Point(.1*width + random.random() * width*.8, .1*height+ random.random() * height*.8)
    a = random.random() * 2*3.14159
    p2 = Point(math.cos(a)*segment_length, math.sin(a)*segment_length)
    p2.x += p1.x
    p2.y += p1.y

    sh.segment_add(id, p1, p2)
    segments.append(segment(id, p1, p2))


# n = 200
# for i in range(n):
#     p1 = Point(random.random() * width, random.random() * height)
#     a = list(sh.segment_intersect(Point(0,0), p1))



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

    for x, y in sh._segment_supercover(center, mouse):
        view.draw_rect((x*sh.d, (y*sh.d), sh.d, sh.d), (0,200,0), width=0)

    view.draw_line(center, mouse, (0,0,0), width=2)

    for segment in segments:
       view.draw_line(segment.p1, segment.p2, (0,0,0), width=4)

    for id in sh.segment_intersect(center, mouse):
        view.draw_line(segments[id].p1, segments[id].p2, (200,0,0), width=4)

    view.end_draw()
