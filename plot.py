import numpy as np

def plot(view, world, draw_polygrid=False, draw_segmentgrid=False):
    sh = world.sh
    height = sh.height
    view.start_draw()

    if draw_polygrid:
        pixl_arr = np.swapaxes(np.array(polygrid.img), 0,1)
        new_surf = pygame.pixelcopy.make_surface(pixl_arr)
        view.surface.blit(new_surf, (0, 0))


    if draw_segmentgrid:
        for (i,j), v in np.ndenumerate(world.sh.data):
            if len(v):
                view.draw_rect((i*sh.d, height-j*sh.d, sh.d, -sh.d), (0,200,0, 50), width=0)


    for plant in world.plants:
        for C in plant.cells:
            P = C.P
            # if draw
            # if C.frozen:
            #     view.draw_circle(C.P, 4, (100, 100, 200), width=0)
            # else:
            view.draw_circle(C.P, 4, (0,0,255), width=0)

            # view.draw_line(C.P, C.next.P, (0,0,0), width=2)

            # if C.light:# and C.next.light:
                # view.draw_line(C.P, C.next.P, (250,250,50), width=3)
                # view.draw_line(C.P, world.light, (200, 200, 0), width=1)
                # view.draw_circle(C.P, 4, (200, 200, 0), width=0)
            # else:
            #     view.draw_line(C.P, C.next.P, (200,200,200), width=3)
            view.draw_line(C.P, C.next.P, (0,0,0), width=3)

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
