import math
from colorsys import hsv_to_rgb
import numpy as np
import pygame

from plant_growth.vec2D import Vec2D

def plot(view, world, draw_segmentgrid=False):
    sh = world.sh

    width, height = sh.width, sh.height

    view.start_draw()
    view.draw_rect((0, 0, width, height), (0, 102, 255), width=0)
    view.draw_rect((0, 0, width, world.soil_height), (153, 102, 51, 200), width=0)


    # pixl_arr = np.array(world.pg.img)
    # pixl_arr = np.swapaxes(np.array(world.plants[0].grid), 0, 1)
    # pixl_arr = np.fliplr(pixl_arr)
    # print(pixl_arr)
    # new_surf = pygame.pixelcopy.make_surface(pixl_arr)
    # view.surface.blit(new_surf, (0, 0))
    # view.end_draw()
    # return

    # Draw Plant Mass
    for plant in world.plants:
        # print([c.P for c in plant.cells])
        view.draw_polygon(plant.polygon, (20, 200, 20))

    # Draw light rays
    for plant in world.plants:
        for cell in plant.cells:
            if cell.light > 0 and cell.prev.light > 0:
                derp = cell.P + Vec2D(math.cos(world.light), math.sin(world.light)) * 1000
                view.draw_line(derp, cell.P, (255, 255, 102, 255))


    # Draw Plant Cells
    for plant in world.plants:
        for cell in plant.cells:
            water = (cell.water + cell.prev.water) / 2
            light = (cell.light + cell.prev.light) / 2
            # else:
            # color = hsv_to_rgb(.59, 1, water)
            # width = 1
            # rgb = tuple(int(x*255) for x in color)

            view.draw_line(cell.P, cell.prev.P, (0,0,0), width=1)


    if draw_segmentgrid:
        for (i,j), v in np.ndenumerate(world.sh.data):
            if len(v):
                view.draw_rect((i*sh.d, j*sh.d, sh.d, sh.d), (0,200,0,200), width=1)
            # else:
            #     view.draw_rect((i*sh.d, j*sh.d, sh.d, sh.d), (0,0,0,0), width=1)

    # for plant in world.plants:
    #     for cell in plant.cells:
    #         # if cell.water:
    #         #     view.draw_circle(cell.P, 3, (0, 0, 200), width=0)
    #         # else:
    #         #     view.draw_circle(cell.P, 3, (0, 0, 0), width=0)
    #         rgb = hsv_to_rgb(1, 1-cell.curvature/(2*math.pi), 1)
    #         rgb = tuple(int(x*255) for x in rgb)
    #         # if cell.curvature > math.pi:
    #         #     d = int(((cell.curvature-math.pi)/math.pi) * 255)
    #         #     hsv_to_rgb
    #         #     view.draw_circle(cell.P, 3, (d, 0, 0), width=0)
    #         # else:
    #         #     d = int((cell.curvature/math.pi) * 255)
    #         #     view.draw_circle(cell.P, 3, (0, 0, d), width=0)
    #         view.draw_circle(cell.P, 3, rgb, width=0)

    # for (i,j), v in np.ndenumerate(pixl_arr):
    #     if v:
    #         view.draw_pixel((j,i), (255, 0, 0, 100))


    for i, plant in enumerate(world.plants):
        x = (i * 400) + 25
        view.draw_text((x, height), "Plant id: "+str(i), font=16)
        view.draw_text((x, height-20), "Light: "+str(plant.light), font=16)
        view.draw_text((x, height-40), "Water: "+str(plant.water), font=16)
        view.draw_text((x, height-60), "Volume: "+str(plant.volume), font=16)
        view.draw_text((x, height-80), "Energy: "+str(plant.energy), font=16)
        view.draw_text((x, height-100), "consumption: "+str(plant.consumption), font=16)
        view.draw_text((x, height-120), "Num cells: "+str(len(plant.cells)), font=16)
    # view.draw_circle(world.light, 10, (255, 255, 0), width=0)
    view.end_draw()
