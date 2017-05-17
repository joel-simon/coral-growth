from plant_growth import linkedlist, constants, vec2D

class Cell(linkedlist.Node):
    __slots__ = ['id', 'flower', 'inputs', 'vector']
    def __init__(self, id, x, y):
        self.id = id

        self.light = 0
        self.water = 0
        self.curvature = 0

        self.flower = 0
        self.vector = vec2D.Vec2D(x, y)

        super(Cell, self).__init__()

    def __str__(self):
        return "Cell:"+str(self.v)
