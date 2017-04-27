from __future__ import division
from geometry import intersect
import numpy as np
# import pyclipper
import shapely
from shapely.geometry import box
from shapely.geometry.polygon import Polygon

class PolygonGrid(object):
    """docstring for PolygonGrid"""
    def __init__(self, width, height, box_width):
        self.width = width
        self.height = height
        self.box_width = box_width
        self.polygons = dict()
        self.num_x = int(width/box_width)
        self.num_y = int(height/box_width)
        self.grid = None

    def initialize_polygon(self, polygon_points):
        self.grid = np.zeros((self.num_x, self.num_y), dtype=object)
        polygon = Polygon(polygon_points)

        d = self.box_width
        for x in range(self.num_x):
            for y in range(self.num_y):
                b = box(x*d, y*d, (x+1)*d, (y+1)*d)
                g = polygon.intersection(b)
                if g.is_empty:
                    self.grid[x,y] = -1
                elif g.area == b.area:
                    self.grid[x,y] = 0
                else:
                    self.grid[x,y] = g

    def in_polygon(self, point):
        grid_x = int(point.x / self.box_width)
        grid_y = int(point.y / self.box_width)

        d = self.grid[grid_x, grid_y]

        if d == -1:
            return False
        elif d == 0:
            return True
        else:
            return d.contains(point)

    # def line_intersection(self, point1, point2):
    #     d = point2 - point1
    #     n = 4
    #     for i in range(n):
    #         p = point1 + i/float(n) * d
    #         if self.img.getpixel((p.x, p.y)):
    #             return True

    #     return False


# if __name__ == '__main__':
#     grid = PolygonGrid(100, 100)
#     grid.add_polygon([(0, 0), (50, 50), (50, 0)])
#     print(grid.mask)
