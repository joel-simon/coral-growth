import numpy as np
cimport numpy as np
from cymesh.structures cimport Vert

cdef class Cell:
    def __init__(self, id, vert, n_morphogens=1):
        self.id = id
        self.vert = vert
        # self.rotated = np.array(3)
        self.last_p = np.zeros(3)
        self.morphogens = np.zeros(n_morphogens)

        self.energy = 0
        self.light = 0
        self.flow = 0
        self.ctype = 0
        # self.inputs = np.zeros()
