import numpy as np
import math
def plot(view, world, draw_segmentgrid=False):
    sh = world.sh

    width, height = sh.width, sh.height

    view.start_draw()
    view.draw_rect((0, 0, width, height), (0, 102, 255), width=0)
    view.draw_rect((0, 0, width, world.soil_height), (153, 102, 51), width=0)

    if draw_segmentgrid:
        for (i,j), v in np.ndenumerate(world.sh.data):
            if len(v):
                view.draw_rect((i*sh.d, j*sh.d, sh.d, sh.d), (0,200,0, 50), width=0)

    for plant in world.plants:
        view.draw_polygon([c.P for c in plant.cells], (255, 255, 255))

    for plant in world.plants:
        for cell in plant.cells:
            d = int((cell.light+ cell.prev.light)/2 * 255)
            view.draw_line(cell.P, cell.prev.P, (d, d, 0), width=1)

    for plant in world.plants:
        for cell in plant.cells:
            # if cell.water:
            #     view.draw_circle(cell.P, 3, (0, 0, 200), width=0)
            # else:
            #     view.draw_circle(cell.P, 3, (0, 0, 0), width=0)

            if cell.curvature > math.pi:
                d = int(((cell.curvature-math.pi)/math.pi) * 255)
                view.draw_circle(cell.P, 3, (d, 0, 0), width=0)
            else:
                d = int((cell.curvature/math.pi) * 255)
                view.draw_circle(cell.P, 3, (0, 0, d), width=0)

    view.draw_circle(world.light, 10, (255, 255, 0), width=0)
    view.end_draw()
