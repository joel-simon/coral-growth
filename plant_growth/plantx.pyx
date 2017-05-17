        # self.__cid = 0 # next cell id
        # self.__eid = 0 # next edge id
        # self.__tid = 0 # next tri id

    # def __cinit__(self, *args, **kwargs):
    #     cdef int nmax = constants.MAX_CELLS
    #     self.cells = <Cell *>malloc(nmax*sizeof(Cell))
    #     self.edges = <Edge *>malloc(nmax*sizeof(Edge))
    #     self.tris = <Tri *>malloc(nmax*sizeof(Tri))

    # def __dealloc__(self):
    #     free(self.cells)
    #     free(self.edges)
    #     free(self.tris)

    # cdef __new_cell(self, x, y):
    #     cdef i = self.__cid

    #     self.cells[i].P = Vec2D(x, y)
    #     # self.cells[i].P = Vec2D(x, y)

    #     self.cells[i].flower = False
    #     # self.verts[i].y = y
    #     self.__cid += 1

    #     return self.cell[i]
    # def __new_cell(self, v):
    #     cell = Cell(None, v)
    #     self.cells.append(cell)
    #     return cell

    # cdef Edge __new_e(self, Cell *c1, Cell *c2, Tri *t1, t2):
    #     cdef i = self.__eid
    #     self.__eid += 1
    #     self.edges[i].c1 = c1
    #     self.edges[i].c2 = c2
    #     self.edges[i].t1 = t1
    #     self.edges[i].t2 = t2
    #     return self.edges[i]
    # def __new_edge(self, c1, c2, t1, t2):
    #     edge = Edge(c1, c2, t1, t2)
    #     self.edges.append(edge)
    #     return edge

    # cdef __new_t(self, Cell *c1, Cell *c2, Cell *c3):
    #     cdef i = self.__tid
    #     self.tris[i].c1 = c1
    #     self.tris[i].c2 = c2
    #     self.tris[i].c3 = c3
    #     self.__tid += 1
    #     return self.tris[i]
    # def __new_tri(self, c1, c2, c3):
    #     tri = Tri(c1, c2, c3)
    #     self.tris.append(tri)
    #     return tri
