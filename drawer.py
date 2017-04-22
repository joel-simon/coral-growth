"""
    provide a consistent api around pygame draw functions
    using gfx draw when available
"""
import sys
import math
import pygame
import pygame.gfxdraw
pygame.init()
# pygame.font.init()
pygame.mixer.init()
BLACK = (0,0,0)

class Draw(object):
    """docstring for Draw"""
    def __init__(self, w, h, scale=1, save_path=None):
        self.fonts = dict()
        self.w = w
        self.h = h
        self.scale = scale
        self.surface = pygame.display.set_mode((w, h))
        self.images = dict()

        self.save_path = save_path
        if self.save_path:
            self.frame = 0

    def map_point(self, p):
        x, y = p
        return (int(x*self.scale), int(self.h - y*self.scale))

    def start_draw(self):
        self.surface.fill((255, 255, 255))

    def end_draw(self):
        pygame.display.flip()

    def hold(self):
        while True:
            for event in pygame.event.get():
              if event.type == pygame.QUIT:
                sys.exit()

class PygameDraw(Draw):
    """docstring for PygameDraw"""
    def draw_polygon(self, points, color, t=0):

        points = list(map(self.map_point, points))
        pygame.draw.polygon(self.surface, color, points, t)

    def draw_circle(self, position, radius, color, width=1):
        # pos = (int(position[0]*self.scale), int(position[1]*self.scale))
        position = self.map_point(position)
        r  = int(radius*self.scale)
        width = int(width*self.scale)
        pygame.draw.circle(self.surface, color, position, r, width)

    def draw_line(self, positionA, positionB, color, width=1):
        a = self.map_point(positionA)
        b = self.map_point(positionB)
        width = int(width*self.scale)
        # pygame.draw.line(self.surface, color, a, b, width)
        pygame.gfxdraw.line(self.surface, a[0], a[1], b[0], b[1], color)

    def draw_lines(self, points, color, width=1):
        points = [self.map_point(x,y) for x, y in points]
        pygame.draw.lines(self.surface, color, False, points, width)

    def draw_rect(self, rect, color, width=1):
        x, y = self.map_point((rect[0], rect[1]))
        w, h = int(self.scale*rect[2]), int(self.scale*rect[3])
        rect = (x, y, w, -h)
        pygame.draw.rect(self.surface, color, rect, width)
        # pygame.gfxdraw.rectangle(self.surface, rect, color)

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
