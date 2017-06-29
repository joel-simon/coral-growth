import math
from colorsys import hsv_to_rgb
import numpy as np
import pygame
from math import pi as M_PI
from plant_growth.mesh import Mesh
# def contiguous_lit_cells(plant):
#     run = []
#     for i in range(plant.n_cells):
#         cid = plant.cell_order[i]

#         if plant.cell_light[cid] > 0:
#             run.append(cid)

#         elif len(run):
#             yield run
#             run = []

# def plot_mesh(view, points, edges):
def draw_mesh(view, mesh):
    # if isinstance(mesh, Mesh):
    # for face in mesh.faces:
    #     poly = [(v.x, v.y) for v in face.verts()]
    #     view.draw_lines(poly+[poly[0]], (100, 100, 100)) # (50, 150, 50)
    for edge in mesh.edges:
        v1, v2 = edge.verts()
        d = edge.strain
        r = min(255, max(0, int(abs(d)*255.0)))
        color = (r, 0, 0)
        if d > .2:
            view.draw_line((v1.x, v1.y), (v2.x, v2.y), color, 1.5)
    # else:
    #     for face in mesh.elements:
    #         poly = [mesh.points[f] for f in face]
    #         view.draw_lines(poly+[poly[0]], (100, 100, 100)) # (50, 150, 50)

def plot(view, world, title=None):
    width, height = world.width, world.height
    view.start_draw()

    # view.draw_rect((0, 0, width, height), (0, 102, 200), width=0)

    # background_color = (210,210,210)
    # background_color = (199, 206, 199)
    background_color = (69, 84, 156)

    # plant_color = (20, 200, 20)
    # plant_color = (146, 215, 101)
    plant_color = (111, 181, 109)

    plant_thickness = 2
    flower_color = (200, 10, 200)
    dirt_color = (156, 109, 69)
    # dirt_color = (211, 137, 71)

    view.draw_rect((0, 0, width, height), background_color, width=0)

    for plant in world.plants:
        # print(list(plant.cell_alive[:plant.n_cells]))
        view.draw_polygon(plant.polygon, plant_color)

        if plant.mesh:
            draw_mesh(view, plant.mesh)

        for i in range(plant.n_cells):
            cid = plant.cell_order[i]
            prev_id = plant.cell_prev[cid]

            p1 = (plant.cell_x[cid], plant.cell_y[cid])
            p2 = (plant.cell_x[prev_id], plant.cell_y[prev_id])

            light = (plant.cell_light[cid] + plant.cell_light[prev_id])/2

            if not plant.cell_alive[cid] and not plant.cell_alive[prev_id]:
                color = (255, 255, 255)
            else:
                color = (int(255*light), int(248*light), 0, 255)

            view.draw_line(p1, p2, color, width=plant_thickness)

            # for point in list(plant.mesh.points)[:plant.n_cells]:
            #     view.draw_circle(point, 2, flower_color)

        for i in range(plant.n_cells):
            cid = plant.cell_order[i]

            c_x = plant.cell_x[cid]
            c_y = plant.cell_y[cid]

            if plant.cell_type[cid] == 1:
                view.draw_circle((c_x, c_y), 1, (200,0,0), width=0)
            elif plant.cell_type[cid] == 2:
                view.draw_circle((c_x, c_y), 1, (0,0,200), width=0)

        #         view.draw_circle((c_x, c_y), 2, (255, 255, 255), width=0)
        # #         c_x = plant.cell_x[cid]
        #         c_y = plant.cell_y[cid]
        #         light = plant.cell_light[cid]

                # if plant.cell_flower[cid]:
                    # view.draw_circle((c_x, c_y), 1, flower_color, width=0)

                # # elif plant.cell_water[cid]:
                # #     view.draw_circle((c_x, c_y), 1, (0, 0, 200), width=0)

                # # elif light != 0:
                # #     assert light <= 1.0
                # #     # light  = 1.0
                # #     # assert light >= 0, light
                # #     if light < 0:
                # #         color = (200, 0, 0)
                # #     else:
                # #         color = (int(255*light), int(248*light), 0, 255)
                # #     view.draw_circle((c_x, c_y), 1, color, width=0)

    for i, plant in enumerate(world.plants):
        x = (i * 400) + 10
        if title:
            view.draw_text((x, height-5), title, font=32)
            y = 40
        else:
            y = 20
        view.draw_text((x, height-y), "Plant id: %i"%i, font=16)
        view.draw_text((x, height-20-y), "Alive: %i"%sum(plant.cell_alive[:plant.n_cells]), font=16)
        # view.draw_text((x, height-60-y), "Volume: %.4f"%plant.volume, font=16)
        # view.draw_text((x, height-100-y), "energy_usage: %.4f"%plant.energy_usage, font=16)
        view.draw_text((x, height-40-y), "Num cells: %i"%plant.n_cells, font=16)
        view.draw_text((x, height-60-y), "Gametes: %i"%plant.gametes, font=16)

    view.end_draw()
