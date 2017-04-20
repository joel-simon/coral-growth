from vector import Vector

class Node(object):
    def __init__(self):
        self.prev = None
        self.next = None

class Cell(Node):
    def __init__(self, id, P):
        self.id = id
        self.P = P
        self.next_P = P.copy()
        self.frozen = False
        self.light = 0
        super(Cell, self).__init__()

    def calculate_normal(self):
        Sa = self.prev.P - self.P
        Sb = self.next.P - self.P
        # self.N = Sa.cross(Sb).normed()
        return Sa.cross(Sb).normed()

    def __str__(self):
        return "Cell:"+str(self.P)
