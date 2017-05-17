from __future__ import division

import math
import numpy as np
# from recordclass import recordclass

class Vert:
    __slots__ = ['id', 'x', 'y', 'he']
    def __init__(self, id, x, y, he=None):
        self.id = id
        self.x = x
        self.y = y
        self.he = he

    def __str__(self):
        return "Vert(%f, %f, %s)" %(self.x, self.y, str(bool(self.he)))

class Edge:
    __slots__ = ['id', 'he']
    def __init__(self, id, he=None):
        self.id = id
        self.he = he

    def verts(self):
        yield self.he.vert
        yield self.he.next.vert

    def is_boundry(self):
        return self.he.twin == None

class Face:
    __slots__ = ['id', 'he']
    def __init__(self, id, he=None):
        self.id = id
        self.he = he

    def verts(self):
        yield self.he.vert
        yield self.he.next.vert
        yield self.he.next.next.vert

    def halfs(self):
        yield self.he
        yield self.he.next
        yield self.he.next.next

class HalfEdge(object):
    __slots__ = ['twin', 'next', 'vert', 'edge', 'face']
    def __init__(self, twin=None, next=None, vert=None, edge=None, face=None):
        self.twin = twin
        self.next = next
        self.vert = vert
        self.edge = edge
        self.face = face

class Mesh:
    def __init__(self, raw_verts, raw_polygon):
        self.foo = 0
        self.verts = []
        self.edges = []
        self.faces = []
        self.halfs = []
        self.vertex_degree = {}

        self.__v_id = 0
        self.__e_id = 0
        self.__f_id = 0

        """ Build half-edge data structure.
        """
        index_to_vert = {}
        self.vertices_to_half = {}
        # index_pair_to_half = {} # (i,j) tuple -> half edge - (i,j) is twin of (j,i)

        for i, (x, y) in enumerate(raw_verts):
            v = self.__vert(x, y)
            index_to_vert[i] = v
            self.vertex_degree[v] = 0

        for poly in raw_polygon:
            for i in poly:
                self.vertex_degree[index_to_vert[i]] += 1

        for poly in raw_polygon:
            degree = len(poly)
            face = self.__face()
            face_half_edges = []

            for i, a in enumerate(poly):
                b = poly[(i+1)%degree]
                pair = (index_to_vert[a], index_to_vert[b])

                h_ab = self.__half()
                self.vertices_to_half[pair] = h_ab

                h_ab.vert = index_to_vert[a]
                index_to_vert[a].he = h_ab

                h_ab.face = face
                face.he = h_ab

                face_half_edges.append(h_ab)

                pair_ba = (index_to_vert[b], index_to_vert[a])
                if pair_ba in self.vertices_to_half:
                    h_ba = self.vertices_to_half[pair_ba]
                    h_ba.twin = h_ab
                    h_ab.twin = h_ba
                    h_ab.edge = h_ba.edge
                else:
                    edge = self.__edge(h_ab)
                    h_ab.edge = edge

            # Link them together via their "next" pointers.
            for i, he in enumerate(face_half_edges):
                he.next = face_half_edges[(i+1) % degree]

        self.__check_valid()

    def __str__(self):
        s = "Mesh"
        for v in self.verts:
            s += "\n\tv_%i: %i, %i" % (v.id, int(v.x), int(v.y))

        for f in self.faces:
            s += "\n\tf_%i: %s" % (f.id, str([v.id for v in f.verts()]))
        return s

    def __vert(self, x, y, he=None):
        vert = Vert(self.__v_id, x, y, he)
        self.__v_id += 1
        self.verts.append(vert)
        return vert

    def __edge(self, he=None):
        edge = Edge(self.__e_id, he)
        self.__e_id += 1
        self.edges.append(edge)
        return edge

    # def __add_face(vertices):
    #     n = len(vertices)
    #     for i, v in enumerate(vertices):
    #         v2 = vertices[(i+1) % ]
    #             pair_ba = (index_to_vert[b], index_to_vert[a])
    #             if pair_ba in self.vertices_to_half:
    #                 h_ba = self.vertices_to_half[pair_ba]
    #                 h_ba.twin = h_ab
    #                 h_ab.twin = h_ba
    #                 h_ab.edge = h_ba.edge
    #             else:
    #                 edge = self.__edge(h_ab)
    #                 h_ab.edge = edge

    def __face(self, he=None):
        face = Face(self.__f_id, he)
        self.__f_id += 1
        self.faces.append(face)
        return face

    def __half(self, twin=None, next=None, vert=None, edge=None, face=None):
        half = HalfEdge(twin, next, vert, edge, face)
        self.halfs.append(half)
        return half

    def __check_valid(self):
        for v in self.verts:
            try:
                assert(v.x != None)
                assert(v.y != None)
                assert(isinstance(v.he, HalfEdge))
                assert(v == v.he.vert)

            except AssertionError as e:
                print()
                print(v, v.he.vert, self.verts.index(v))
                print()
                raise e

        for he in self.halfs:
            # assert(isinstance(he.twin, HalfEdge))
            assert isinstance(he.next, HalfEdge), str(he.next)
            assert isinstance(he.vert, Vert), str(he.vert)
            assert isinstance(he.edge, Edge), str(he.edge)
            assert isinstance(he.face, Face), str(he.face)
            if he.twin != None:
                assert(he.twin.twin == he)

            assert(he.face in self.faces)
            assert(he.vert in self.verts)

        # print(self.edges)l
        for e in self.edges:
            assert isinstance(e.he, HalfEdge), 'e.he not half edge '+str(e.he)
            # v1 , v2 = e.verts()
            # print(v1, v2)

        for f in self.faces:
            assert(isinstance(f.he, HalfEdge))
            assert(f.he.face == f)
            # assert(f.he.next.next.next == f.he)
            assert(f.he.next.next.next == f.he) # valid circular linked list
            v = f.he.vert
            assert(f.he.vert == f.he.next.next.next.vert)

    # def __split_half_edge(self, h_ab, vert=None):
    def get_edge(self, vert_a, vert_b):
        for edge in self.edges:
            v1, v2 = edge.verts()
            if (v1, v2) == (vert_a, vert_b) or (v1,v2) == (vert_b, vert_a):
                return edge
        return None

    def edge_flip(self, edge):
        assert not edge.is_boundry()
        he1 = edge.he
        he2 = he1.twin

        f1, f2 = he1.face, he2.face

        he11 = he1.next
        he12 = he11.next

        he21 = he2.next
        he22 = he21.next

        v1, v2 = he1.vert, he2.vert
        v3, v4 = he12.vert, he22.vert

        he1.next = he22
        he1.vert = v4

        he2.next = he12
        he2.vert = v3

        he11.next = he1

        h12.next, h12.face = he21, f1
        he21.next = he2
        he22.next, he22.face = he11, f1

        if f2.he == he22:
            f2.he = he12
        if f1.he == he12:
            f1.he = he22
        if v1.he == he1:
            v1.he = he21
        if v2.he == he2:
            v2.he = he11


    def edge_split(self, edge_ab):
        # return
        # print('Splitting edge', edge_ab)
        # if self.foo > 0:
        #     return
        # self.foo += 1
        """ Split an external or internal edge and return new vertex.
        """
        # half = edge.he
        # vert = self.__split_half_edge(half)

        # if not edge_ab.is_boundry():
        #     self.__split_half_edge(half.twin, vert=vert)

        # return vert
        # if not edge_ab.is_boundry():
        #     return

        # Three half edges that make up triangle.
        h_ab = edge_ab.he
        h_bc = edge_ab.he.next
        h_ca = edge_ab.he.next.next

        # Three vertices of triangle.
        v_a, v_b = edge_ab.verts()
        v_c = h_ca.vert

        # Face of triangle.
        face_a = h_ab.face

        # Create new vertex in middle of edge
        x = (v_a.x + v_b.x) / 2.
        y = (v_a.y + v_b.y) / 2.
        v_n = self.__vert(x, y, None)

        # Create two new faces.
        f_nbc = self.__face()
        f_anc = self.__face()

        # Create three new edges.
        e_an = self.__edge()
        e_nb = self.__edge()
        e_cn = self.__edge() # The interior edge that splits triangle.

        # Create twin half edges on both sides of new interior edge.
        h_cn = self.__half(None, None, v_c, e_nb, f_nbc)
        h_nc = self.__half(h_cn, h_ab.next.next, v_n, e_nb, f_anc)
        h_cn.twin = h_nc

        # Half edges that border new split edges.
        h_an = self.__half(None, h_nc, v_a, e_an, f_anc)
        h_nb = self.__half(None, h_ab.next, v_n, e_an, f_nbc)
        h_cn.next = h_nb

        # Set edge pointers to half_edges
        e_an.he = h_an
        e_nb.he = h_nb
        e_cn.he = h_cn

        # Set face to half edge pointers .
        f_nbc.he = h_nb
        f_anc.he = h_nc

        # Set vertex to half edge pointer
        v_n.he = h_nb

        # Update old half pointers
        h_bc.face = f_nbc
        h_bc.next = h_cn
        h_ca.face = f_anc
        h_ca.next = h_an

        # Remove old
        self.halfs.remove(h_ab)
        self.faces.remove(face_a)
        self.edges.remove(edge_ab)

        assert f_anc.he.face == f_anc
        assert f_nbc.he.face == f_nbc

        assert(f_nbc.he.next.next.next == f_nbc.he)
        assert(f_anc.he.next.next.next == f_anc.he)

        # if False:
        if not edge_ab.is_boundry():
            # pass
            h_ba = h_ab.twin
            h_ad = h_ba.next
            h_db = h_ad.next

            face_b = h_ba.face

            v_d = h_db.vert

            v_n.x *= 2
            v_n.y *= 2
            v_n.x += (v_c.x + v_d.x)
            v_n.y += (v_c.y + v_d.y)
            v_n.x /= 4
            v_n.y /= 4

            # Create new faces
            f_dna = self.__face()
            f_dbn = self.__face()

            # Create new edge
            e_nd = self.__edge()

            # Create twin half edges on both sides of new interior edge.
            h_dn = self.__half(None, None, v_d, e_nd, f_dna)
            h_nd = self.__half(h_dn, h_db, v_n, e_nd, f_dbn)
            h_dn.twin = h_nd

            h_bn = self.__half(h_nb, h_nd, v_b, e_nb, f_dbn)
            h_nb.twin = h_bn

            h_na = self.__half(h_an, h_ba.next, v_n, e_an, f_dna)
            h_an.twin = h_na
            h_dn.next = h_na

            f_dna.he = h_dn
            f_dbn.he = h_bn

            # Update old half pointers

            h_db.face = f_dbn
            h_db.next = h_bn
            h_ad.face = f_dna
            h_ad.next = h_dn

            assert(f_dna.he.next.next.next == f_dna.he)
            assert(f_dbn.he.next.next.next == f_dbn.he)

            e_nd.he = h_nd

            self.halfs.remove(h_ba)
            self.faces.remove(h_ba.face)

        self.__check_valid()
        return v_n



if __name__ == '__main__':
    verts = [(0.5,0), (1, .5), (.5, 1), (0, .5)]
    polys = [(0, 1, 2), (2, 3, 0)]
    mesh = Mesh(verts, polys)
    edge = mesh.get_edge(mesh.verts[0], mesh.verts[2])
    mesh.edge_split(edge)
    print(mesh)
