import numpy as np
import math
def plot(view, world, draw_segmentgrid=False):
    sh = world.sh
    height = sh.height
    view.start_draw()

    if draw_segmentgrid:
        for (i,j), v in np.ndenumerate(world.sh.data):
            if len(v):
                view.draw_rect((i*sh.d, height-j*sh.d, sh.d, -sh.d), (0,200,0, 50), width=0)


    for plant in world.plants:
        s = 0
        for C in plant.cells:
            P = C.P
            # if draw
            # if C.frozen:
            #     view.draw_circle(C.P, 4, (100, 100, 200), width=0)
            # else:
            # view.draw_circle(C.P, 4, (0,0,255), width=0)

            if C.light:# and C.prev.light:
                # a1 = math.atan2(world.light.y - C.P.y, world.light.x - C.P.x)
                # a2 = math.atan2(world.light.y - C.prev.P.y, world.light.x - C.prev.P.x)
                # s += abs(math.degrees(a1) - math.degrees(a2))
                foo = int(C.light * 255)
                # print(C.light)
                # view.draw_line(C.P, world.light, (200, 200, 0), width=1)
                view.draw_circle(C.P, 2, (foo, foo, 0), width=0)
            # else:
                # view.draw_circle(C.P, 4, (0,0, 0), width=1)
                # light = a1-a2
                # print(a2 - a1)
                # print(math.degrees(a2 - a1))
            # view.draw_line(C.P, C.next.P, (0,0,0), width=2)

            # if C.light:# and C.next.light:
                # view.draw_line(C.P, C.next.P, (250,250,50), width=3)

                # view.draw_circle(C.P, 4, (200, 200, 0), width=0)
            # else:
            #     view.draw_line(C.P, C.next.P, (200,200,200), width=3)
            view.draw_line(C.P, C.next.P, (0,0,0), width=1)
        # print('a', s)

    # for p0, p1 in world.sh.segments.values():
        # view.draw_line(p0, p1, (0,0,0), width=2)

        # for v in vis:
        #     view.draw_circle((v.x, v.y), 4, (200, 200, 0), width=0)

            # else:
        # exit()

        # if elements != None:
        #     for a, b, c in elements:
        #         # print(a,b,c)
        #         va = points[a]
        #         vb = points[b]
        #         vc = points[c]
        #         view.draw_line(va, vb, (100,100,100))
        #         view.draw_line(va, vc, (100,100,100))
        #         view.draw_line(vb, vc, (100,100,100))

    view.end_draw()
