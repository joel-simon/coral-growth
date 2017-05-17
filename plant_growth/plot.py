import math
from colorsys import hsv_to_rgb
import numpy as np
import pygame

from plant_growth.vec2D import Vec2D

def plot_image_grid(view, world):
    pixl_arr = np.array(world.pg.img)
    pixl_arr = np.swapaxes(np.array(world.plants[0].grid), 0, 1)
    pixl_arr = np.fliplr(pixl_arr)
    new_surf = pygame.pixelcopy.make_surface(pixl_arr)
    view.surface.blit(new_surf, (0, 0))

def plot(view, world, title=None):
    sh = world.sh

    width, height = sh.width, sh.height

    view.start_draw()
    view.draw_rect((0, 0, width, height), (0, 102, 200), width=0)
    view.draw_rect((0, 0, width, world.soil_height), (153, 102, 51, 200), width=0)

    for plant in world.plants:
        view.draw_polygon(plant.polygon, (20, 200, 20))
        view.draw_lines(plant.polygon, (20, 20, 20), width=1)
        # m = plant.mesh

        if plant.mesh:
            for face in plant.mesh.elements:
                poly = [plant.mesh.points[f] for f in face]
                view.draw_lines(poly+[poly[0]], (50, 150, 50))

        for cell in plant.cells:
            if cell.flower:
                view.draw_circle(cell.vector, 3, (200, 0, 200), width=0)

    view.draw_rect((0, 0, width, world.soil_height), (153, 102, 51, 150), width=0)

    # for plant in world.plants:
    #     m = plant.mesh
    #     for face in m.faces:
    #         poly = [(v.x, v.y) for v in face.verts()]
    #         view.draw_polygon(poly, (20, 200, 20))

    #     for edge in m.edges:
    #         v1, v2 = edge.verts()
    #         # print('hi', edge, v1, v2)
    #         view.draw_line((v1.x, v1.y), (v2.x, v2.y), (0,0,0), width=1)

    #     for v in m.verts:
    #         view.draw_circle((v.x, v.y), 3, (0, 0, 0), width=0)
    #         # view.draw_text((v.x, v.y), str(v.id), font=12, center=False)



    # for plant in world.plants:
    #     for tri in plant.tris:
    #         print(tri.c1.P, tri.c2.P, tri.c3.P)
    #         view.draw_polygon([tri.c1.P, tri.c2.P, tri.c3.P], (20, 200, 20))

    #     for edge in plant.edges:
    #         view.draw_line(edge.c1.P, edge.c2.P, (0,0,0), width=1)

    #     for c in plant.cells:
    #         view.draw_circle(c.P, 3, (0, 0, 0), width=0)



    # # Draw light rays
    # for plant in world.plants:
    #     for cell in plant.out_verts:
    #         if cell.light > 0 and cell.prev.light > 0:
    #             derp = cell.P + Vec2D(math.cos(world.light), math.sin(world.light)) * 1000
    #             view.draw_line(derp, cell.P, (255, 255, 102, 255))


    # # Draw Plant Cells
    # for plant in world.plants:
    #     for cell in plant.out_verts:
    #         water = (cell.water + cell.prev.water) / 2
    #         light = (cell.light + cell.prev.light) / 2
    #         # else:
    #         # color = hsv_to_rgb(.59, 1, water)
    #         # width = 1
    #         # rgb = tuple(int(x*255) for x in color)

    #         view.draw_line(cell.P, cell.prev.P, (0,0,0), width=1)


    # if draw_segmentgrid:
    #     for (i,j), v in np.ndenumerate(world.sh.data):
    #         if len(v):
    #             view.draw_rect((i*sh.d, j*sh.d, sh.d, sh.d), (0,200,0,200), width=1)
    #         # else:
    #         #     view.draw_rect((i*sh.d, j*sh.d, sh.d, sh.d), (0,0,0,0), width=1)

    # for plant in world.plants:
    #     for cell in plant.out_verts:
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
        view.draw_text((x, height-120-y), "flowers: %i"%plant.num_flowers, font=16)
        # view.draw_text((x, height-120), "Num out_verts: "+str(len(plant.out_verts)), font=16)
    # view.draw_circle(world.light, 10, (255, 255, 0), width=0)
    view.end_draw()
