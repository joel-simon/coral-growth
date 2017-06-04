import math
from colorsys import hsv_to_rgb
import numpy as np
import pygame
from math import pi as M_PI

def contiguous_lit_cells(plant):
    run = []
    for i in range(plant.n_cells):
        cid = plant.cell_order[i]

        if plant.cell_light[cid] > 0:
            run.append(cid)

        elif len(run):
            yield run
            run = []

def plot(view, world, title=None):
    width, height = world.width, world.height
    view.start_draw()
    view.draw_rect((0, 0, width, height), (0, 102, 200), width=0)
    view.draw_rect((0, 0, width, world.soil_height), (153, 102, 51, 150), width=0)

    for plant in world.plants:
        view.draw_polygon(plant.polygon, (20, 200, 20))
        # print(plant.cell_x[0], plant.cell_next_x[0])

        for i in range(plant.n_cells):
            cid = plant.cell_order[i]
            assert(plant.cell_alive[cid])

            prev_id = plant.cell_prev[cid]
            # cell_light = plant.cell_light[cid]
            # prev_light = plant.cell_light[prev_id]
            c_x = plant.cell_x[cid]
            c_y = plant.cell_y[cid]
            p_x = plant.cell_x[prev_id]
            p_y = plant.cell_y[prev_id]

    #         light = min(1, max(0, plant.cell_light[cid]))
    #         color = (int(255*light), int(248*light), 0, 255)
            color = (0,0,0)
            view.draw_line((c_x, c_y), (p_x, p_y), color, width=1)

        if plant.mesh:
            for face in plant.mesh.elements:
                poly = [plant.mesh.points[f] for f in face]
                view.draw_lines(poly+[poly[0]], (50, 150, 50))


        for cid in range(plant.max_i):
            if plant.cell_alive[cid]:
                c_x = plant.cell_x[cid]
                c_y = plant.cell_y[cid]

                if plant.cell_flower[cid]:
                    view.draw_circle((c_x, c_y), 1, (200, 0, 200, 150), width=0)

                # elif plant.cell_water[cid]:
                #     view.draw_circle((c_x, c_y), 1, (0, 0, 200), width=0)

                elif plant.cell_light[cid]:
                    light = min(1, max(0, plant.cell_light[cid]))
                    color = (int(255*light), int(248*light), 0, 255)
                    view.draw_circle((c_x, c_y), 1, color, width=0)

    view.draw_rect((0, 0, width, world.soil_height), (153, 102, 51, 150), width=0)

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
