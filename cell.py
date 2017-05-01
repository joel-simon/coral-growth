from vec2D import Vec2D
from modules.linkedlist import Node


class Cell(Node):
    def __init__(self, id, P):
        self.id = id
        self.P = P
        self.new_p = P.copy()
        self.frozen = False
        self.alive = True
        # self.N = None
        # self.grow_d = 0w

        self.light = 0
        self.water = 0
        self.curvature = 0

        super(Cell, self).__init__()

    def calculate_normal(self):
        Sa = self.prev.P - self.P
        Sb = self.next.P - self.P
        # self.N = Sa.cross(Sb).normed()
        return Sa.cross(Sb).normed()

    def __str__(self):
        return "Cell:"+str(self.P)
