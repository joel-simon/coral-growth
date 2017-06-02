import sys, os
sys.path.append(os.path.abspath('.'))
from math import pi as M_PI
from math import cos, sin
from collections import Counter
import pygame

from plant_growth.pygameDraw import PygameDraw

a_n = 16
b_n = 24

def intersect(p0_x, p0_y, p1_x, p1_y, p2_x, p2_y, p3_x, p3_y):
    s1_x = p1_x - p0_x
    s1_y = p1_y - p0_y
    s2_x = p3_x - p2_x
    s2_y = p3_y - p2_y

    d = -s2_x * s1_y + s1_x * s2_y

    # Parallel (Consider co-linear as not intersecting)
    if d == 0.0:
        return False

    s = (-s1_y * (p0_x - p2_x) + s1_x * (p0_y - p2_y)) / d
    t = ( s2_x * (p0_y - p2_y) - s2_y * (p0_x - p2_x)) / d

    if (s >= 0 and s <= 1 and t >= 0 and t <= 1):
        i_x = p0_x + (t * s1_x)
        i_y = p0_y + (t * s1_y)
        return (i_x, i_y)

    return False

################################################################################
""" Create circles.
"""
def create_circle(x, y, r, n):
    circle = []
    for i in range(n):
        a = 2 * i * M_PI / n
        circle.append((x + cos(a) * r, y + sin(a) * r))
    return circle
    # circle_b.append((offset_b[0] + cos(a) * radius_b, offset_b[1] + sin(a) * radius_b))

################################################################################
""" Calculate collisions.
"""
def create_intersections(circle_a, circle_b):
    intersections = []

    for i0, p0 in enumerate(circle_a):
        i1, p1 = (i0+1)%a_n, circle_a[(i0+1)%a_n]
        for i2, p2 in enumerate(circle_b):
            i3, p3 = (i2+1)%b_n, circle_b[(i2+1)%b_n]
            point = intersect(p0[0], p0[1], p1[0], p1[1], p2[0], p2[1], p3[0], p3[1])
            if point:
                x, y = point
                intersections.append((x, y, i0, i1, i2, i3))

    return intersections

################################################################################
""" Locate intersecting segments.
"""
def isLeft(a, b, c):
    """ segment (a, b) and point c to check against.
    """
    return ((b[0] - a[0])*(c[1] - a[1]) > (b[1] - a[1])*(c[0] - a[0]))

def project(a, b, c):
    """ get the projected point of c onto segment (a, b)
    """
    px = b[0] - a[0]
    py = b[1] - a[1]
    d = (px * px + py * py)
    if d == 0:
        return a
    u = ((c[0] - a[0]) * px + (c[1] - a[1]) * py) / d
    x = a[0] + u * px
    y = a[1] + u * py
    return x, y

def step(i, direction, n):
    if direction == 1:
        i = (i + 1) % n
    else:
        i -= 1
        if i < 0:
            i += n
    return i

def foo(circle, id, direction, flagged, terminal):
    n = len(circle)
    flagged.add(id)
    id = step(id, direction, n)

    while id not in flagged and id not in terminal:
        flagged.add(id)
        id = step(id, direction, n)

key = lambda x: tuple(sorted(x))

def create_zipper_halfs(circle_a, circle_b):
    zipper_halfs = []

    flagged_a = set()
    flagged_b = set()

    terminal_a = set()
    terminal_b = set()

    intersections = create_intersections(circle_a, circle_b)

    intersections_per_segment_a = Counter()
    intersections_per_segment_b = Counter()

    foo_a = []
    foo_b = []

    for x, y, a0, a1, b0, b1 in intersections:
        intersections_per_segment_a[key((a0, a1))] += 1
        intersections_per_segment_b[key((b0, b1))] += 1

    for x, y, i0, i1, i2, i3 in intersections:
        p0, p1 = circle_a[i0], circle_a[i1]
        p2, p3 = circle_b[i2], circle_b[i3]

        if intersections_per_segment_a[key((i0, i1))] % 2 == 1:
            if isLeft(p0, p2, p3):
                flagged_a.add(i0)
                terminal_a.add(i1)
                foo_a.append((i0, -1))
            else:
                flagged_a.add(i1)
                terminal_a.add(i0)
                foo_a.append((i1, 1))
        else:
            flagged_a.add(i0)
            flagged_a.add(i1)

        if intersections_per_segment_b[key((i2, i3))] % 2 == 1:
            if isLeft(p2, p0, p1):
                flagged_b.add(i2)
                terminal_b.add(i3)
                foo_b.append((i2, -1))
            else:
                flagged_b.add(i3)
                terminal_b.add(i2)
                foo_b.append((i3, 1))
        else:
            flagged_b.add(i2)
            flagged_b.add(i3)

    for a, d in foo_a:
        foo(circle_a, a, d, flagged_a, terminal_a)

    for b, d in foo_b:
        foo(circle_b, b, d, flagged_b, terminal_b)

    return flagged_a, flagged_b

################################################################################
""" Visualize.
"""
w, h = 400, 400
view = PygameDraw(w, h)
color_a = (0,200,0)
color_b = (0,0,200)
radius = 50

circle_a = create_circle(200, 200, radius, a_n)

while True:
    view.start_draw()
    x, y = pygame.mouse.get_pos()
    y = h - y
    circle_b = create_circle(x, y, radius, b_n)

    flagged_a, flagged_b = create_zipper_halfs(circle_a, circle_b)

    view.draw_polygon(circle_a, color_a, t=2)
    view.draw_polygon(circle_b, color_b, t=2)

    for i in flagged_a:
        p = circle_a[i]
        view.draw_circle(p, 4, color_a)

    for i in flagged_b:
        p = circle_b[i]
        view.draw_circle(p, 4, color_b)

    view.end_draw()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()






