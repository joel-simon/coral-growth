from __future__ import division

import math
import numpy as np
from collections import defaultdict
# from recordclass import recordclass

class Vert:
    __slots__ = ['id', 'x', 'y', 'x0', 'y0', 'he', 'cid', 'boundary']
    def __init__(self, id, x, y, he=None):
        self.id = id
        self.x = x
        self.y = y
        self.x0 = x
        self.y0 = y
        self.he = he
        self.cid = None
        self.boundary = False

    def __str__(self):
        return "Vert(%i, %f, %f, he=%r)" %(self.id, self.x, self.y, bool(self.he))

    def is_boundary(self):
        return self.boundary

class Edge:
    __slots__ = ['id', 'he', 'boundary']
    def __init__(self, id, he=None):
        self.id = id
        self.he = he
        self.boundary = False

    def __str__(self):
        v1, v2 = self.verts()
        return "Edge(%i, %i, length=%f)" % (v1.id, v2.id, self.length())

    def verts(self):
        yield self.he.vert
        yield self.he.next.vert

    def is_boundary(self):
        return self.he.face == None or self.he.twin.face == None

    def length(self):
        p1 = self.he.vert
        p2 = self.he.next.vert
        return math.sqrt(((p1.x-p2.x)**2) + (p1.y-p2.y)**2)

class Face:
    __slots__ = ['id', 'he']
    def __init__(self, id, he=None):
        self.id = id
        self.he = he

    def __str__(self):
        return 'Face(verts=%s)' % str(tuple(v.id for v in self.verts()))

    def verts(self):
        yield self.he.vert
        yield self.he.next.vert
        yield self.he.next.next.vert

    def halfs(self):
        yield self.he
        yield self.he.next
        yield self.he.next.next

    def center(self):
        x = 0.0
        y = 0.0
        for v in self.verts():
            x += v.x
            y += v.y
        return (x/3, y/3)

class HalfEdge(object):
    __slots__ = ['twin', 'next', 'vert', 'edge', 'face']
    def __init__(self, twin=None, next=None, vert=None, edge=None, face=None):
        self.twin = twin
        self.next = next
        self.vert = vert
        self.edge = edge
        self.face = face

    def __str__(self):
        v1, v2 = self.edge.verts()
        if v2 == self.vert:
            v1, v2 = v2, v1
        return "HalfEdge(from=%i, to=%i, twin=%r)" % (v1.id, v2.id, bool(self.twin))

    def prev():
        return self.next.next

class Mesh:
    def __init__(self, raw_verts, raw_polygons):
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
        self.num_edge_polys = defaultdict(int)
        
        pair_to_half = {} # (i,j) tuple -> half edge - (i,j) is twin of (j,i)
        pair_poly_count = {}

        # Create vertex objects.
        for i, p in enumerate(raw_verts):
            v = self.__vert(p[0], p[1])
            index_to_vert[i] = v
            self.vertex_degree[v] = 0

        for poly in raw_polygons:
            for i in poly:
                self.vertex_degree[index_to_vert[i]] += 1

        for poly in raw_polygons:
            degree = len(poly)
            face = self.__face()
            face_half_edges = []

            if degree != 3:
                raise ValueError('Only Triangular Meshes Accepted.')

            for i, a in enumerate(poly):
                b = poly[ (i+1) % degree ]
                pair = (index_to_vert[a], index_to_vert[b])
                
                # if pair in pair_poly_count:
                #     pair_poly_count[pair] += 1
                # elif tuple(reversed(pair)) in pair_poly_count:
                #     pair_poly_count[tuple(reversed(pair))] =+ 1
                # else:
                #     pair_poly_count[pair] = 1

                h_ab = self.__half()
                self.vertices_to_half[pair] = h_ab
                pair_to_half[pair] = h_ab

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

        # Create boundary edges.
        he_boundary = {}
        for (a, b) in pair_to_half:
            if (b, a) not in pair_to_half:
                twin = pair_to_half[(a,b)]
                # assert twin
                # print(a.id, b.id)
                h_ba = self.__half(vert=b, twin=twin, next=None, edge=twin.edge, face=None)
                he_boundary[b] = (h_ba, a)

        for start, (he, end) in he_boundary.items():
            he.next = he_boundary[end][0]

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
        if he:
            he.face = face
        return face

    def __half(self, twin=None, next=None, vert=None, edge=None, face=None):
        he = HalfEdge(twin, next, vert, edge, face)
        self.halfs.append(he)
        if twin:
            twin.twin = he
        if vert:
            vert.he = he
        if edge:
            edge.he = he
        if face:
            face.he = he
        return he

    def __check_valid(self):
        """ For debugging purposes only.
        """
        for v in self.verts:
            try:
                assert v.x != None
                assert v.y != None
                assert isinstance(v.he, HalfEdge)
                assert v.he in self.halfs
            except AssertionError as e:
                print(v)
                raise e

        for he in self.halfs:
            assert isinstance(he.twin, HalfEdge), str(he.twin)
            assert he.twin.twin == he, he
            assert isinstance(he.next, HalfEdge), str(he.next)
            assert isinstance(he.vert, Vert), str(he.vert)
            assert isinstance(he.edge, Edge), str(he.edge)
            assert he.next in self.halfs
            assert he.vert in self.verts
            assert he.edge in self.edges

            if he.face != None:
                assert he.face in self.faces
                assert isinstance(he.face, Face)
            else:
                assert isinstance(he.twin.face, Face) 
            # assert he.face == he.next.face
            # assert he.face == he.next.next.face

        for e in self.edges:
            assert isinstance(e.he, HalfEdge), 'e.he not half edge '+str(e.he)
            v1, v2 = e.verts()
            assert v1 != v2, (v1.id, v2.id)
            if e.he.twin:
                assert e.he.twin.edge == e, (e, e.he.twin.edge)
                assert e.he.face != e.he.twin.face, (str(e.he.face), str(e.he.twin.face))
        
        for f in self.faces:
            self.__valid_face(f)
    
    def __valid_face(self, f):
        assert f
        assert isinstance(f.he, HalfEdge)
        assert len(set(f.verts())) == 3
        assert len(set([f.he, f.he.next, f.he.next.next])) == 3
        assert f.he.next.next.next == f.he # valid circular linked list
        assert f.he.face == f
        assert f.he.next.face == f
        assert f.he.next.next.face == f


    # def __split_half_edge(self, h_ab, vert=None):
    def get_edge(self, vert_a, vert_b):
        for edge in self.edges:
            v1, v2 = edge.verts()
            if (v1, v2) == (vert_a, vert_b) or (v1,v2) == (vert_b, vert_a):
                return edge
        return None

    def neighbors(self, v):
        # print(self)
        h = v.he
        start = h
        # print('start', start)

        h_twin = h.twin
        v = h_twin.vert
        # print(v.id)
        yield v
        h = h_twin.next
        i = 0
        while h != start:
            assert h.twin, h
            h_twin = h.twin
            v = h_twin.vert
            # print(v.id)
            yield v
            h = h_twin.next
            i += 1
            if i >= 50:
                print('errore')
                raise ValueError()

        # print()

    def edge_flip(self, edge):
        # http://mrl.nyu.edu/~dzorin/cg05/lecture11.pdf
        # self.__check_valid()
        if edge.is_boundary():
            return

        # Defining variables
        he1 = edge.he
        he2 = he1.twin
        f1, f2 = he1.face, he2.face

        he11 = he1.next
        he12 = he11.next
        he21 = he2.next
        he22 = he21.next
       
        v1, v2 = he1.vert, he2.vert
        v3, v4 = he12.vert, he22.vert

        # TODO: find out why.
        # assert(v3 != v4)
        if v3 == v4:
            return
       
        # Logic
        he1.next = he22
        he1.vert = v3

        he2.next = he12
        he2.vert = v4

        he11.next = he1

        he12.next = he21
        he12.face = f2

        he21.next = he2

        he22.next = he11
        he22.face = f1

        if f2.he == he22:
            f2.he = he12
        if f1.he == he12:
            f1.he = he22
        if v1.he == he1:
            v1.he = he21
        if v2.he == he2:
            v2.he = he11

        # self.__check_valid()

    def edge_split(self, edge):
        """ Split an external or internal edge and return new vertex.
        """
        # self.__check_valid()
        boundary = edge.is_boundary()

        if edge.he.face is None:
            edge.he = edge.he.twin

        other_face = edge.he.twin.face

        # Three half edges that make up triangle.
        h_ab = edge.he
        h_ba = h_ab.twin
        h_bc = edge.he.next
        h_ca = edge.he.next.next

        # Three vertices of triangle.
        v_a = h_ab.vert
        v_b = h_bc.vert
        v_c = h_ca.vert

        # New vertex.
        x = (v_a.x + v_b.x) / 2.0
        y = (v_a.y + v_b.y) / 2.0
        v_n = self.__vert(x, y, None)

        # Create new face.
        f_nbc = self.__face()
        f_anc =  h_ab.face
        # Create two new edges.
        e_an = edge
        e_nb = self.__edge()
        e_cn = self.__edge() # The interior edge that splits triangle.

        # Create twin half edges on both sides of new interior edge.
        h_cn = self.__half(twin=None, next=None, vert=v_c, edge=e_cn, face=f_nbc)
        h_nc = self.__half(twin=h_cn, next=h_ca, vert=v_n, edge=e_cn, face=f_anc)

        # Half edges that border new split edges.
        h_an = h_ab
        h_an.face = f_anc
        h_bn = h_ba
        h_bn.edge = e_nb
        h_nb = self.__half(twin=h_bn, next=h_bc, vert=v_n, edge=e_nb, face=f_nbc)
        h_na = self.__half(twin=h_an, next=h_ba.next, vert=v_n, edge=e_an, face=None)

        # Update old half pointers
        h_bc.face = f_nbc
        
        h_bc.next = h_cn
        h_ca.next = h_an
        h_an.next = h_nc
        h_cn.next = h_nb
        h_bn.next = h_na
        h_bn.twin = h_nb

        if not boundary:
            h_ad = h_na.next
            h_db = h_ad.next
            v_d = h_db.vert

            # Create new faces
            f_dna = other_face
            f_dbn = self.__face()

            # Create new edge
            e_nd = self.__edge()

            # Create twin half edges on both sides of new interior edge.
            h_dn = self.__half(twin=None, next=h_na, vert=v_d, edge=e_nd, face=f_dna)
            h_nd = self.__half(twin=h_dn, next=h_db, vert=v_n, edge=e_nd, face=f_dbn)

            h_bn.next = h_nd
            h_bn.face = f_dbn

            h_na.face = f_dna
            h_dn.next = h_na

            # Update old half pointers.
            h_db.face = f_dbn
            h_db.next = h_bn
            h_ad.face = f_dna
            h_ad.next = h_dn
            
            v_b.he = h_bn

        return v_n

    def flip_if_better(self, edge):
        if edge.is_boundary():
            return

        p1 = edge.he.next.next.vert
        p2 = edge.he.twin.next.next.vert
        d = math.sqrt((p1.x-p2.x)**2 + (p1.y-p2.y)**2)
        if edge.length() - d > .01:
            self.edge_flip(edge)

if __name__ == '__main__':
    verts = [(0.5, 0), (1, .5), (.5, 1), (0, .5)]
    polys = [(0, 1, 2), (2, 3, 0)]
    mesh = Mesh(verts, polys)
    edge = mesh.get_edge(mesh.verts[0], mesh.verts[2])
    mesh.edge_split(edge)
    print(mesh)
