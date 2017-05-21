import math
from colorsys import hsv_to_rgb
import numpy as np
import pygame

from plant_growth.vec2D import Vec2D

def plot_image_grid(view, world):
    # pixl_arr = np.array(world.pg.img)
    # pixl_arr = np.swapaxes(np.array(world.plants[0].grid), 0, 1)
    # pixl_arr = np.fliplr(pixl_arr)
    # new_surf = pygame.pixelcopy.make_surface(pixl_arr)
    # view.surface.blit(new_surf, (0, 0))

    for plant in world.plants:
        for x in range(world.width):
            for y in range(world.height):
                if plant.grid[x, y]:
                    view.draw_pixel((x, y), (0, 200, 0, 100))
        # for (i,j), v in np.ndenumerate(pixl_arr):
        #     if v:
        #         view.draw_pixel((j,i), (255, 0, 0, 100))

import random
r = lambda: random.randint(0,255)
c = lambda: ('#%02X%02X%02X' % (r(),r(),r()))
# print
num_groups = 10
colors = [c() for _ in range(num_groups)]

def plot(view, world, title=None):
    # sh = world.sh


    width, height = world.width, world.height

    view.start_draw()
    view.draw_rect((0, 0, width, height), (0, 102, 200), width=0)
    view.draw_rect((0, 0, width, world.soil_height), (153, 102, 51, 200), width=0)

    for plant in world.plants:
        for cid in range(plant.n_cells):
            light_cell = plant.cell_light[cid]
            light_prev = plant.cell_light[plant.cell_prev[cid]]
            if light_cell > 0 and light_prev > 0:
                v_cell = plant.cell_p[cid]
                derp = v_cell + Vec2D(math.cos(world.light), math.sin(world.light)) * 1000
                view.draw_line(derp, v_cell, (255, 255, 102, 150))

    for plant in world.plants:
        view.draw_polygon(plant.polygon, (20, 200, 20))
        view.draw_lines(plant.polygon, (20, 20, 20), width=1)

        if plant.mesh:
            for face in plant.mesh.elements:
                poly = [plant.mesh.points[f] for f in face]
                view.draw_lines(poly+[poly[0]], (50, 150, 50))


        for cid in range(plant.n_cells):
            if plant.cell_flower[cid]:
                v_cell = plant.cell_p[cid]
                view.draw_circle(v_cell, 3, (200, 0, 200, 100), width=0)

    view.draw_rect((0, 0, width, world.soil_height), (153, 102, 51, 150), width=0)
    # plot_image_grid(view, world)

    for i, plant in enumerate(world.plants):
        x = (i * 400) + 10
        if title:
            view.draw_text((x, height-5), title, font=32)
            y = 40
        else:
            y = 20
        view.draw_text((x, height-y), "Plant id: %i"%i, font=16)
        view.draw_text((x, height-20-y), "Light: %.4f"%plant.light, font=16)
        view.draw_text((x, height-40-y), "Water: %.4f"%plant.water, font=16)
        view.draw_text((x, height-60-y), "Volume: %.4f"%plant.volume, font=16)
        view.draw_text((x, height-80-y), "Energy: %.4f"%plant.energy, font=16)
        view.draw_text((x, height-100-y), "consumption: %.4f"%plant.consumption, font=16)
        view.draw_text((x, height-120-y), "Num cells: %i"%plant.n_cells, font=16)
        view.draw_text((x, height-140-y), "Num flowers: %i"%plant.num_flowers, font=16)
    # view.draw_circle(world.light, 10, (255, 255, 0), width=0)
    view.end_draw()
