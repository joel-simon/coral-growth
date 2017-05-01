from __future__ import division
import numpy as np
from PIL import Image, ImageDraw

class PolygonGrid(object):
    """docstring for PolygonGrid"""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.img = Image.new('L', (width, height), 0)

    def add_polygon(self, polygon):
        points = [(p.x, p.y) for p in polygon]
        ImageDraw.Draw(self.img).polygon(points, outline=0, fill=1)

    def in_polygon(self, point):
        return self.img.getpixel((point.x, point.y))

if __name__ == '__main__':
    grid = PolygonGrid(100, 100)
    grid.add_polygon([(0, 0), (50, 50), (50, 0)])
    print(grid.mask)
