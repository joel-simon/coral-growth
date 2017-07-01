from __future__ import division

import numpy as np
cimport numpy as np
from libc.math cimport sqrt

cdef class Vert:
    def __init__(self, id, x, y, he=None):
        self.id = id
        self.x = x
        self.y = y
        self.x0 = x
        self.y0 = y
        self.he = he
        self.cid = None

        # Used for physics
        self.prev_x = x
        self.prev_y = y
        self.accel_x = 0
        self.accel_y = 0
        self.fixed = False

cdef class Edge:
    def __init__(self, id, he=None):
        self.id = id
        self.he = he

        # Used for physics
        self.target = 0
        self.strain = 0


cdef class Face:
    __slots__ = ['id', 'he']
    def __init__(self, id, he=None):
        self.id = id
        self.he = he

cdef class HalfEdge(object):
    def __init__(self, twin=None, next=None, vert=None, edge=None, face=None):
        self.twin = twin
        self.next = next
        self.vert = vert
        self.edge = edge
        self.face = face

cdef class Mesh:
    def __init__(self, raw_points, raw_polygons):
        self.verts = []
        self.edges = []
        self.faces = []
        self.halfs = []
        self.boundary_start = None # Store a reference to a boundary vert for perimeter iteration.

        self.__v_id = 0
        self.__e_id = 0
        self.__f_id = 0

        """ Build half-edge data structure.
        """
        vertices_to_half = {}
        pair_to_half = {} # (i,j) tuple -> half edge

        # Create Vert objects.
        for i, p in enumerate(raw_points):
            v = self.__vert(p[0], p[1])

        # Create Face objects.
        for poly in raw_polygons:
            if len(poly) != 3:
                raise ValueError('Only Triangular Meshes Accepted.')

            face = self.__face()
            face_half_edges = []

            # Create half-edge for each edge.
            for i, a in enumerate(poly):
                b = poly[ (i+1) % len(poly) ]
                pair = (self.verts[a], self.verts[b])
                h_ab = self.__half(face=face, vert=self.verts[a], twin=None, next=None, edge=None)
                vertices_to_half[pair] = h_ab
                pair_to_half[pair] = h_ab
                face_half_edges.append(h_ab)

                # Link to twin if it exists.
                pair_ba = (self.verts[b], self.verts[a])
                if pair_ba in vertices_to_half:
                    h_ba = vertices_to_half[pair_ba]
                    h_ba.twin = h_ab
                    h_ab.twin = h_ba
                    h_ab.edge = h_ba.edge
                else:
                    edge = self.__edge(h_ab)
                    h_ab.edge = edge

            # Link them together via their 'next' pointers.
            for i, he in enumerate(face_half_edges):
                he.next = face_half_edges[(i+1) % len(poly)]

        # Create boundary edges.
        he_boundary = {}
        for (a, b) in pair_to_half:
            if (b, a) not in pair_to_half:
                twin = pair_to_half[(a,b)]
                h_ba = self.__half(vert=b, twin=twin, next=None, edge=twin.edge, face=None)
                he_boundary[b] = (h_ba, a)

        # Link external boundary edges.
        for start, (he, end) in he_boundary.items():
            he.next = he_boundary[end][0]
            self.boundary_start = he

    def __str__(self):
        s = "Mesh"
        for v in self.verts:
            s += "\n\tv_%i: %i, %i" % (v.id, int(v.x), int(v.y))

        for f in self.faces:
            s += "\n\tf_%i: %s" % (f.id, str([v.id for v in self.face_verts(f)]))

        return s

    # Constructor functions.
    cdef Vert __vert(self, double x, double y, he=None):
        cdef Vert vert = Vert(self.__v_id, x, y, he)
        self.__v_id += 1
        self.verts.append(vert)
        return vert

    cdef Edge __edge(self, he=None):
        cdef Edge edge = Edge(self.__e_id, he)
        self.__e_id += 1
        self.edges.append(edge)
        return edge

    cdef Face __face(self, he=None):
        cdef Face face = Face(self.__f_id, he)
        self.__f_id += 1
        self.faces.append(face)
        if he:
            he.face = face
        return face

    cdef HalfEdge __half(self, HalfEdge twin=None, HalfEdge next=None, Vert vert=None, Edge edge=None, Face face=None):
    # cdef HalfEdge __half(self, Twin* twin=NULL, HalfEdge* next=NULL, Vert* vert=NULL, Edge* edge=NULL, Face* face=NULL):
        cdef HalfEdge he = HalfEdge(twin, next, vert, edge, face)
        # he.twin = twin
        # he.next = next
        # he.vert = vert
        # he.edge = edge
        # he.face = face
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

    # Meh modifying
    cpdef void edge_flip(self, Edge edge):
        cdef HalfEdge he1, he2, he11, he12, he22
        cdef Vert v1, v2, v3, v4
        cdef Face f1, f2

        # http://mrl.nyu.edu/~dzorin/cg05/lecture11.pdf
        if self.is_boundary_edge(edge):
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

    cpdef Vert edge_split(self, Edge edge):
        """ Split an external or internal edge and return new vertex.
        """
        cdef Face other_face, f_nbc, f_anc, f_dna, f_dbn
        cdef HalfEdge h_ab, h_ba, h_bc, h_ca, h_cn, h_nc, h_an, h_na, h_bn
        cdef HalfEdge h_ad, h_db, h_dn, h_nd
        cdef Edge e_an, e_nb, e_cn, e_nd
        cdef Vert v_a, v_b, v_c, v_n
        cdef double x, y

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
        h_bc.face = f_nbc
        h_bc.next = h_cn
        h_ca.next = h_an
        h_an.next = h_nc
        h_cn.next = h_nb
        h_bn.next = h_na
        h_bn.twin = h_nb

        if other_face:
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
            h_db.face = f_dbn
            h_db.next = h_bn
            h_ad.face = f_dna
            h_ad.next = h_dn
            v_b.he = h_bn

        return v_n

    cpdef void flip_if_better(self, Edge edge):
        e = .01
        if self.is_boundary_edge(edge):
            return

        p1 = edge.he.next.next.vert
        p2 = edge.he.twin.next.next.vert
        d = sqrt((p1.x-p2.x)**2 + (p1.y-p2.y)**2)

        if self.edge_length(edge) - d > e:
            self.edge_flip(edge)

    def to_arrays(self):
        points = np.zeros((len(self.verts), 2))
        edges = np.zeros((len(self.edges), 2), dtype='int64')
        v_to_i = dict()

        for i, vert in enumerate(self.verts):
            v_to_i[vert] = i
            points[i, 0] = vert.x
            points[i, 1] = vert.y

        for j, edge in enumerate(self.edges):
            v1, v2 = self.edge_verts(edge)
            edges[j, 0] = v_to_i[v1]
            edges[j, 1] = v_to_i[v2]

        return {'points': points, 'edges': edges }

    cpdef void smooth(self):
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

                neighbors = self.vert_neighbors(v)

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

    cpdef list adapt(self, double max_edge_length):
        cdef:
            list new_verts = []
            Edge edge
            Vert vert, v1, v2

        for edge in self.edges:
            if self.edge_length(edge) > max_edge_length:
                v1, v2 = self.edge_verts(edge)
                vert = self.edge_split(edge)
                new_verts.append((vert, v1, v2))

        for edge in self.edges:
            self.flip_if_better(edge)

        self.smooth()

        return new_verts

    # Query
    cpdef list face_verts(self, Face face):
        cdef HalfEdge he = face.he
        return [he.vert, he.next.vert, he.next.next.vert]

    cpdef list face_halfs(self, Face face):
        cdef HalfEdge he = Face.he
        return [he, he.next, he.next.next]

    cpdef tuple face_center(self, Face face):
        cdef HalfEdge he = Face.he
        cdef double x = he.vert.x + he.next.vert.x + he.next.next.vert.x
        cdef double y = he.vert.y + he.next.vert.y + he.next.next.vert.y
        return (x/3.0, y/3.0)

    cpdef list boundary(self):
        cdef list result = []
        cdef HalfEdge he
        he = self.boundary_start
        result.append(he)
        he = he.next
        while he != self.boundary_start:
            result.append(he)
            he = he.next
        return result

    cpdef bint is_boundary_edge(self, Edge e):
        return e.he.face == None or e.he.twin.face == None

    cpdef bint is_boundary_vert(self, Vert v):
        cdef Edge e
        cdef list neighbors = self.edge_neighbors(v)
        for e in neighbors:
            if self.is_boundary_edge(e):
                return True
        return False

    cpdef list vert_neighbors(self, Vert v):
        cdef:
            HalfEdge h, start, h_twin
            list result = []
        h = v.he
        start = h

        h_twin = h.twin
        v = h_twin.vert
        result.append(v)
        h = h_twin.next

        while h != start:
            h_twin = h.twin
            v = h_twin.vert
            result.append(v)
            h = h_twin.next

        return result

    cpdef list edge_neighbors(self, Vert v):
        cdef:
            HalfEdge h, start, h_twin
            Edge e
            list result = []

        h = v.he
        start = h

        h_twin = h.twin
        e = h_twin.edge
        result.append(e)
        h = h_twin.next

        while h != start:
            h_twin = h.twin
            e = h_twin.edge
            result.append(e)
            h = h_twin.next

        return result

    cpdef tuple edge_verts(self, Edge e):
        return (e.he.vert, e.he.next.vert)

    cpdef double edge_length(self, Edge e):
        cdef Vert p1 = e.he.vert
        cdef Vert p2 = e.he.next.vert
        cdef double dx = p1.x-p2.x
        cdef double dy = p1.y-p2.y
        return sqrt(dx*dx + dy*dy)
