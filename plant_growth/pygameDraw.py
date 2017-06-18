""" provide a consistent api around pygame draw functions
    using gfx draw if available.
"""
import sys
import math
import pygame
import pygame.gfxdraw

pygame.init()
pygame.mixer.init()

BLACK = (0,0,0)

class PygameDraw(object):
    """docstring for Draw"""
    def __init__(self, w, h, scale=1, flip_y=True):
        self.fonts = dict()
        self.w = w
        self.h = h
        self.scale = scale
        self.flip_y = flip_y

        self.surface = pygame.display.set_mode((w, h))
        self.images = dict()

    def map_point(self, p):
        x, y = p
        if self.flip_y:
            return (int(x*self.scale), int(self.h - y*self.scale))
        else:
            return (int(x*self.scale), int(y*self.scale))

    def start_draw(self):
        self.surface.fill((255, 255, 255))

    def end_draw(self):
        pygame.display.flip()

    def save(self, path):
        pygame.image.save(self.surface, path)

    def hold(self):
        while True:
            for event in pygame.event.get():
              if event.type == pygame.QUIT:
                sys.exit()

    def draw_pixel(self, point, color):
        x, y = self.map_point(point)
        pygame.gfxdraw.pixel(self.surface, x, y, color)

    def draw_polygon(self, points, color, t=0):
        points = [self.map_point(p) for p in points]
        if t == 0:
            pygame.gfxdraw.filled_polygon(self.surface, points, color)
        elif t == 1:
            pygame.gfxdraw.aapolygon(self.surface, points, color)
        else:
            pygame.draw.polygon(self.surface, color, points, t)

    def draw_circle(self, position, radius, color, width=0):
        position = self.map_point(position)
        r  = int(radius*self.scale)
        width = int(width*self.scale)
        if width == 0:
            x, y = position
            pygame.gfxdraw.filled_circle(self.surface, x, y, r, color)
        else:
            pygame.draw.circle(self.surface, color, position, r, width)

    def draw_line(self, positionA, positionB, color, width=1):
        a = self.map_point(positionA)
        b = self.map_point(positionB)
        width = int(width*self.scale)
        center = ((a[0] + b[0])/2, (a[1] + b[1])/2)
        angle = math.atan2(a[1] - b[1], a[0] - b[0])
        length = math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

        if width == 1:
            pygame.draw.line(self.surface, color, a, b, width)
        else:
            UL = (center[0] + (length / 2.) * math.cos(angle) - (width / 2.) * math.sin(angle),
                  center[1] + (width / 2.) * math.cos(angle) + (length / 2.) * math.sin(angle))
            UR = (center[0] - (length / 2.) * math.cos(angle) - (width / 2.) * math.sin(angle),
                  center[1] + (width / 2.) * math.cos(angle) - (length / 2.) * math.sin(angle))
            BL = (center[0] + (length / 2.) * math.cos(angle) + (width / 2.) * math.sin(angle),
                  center[1] - (width / 2.) * math.cos(angle) + (length / 2.) * math.sin(angle))
            BR = (center[0] - (length / 2.) * math.cos(angle) + (width / 2.) * math.sin(angle),
                  center[1] - (width / 2.) * math.cos(angle) - (length / 2.) * math.sin(angle))

            pygame.gfxdraw.aapolygon(self.surface, (UL, UR, BR, BL), color)
            pygame.gfxdraw.filled_polygon(self.surface, (UL, UR, BR, BL), color)

        # if width > 1:
        #     pygame.draw.line(self.surface, color, a, b, width)
        # else:
            # pygame.gfxdraw.line(self.surface, a[0], a[1], b[0], b[1], color)

    def draw_lines(self, points, color, width=1):
        points = [self.map_point(p) for p in points]
        pygame.draw.lines(self.surface, color, False, points, width)

    def draw_rect(self, rect, color, width=1):
        x, y = self.map_point((rect[0], rect[1]))
        w, h = int(self.scale*rect[2]), int(self.scale*rect[3])
        rect = (x, y, w, -h)

        if width == 0:
            points = [(x, y), (x+w, y), (x+w, y-h), (x, y-h)]
            pygame.gfxdraw.filled_polygon(self.surface, points, color)

        elif width == 1:
            pygame.gfxdraw.rectangle(self.surface, rect, color)

        else:
            pygame.draw.rect(self.surface, color, rect, width)

    def draw_alpha_rect(self, rect, color, alpha):
        x, y = self.map_point((rect[0], rect[1]))
        w, h = int(self.scale*rect[2]), int(self.scale*rect[3])
        s = pygame.Surface((w, h), pygame.SRCALPHA)   # per-pixel alpha
        s.fill(color + (alpha,))
        # print(y, self.h)
        self.surface.blit(s, (x, y-h))

    def draw_text(self, position, string, font=8, color=BLACK, center=False):
        font = int(self.scale * font)
        x, y = self.map_point(position)
        if font not in self.fonts:
            self.fonts[font] = pygame.font.SysFont("monospace", font)
        text = self.fonts[font].render(string, 1, color)

        if center:
            w = text.get_rect().width
            h = text.get_rect().height
            self.surface.blit(text, (int(x-w/2.), int(y-h/2.)))
        else:
            self.surface.blit(text, (x, y))
