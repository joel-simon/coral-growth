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

    # view.draw_rect((0, 0, width, height), (0, 102, 200), width=0)
    # view.draw_rect((0, 0, width, world.soil_height), (153, 102, 51, 150), width=0)

    # background_color = (210,210,210)
    # background_color = (199, 206, 199)
    background_color = (69, 84, 156)
    
    # plant_color = (20, 200, 20)
    # plant_color = (146, 215, 101)
    plant_color = (111, 181, 109)
    
    plant_thickness = 1
    flower_color = (200, 10, 200)
    dirt_color = (156, 109, 69)
    # dirt_color = (211, 137, 71)

    view.draw_rect((0, 0, width, height), background_color, width=0)
    # view.draw_rect((0, 0, width, world.soil_height), (0,0,0, 150), width=0)

    view.draw_rect((0, 0, width, world.soil_height), dirt_color, width=0)

    for plant in world.plants:
        view.draw_polygon(plant.polygon, plant_color)

        for i in range(plant.n_cells):
            cid = plant.cell_order[i]
            assert(plant.cell_alive[cid])

            prev_id = plant.cell_prev[cid]

            p1 = (plant.cell_x[cid], plant.cell_y[cid])
            p2 = (plant.cell_x[prev_id], plant.cell_y[prev_id])

            light = (plant.cell_light[cid] + plant.cell_light[prev_id])/2

            color = (int(255*light), int(248*light), 0, 255)
            # color = (0,0,0)
            view.draw_line(p1, p2, color, width=plant_thickness)

        if plant.mesh:
            for face in plant.mesh.elements:
                poly = [plant.mesh.points[f] for f in face]
                view.draw_lines(poly+[poly[0]], (50, 150, 50))

        for i in range(plant.n_cells):
            cid = plant.cell_order[i]
            if plant.cell_alive[cid]:
                c_x = plant.cell_x[cid]
                c_y = plant.cell_y[cid]
                light = plant.cell_light[cid]

                if plant.cell_flower[cid]:
                    view.draw_circle((c_x, c_y), 1, flower_color, width=0)

                # elif plant.cell_water[cid]:
                #     view.draw_circle((c_x, c_y), 1, (0, 0, 200), width=0)

                # elif light != 0:
                #     assert light <= 1.0
                #     # light  = 1.0
                #     # assert light >= 0, light
                #     if light < 0:
                #         color = (200, 0, 0)
                #     else:
                #         color = (int(255*light), int(248*light), 0, 255)
                #     view.draw_circle((c_x, c_y), 1, color, width=0)

        # view.draw_line((0, world.soil_height), (world.width, world.soil_height), dirt_color, width=plant_thickness)

    view.draw_alpha_rect((0, 0, width, world.soil_height), dirt_color, 100)

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
        view.draw_text((x, height-100-y), "energy_usage: %.4f"%plant.energy_usage, font=16)
        view.draw_text((x, height-120-y), "Num cells: %i"%plant.n_cells, font=16)
        view.draw_text((x, height-140-y), "Num flowers: %i"%plant.num_flowers, font=16)

    view.end_draw()
