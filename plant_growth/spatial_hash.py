from math import floor
from collections import defaultdict

class SpatialHash(object):
    def __init__(self, cell_size=10.0):
        assert(cell_size > 0)
        self.cell_size = float(cell_size)
        self.d = defaultdict(set)

    def _cells_for_rect(self, x1, y1, x2, y2):
        """Return a set of the cells into which r extends."""
        # cells = set()

        if x1 > x2:
            x1, x2 = x2, x1

        if y1 > y2:
            y1, y2 = y2, y1

        cy = floor(y1 / self.cell_size)

        while (cy * self.cell_size) <= y2:
            cx = floor(x1 / self.cell_size)
            while (cx * self.cell_size) <= x2:
                yield (int(cx), int(cy))
                cx += 1.0
            cy += 1.0
        # return cells

    def add_object(self, key, x1, y1, x2, y2):
        """Add an object obj with bounding box"""
        # cells =
        for c in self._cells_for_rect(x1, y1, x2, y2):
            self.d[c].add(key)

    def remove_object(self, key, x1, y1, x2, y2):
        """Remove an object obj with bounding box"""
        # cells =
        for c in self._cells_for_rect(x1, y1, x2, y2):
            self.d[c].remove(key)

    def move_object(self, key, x1, y1, x2, y2, x3, y3, x4, y4):
        # Move from (p1, p2) to (p3, p4)
        all_same = floor(x1 / self.cell_size) == floor(x3 / self.cell_size) and \
                    floor(y1 / self.cell_size) == floor(y3 / self.cell_size) and \
                    floor(x2 / self.cell_size) == floor(x4 / self.cell_size) and \
                    floor(y2 / self.cell_size) == floor(y4 / self.cell_size)
        if all_same:
            return
        else:
            self.remove_object(key, x1, y1, x2, y2)
            self.add_object(key, x3, y3, x4, y4)

    def potential_collisions(self, key, x1, y1, x2, y2):
        """Get a set of all objects that potentially intersect obj."""
        cells = self._cells_for_rect(x1, y1, x2, y2)
        potentials = set()
        for c in cells:
            potentials.update(self.d.get(c, set()))
        potentials.discard(key) # obj cannot intersect itself
        return potentials

