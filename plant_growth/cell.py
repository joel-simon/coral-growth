from plant_growth import linkedlist

class Cell(linkedlist.Node):
    def __init__(self, id, P):
        self.id = id
        self.P = P
        self.new_p = P.copy()
        self.frozen = False
        self.alive = True

        self.light = 0
        self.water = 0
        self.curvature = 0

        super(Cell, self).__init__()

    def __str__(self):
        return "Cell:"+str(self.P)
