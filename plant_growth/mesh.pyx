from __future__ import division
from libcpp.vector cimport vector
from libcpp.map cimport map
from libcpp.pair cimport pair

import numpy as np
cimport numpy as np
from libc.math cimport sqrt

cdef:
    Vert_pntr VNULL = <Vert_pntr> NULL
    Edge* ENULL = <Edge*> NULL
    Face* FNULL = <Face*> NULL
    HalfEdge* HNULL = <HalfEdge*> NULL

cdef class Mesh:
    def __init__(self, raw_points, raw_polygons):
        self.boundary_start = HNULL # Store a reference to a boundary vert for perimeter iteration.

        self.__v_id = 0
        self.__e_id = 0
        self.__f_id = 0

        """ Build half-edge data structure.
        """
        # Need to use a typdef for vert pointer par because of language weakness.
        # https://stackoverflow.com/questions/13248992/cython-stdpair-of-two-pointers-expected-an-identifier-or-literal
        cdef Vert_pntr va, vb
        cdef HalfEdge* he
        cdef map[Vert_pair, HalfEdge*] pair_to_half
        cdef Vert_pair pair_ba, pair_ab
        cdef vector[HalfEdge*] face_half_edges
        cdef Face* face
        cdef pair[Vert_pair, HalfEdge*] pair_he_map
        # vertices_to_half = {}
        # pair_to_half = {} # (i,j) tuple -> half edge

        # Create Vert objects.
        for i, p in enumerate(raw_points):
            self.__vert(p[0], p[1])

        # Create Face objects.
        for poly in raw_polygons:
            if len(poly) != 3:
                raise ValueError('Only Triangular Meshes Accepted.')

            face = self.__face()
            face_half_edges.clear()

            # Create half-edge for each edge.
            for i, a in enumerate(poly):
                b = poly[ (i+1) % len(poly) ]
                va = &self.verts[a]
                vb = &self.verts[b]
                pair_ab = <Vert_pair>(va, vb)

                h_ab = self.__half(face=face, vert=&self.verts[a], twin=HNULL, next=HNULL, edge=ENULL)

                # vertices_to_half[pair_ab] = h_ab
                pair_to_half[pair_ab] = h_ab
                face_half_edges.push_back(h_ab)

                # Link to twin if it exists.
                pair_ba = <Vert_pair>(vb, va)
                if pair_to_half.count(pair_ba):
                    h_ba = pair_to_half[pair_ba]
                    h_ba.twin = h_ab
                    h_ab.twin = h_ba
                    h_ab.edge = h_ba.edge
                else:
                    edge = self.__edge(h_ab)
                    h_ab.edge = edge

            # Link them together via their 'next' pointers.
            i = 0
            for he in face_half_edges:
                he[0].next = face_half_edges[(i+1) % len(poly)]
                i += 1

        # Create boundary edges.
        cdef map[Vert_pntr, pair[HalfEdge_pntr, Vert_pntr]] he_boundary
        cdef pair[Vert_pntr, pair[HalfEdge_pntr, Vert_pntr]] he_boundary_item
        # he_boundary = {}
        for pair_he_map in pair_to_half:
            pair_ab = pair_he_map.first
            va = pair_ab.first
            vb = pair_ab.second
            pair_ba = <Vert_pair>(vb, va)
            if pair_to_half.count(pair_ba) == 0:
                twin = pair_to_half[pair_ab]
                h_ba = self.__half(vert=vb, twin=twin, next=HNULL, edge=ENULL, face=FNULL)
                he_boundary[vb] = <pair[HalfEdge_pntr, Vert_pntr]>(h_ba, va)

        # Link external boundary edges.
        # for start, (he, end) in he_boundary:
        for he_boundary_item in he_boundary:
            start = he_boundary_item.first
            he = he_boundary_item.second.first
            end = he_boundary_item.second.second

            he.next = he_boundary[end].first
            self.boundary_start = he

    # def __str__(self):
    #     s = "Mesh"
    #     for v in self.verts:
    #         s += "\n\tv_%i: %i, %i" % (v.id, int(v.x), int(v.y))

    #     for f in self.faces:
    #         s += "\n\tf_%i: %s" % (f.id, str([v.id for v in self.face_verts(f)]))

    #     return s

    # Constructor functions.
    cdef Vert* __vert(self, double x, double y, HalfEdge* he=HNULL):
        cdef Vert vert
        vert.id = self.__v_id
        vert.x = x
        vert.y = y
        vert.he = he
        self.__v_id += 1
        self.verts.push_back(vert)
        return &vert

    cdef Edge* __edge(self, HalfEdge* he=HNULL):
        cdef Edge edge
        edge.id = self.__e_id
        edge.he = he
        self.__e_id += 1
        self.edges.push_back(edge)
        return &edge

    cdef Face* __face(self, HalfEdge* he=HNULL):
        cdef Face face
        face.id = self.__f_id,
        face.he = he
        self.__f_id += 1
        self.faces.push_back(face)
        if he:
            he.face = &face
        return &face

    cdef HalfEdge* __half(self, HalfEdge* twin=HNULL, HalfEdge* next=HNULL, Vert* vert=VNULL, Edge* edge=ENULL, Face* face=FNULL):
        cdef HalfEdge he
        he.twin = twin
        he.next = next
        he.vert = vert
        he.edge = edge
        he.face = face
        self.halfs.push_back(he)
        if twin:
            twin.twin = &he
        if vert:
            vert.he = &he
        if edge:
            edge.he = &he
        if face:
            face.he = &he
        return &he

    # Meh modifying
    cdef void edge_flip(self, Edge* e):
        cdef (HalfEdge *) he1, he2, he11, he12, he22
        cdef (Vert *) v1, v2, v3, v4
        cdef (Face *) f1, f2

        # http://mrl.nyu.edu/~dzorin/cg05/lecture11.pdf
        if self.is_boundary_edge(e):
            return

        # Defining variables
        he1 = e.he
        he2 = he1.twin
        f1, f2 = he1.face, he2.face
        he11 = he1.next
        he12 = he11.next
        he21 = he2.next
        he22 = he21.next
        v1, v2 = he1.vert, he2.vert
        v3, v4 = he12.vert, he22.vert

        # TODO: find out why this happens.
        if v3 is v4:# assert(v3 != v4)
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

        if f2.he is he22:
            f2.he = he12
        if f1.he is he12:
            f1.he = he22
        if v1.he is he1:
            v1.he = he21
        if v2.he is he2:
            v2.he = he11

    cdef Vert* edge_split(self, Edge* e):
        """ Split an external or internal edge and return new vertex.
        """
        cdef (Face *) other_face, f_nbc, f_anc, f_dna, f_dbn
        cdef (HalfEdge *) h_ab, h_ba, h_bc, h_ca, h_cn, h_nc, h_an, h_na, h_bn
        cdef (HalfEdge *) h_ad, h_db, h_dn, h_nd
        cdef (Edge *) e_an, e_nb, e_cn, e_nd
        cdef (Vert *) v_a, v_b, v_c, v_n
        cdef double x, y

        if e.he.face is FNULL:
            e.he = e.he.twin

        other_face = e.he.twin.face

        # Three half edges that make up triangle.
        h_ab = e.he
        h_ba = h_ab.twin
        h_bc = e.he.next
        h_ca = e.he.next.next

        # Three vertices of triangle.
        v_a = h_ab.vert
        v_b = h_bc.vert
        v_c = h_ca.vert

        # New vertex.
        x = (v_a.x + v_b.x) / 2.0
        y = (v_a.y + v_b.y) / 2.0
        v_n = self.__vert(x, y)

        # Create new face.
        f_nbc = self.__face()
        f_anc =  h_ab.face
        # Create two new edges.
        e_an = e
        e_nb = self.__edge()
        e_cn = self.__edge() # The interior edge that splits triangle.

        # Create twin half edges on both sides of new interior edge.
        h_cn = self.__half(twin=HNULL, next=HNULL, vert=v_c, edge=e_cn, face=f_nbc)
        h_nc = self.__half(twin=h_cn, next=h_ca, vert=v_n, edge=e_cn, face=f_anc)

        # Half edges that border new split edges.
        h_an = h_ab
        h_an.face = f_anc
        h_bn = h_ba
        h_bn.edge = e_nb
        h_nb = self.__half(twin=h_bn, next=h_bc, vert=v_n, edge=e_nb, face=f_nbc)
        h_na = self.__half(twin=h_an, next=h_ba.next, vert=v_n, edge=e_an, face=FNULL)
        h_bc.face = f_nbc
        h_bc.next = h_cn
        h_ca.next = h_an
        h_an.next = h_nc
        h_cn.next = h_nb
        h_bn.next = h_na
        h_bn.twin = h_nb

        if other_face is not FNULL:
            h_ad = h_na.next
            h_db = h_ad.next
            v_d = h_db.vert
            # Create new faces
            f_dna = other_face
            f_dbn = self.__face()
            # Create new edge
            e_nd = self.__edge()
            # Create twin half edges on both sides of new interior edge.
            h_dn = self.__half(twin=HNULL, next=h_na, vert=v_d, edge=e_nd, face=f_dna)
            h_nd = self.__half(twin=h_dn, next=h_db, vert=v_n, edge=e_nd, face=f_dbn)
            h_bn.next = h_nd
            h_bn.face = f_dbn
            h_na.face = f_dna
            h_dn.next = h_na
            h_db.face = f_dbn
            h_db.next = h_bn
            h_ad.face = f_dna
            h_ad.next = h_dn
            v_b.he = h_bn

        return v_n

    cdef void flip_if_better(self, Edge* e):
        cdef double epsilon = .01
        cdef (Vert *) v1, v2
        if self.is_boundary_edge(e):
            return

        v1 = e.he.next.next.vert
        v2 = e.he.twin.next.next.vert
        d = sqrt((v1.x-v2.x)**2 + (v1.y-v2.y)**2)

        if self.edge_length(e) - d > epsilon:
            self.edge_flip(e)

    # def to_arrays(self):
    #     points = np.zeros((len(self.verts), 2))
    #     edges = np.zeros((len(self.edges), 2), dtype='int64')
    #     v_to_i = dict()

    #     for i, vert in enumerate(self.verts):
    #         v_to_i[vert] = i
    #         points[i, 0] = vert.x
    #         points[i, 1] = vert.y

    #     for j, edge in enumerate(self.edges):
    #         v1, v2 = self.edge_verts(edge)
    #         edges[j, 0] = v_to_i[v1]
    #         edges[j, 1] = v_to_i[v2]

    #     return {'points': points, 'edges': edges }

    cdef void smooth(self):
        """ Smooth each interior vertex by moving towared average of neighbors.
        """
        cdef:
            Vert v
            int i
            double n

        for v in self.verts:
            if v.cid == None:
                v.x0 = 0
                v.y0 = 0
                n = 0

                neighbors = self.vert_neighbors(&v)

                for nv in neighbors:
                    v.x0 += nv.x
                    v.y0 += nv.y
                    n += 1

                v.y0 /= n
                v.x0 /= n

        for v in self.verts:
            if v.cid == None:
                v.x = v.x0
                v.y = v.y0

    # cdef list adapt(self, double max_edge_length):
    #     cdef:
    #         list new_verts = []
    #         Edge edge
    #         (Vert *) vert, v1, v2

    #     for edge in self.edges:
    #         if self.edge_length(&edge) > max_edge_length:
    #             v1, v2 = self.edge_verts(&edge)
    #             vert = self.edge_split(&edge)
    #             new_verts.append((vert, v1, v2))

    #     for edge in self.edges:
    #         self.flip_if_better(&edge)

    #     self.smooth()

    #     return new_verts

    # Query
    cdef vert_three_tuple face_verts(self, Face* face):
        cdef HalfEdge *he = face.he
        cdef vert_three_tuple result = (he.vert, he.next.vert, he.next.next.vert)
        # result.push_back(he.vert)
        # result.push_back(he.next.vert)
        # result.push_back(he.next.next.vert)
        return result
        # return [, he.next.vert, he.next.next.vert]

    cdef half_three_tuple face_halfs(self, Face* face):
        cdef HalfEdge *he = face.he
        # cdef result vector
        return (he, he.next, he.next.next)

    cdef tuple face_center(self, Face* face):
        cdef HalfEdge *he = face.he
        cdef double x = he.vert.x + he.next.vert.x + he.next.next.vert.x
        cdef double y = he.vert.y + he.next.vert.y + he.next.next.vert.y
        return (x/3.0, y/3.0)

    # cdef list boundary(self):
    #     cdef list result = []
    #     cdef HalfEdge *he
    #     he = self.boundary_start
    #     result.append(he)
    #     he = he.next
    #     while he != self.boundary_start:
    #         result.append(he)
    #         he = he.next
    #     return result

    cdef bint is_boundary_edge(self, Edge* e):
        return e.he.face == NULL or e.he.twin.face == NULL

    cdef bint is_boundary_vert(self, Vert* v):
        cdef Edge *e
        cdef vector[Edge*] neighbors = self.edge_neighbors(v)
        for e in neighbors:
            if self.is_boundary_edge(e):
                return True
        return False

    cdef vector[Vert*]& vert_neighbors(self, Vert* v):
        cdef:
            (HalfEdge *) h, start, h_twin
            vector[Vert*] result
        h = v.he
        start = h

        h_twin = h.twin
        v = h_twin.vert
        result.push_back(v)
        h = h_twin.next

        while h != start:
            h_twin = h.twin
            v = h_twin.vert
            result.push_back(v)
            h = h_twin.next

        return result

    cdef vector[Edge*]& edge_neighbors(self, Vert* v):
        cdef:
            (HalfEdge *) h, start, h_twin
            Edge *e
            vector[Edge*] result

        h = v.he
        start = h

        h_twin = h.twin
        e = h_twin.edge
        result.push_back(e)
        h = h_twin.next

        while h != start:
            h_twin = h.twin
            e = h_twin.edge
            result.push_back(e)
            h = h_twin.next

        return result

    cdef Vert_pair edge_verts(self, Edge* e):
        return <Vert_pair>(e.he.vert, e.he.next.vert)

    cdef double edge_length(self, Edge* e):
        cdef Vert *p1 = e.he.vert
        cdef Vert *p2 = e.he.next.vert
        cdef double dx = p1.x-p2.x
        cdef double dy = p1.y-p2.y
        return sqrt(dx*dx + dy*dy)
