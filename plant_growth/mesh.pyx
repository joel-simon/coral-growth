from __future__ import division, print_function
from libc.math cimport sqrt
from libc.stdint cimport uintptr_t
import numpy as np
cimport numpy as np
from cymem.cymem cimport Pool

cdef:
    Vert *VNULL = <Vert*> NULL
    Edge *ENULL = <Edge*> NULL
    Face *FNULL = <Face*> NULL
    HalfEdge *HNULL = <HalfEdge*> NULL

cdef class Mesh:
    def __init__(self, raw_points, raw_polygons):
        """ Allocate Data.
        """
        # self.boundary_start = HNULL # Store a reference to a boundary vert for perimeter iteration.
        self.n_verts = 0
        self.n_edges = 0
        self.n_faces = 0
        self.n_halfs = 0

        self.mem = Pool()

        self.vert_neighbor_buffer = <Vert **>self.mem.alloc(24, sizeof(Vert *))
        self.edge_neighbor_buffer = <Edge **>self.mem.alloc(24, sizeof(Edge *))

        # objects for construction.
        cdef int nv = len(raw_points)
        cdef int nf = len(raw_polygons)
        cdef (HalfEdge *) he, h_ba, h_ab, twin
        cdef dict pair_to_half = {} # (i,j) tuple -> half edge
        cdef dict he_boundary = {} # Create boundary edges.
        cdef Vert** verts = <Vert **>self.mem.alloc(nv, sizeof(Vert *))
        cdef HalfEdge** halfs = <HalfEdge **>self.mem.alloc(6*nf, sizeof(HalfEdge *))
        cdef int n_halfs = 0
        cdef int a, b

        """ Build half-edge data structure.
        """
        # Create Vert objects.
        for i, p in enumerate(raw_points):
            verts[i] = self.__vert(p[0], p[1])

        # Create Face objects.
        for poly in raw_polygons:
            if len(poly) != 3:
                raise ValueError('Only Triangular Meshes Accepted.')

            face = self.__face()
            face_half_edges = []

            # Create half-edge for each edge.
            for i, a in enumerate(poly):
                b = poly[ (i+1) % len(poly) ]
                pair_ab = (verts[a].id, verts[b].id)
                pair_ba = (verts[b].id, verts[a].id)

                h_ab = self.__half(face=face, vert=verts[a], twin=NULL, next=NULL, edge=NULL)
                halfs[n_halfs] = h_ab
                pair_to_half[pair_ab] = n_halfs
                face_half_edges.append(n_halfs)
                n_halfs += 1

                # Link to twin if it exists.
                if pair_ba in pair_to_half:
                    h_ba =  halfs[pair_to_half[pair_ba]]
                    h_ba.twin = h_ab
                    h_ab.twin = h_ba
                    h_ab.edge = h_ba.edge
                else:
                    edge = self.__edge(h_ab)
                    h_ab.edge = edge

            # Link them together via their 'next' pointers.
            for i, he_id in enumerate(face_half_edges):
                he = halfs[he_id]
                he.next = halfs[face_half_edges[(i+1) % len(poly)]]

        for (a, b) in pair_to_half:
            if (b, a) not in pair_to_half:
                twin = halfs[pair_to_half[(a, b)]]
                h_ba = self.__half(vert=verts[b], twin=twin, next=NULL, edge=twin.edge, face=NULL)
                halfs[n_halfs] = h_ba
                he_boundary[b] = (n_halfs, a)
                n_halfs += 1

        cdef int start, end
        # Link external boundary edges.
        for start, (he_id, end) in he_boundary.items():
            he = halfs[he_id]
            he.next = halfs[he_boundary[end][0]]
            # self.boundary_start = he

    cdef void append_data(self, void *data, Node **list_start, Node **list_end):
        cdef Node *node = <Node *>self.mem.alloc(1, sizeof(Node))
        node.data = data
        # node.next = list_start[0]
        # list_start[0] = node
        if list_start[0] == NULL:
            list_start[0] = node
            list_end[0] = node
        else:
            list_end[0].next = node
            list_end[0] = node

    # Constructor functions.
    cdef Vert* __vert(self, double x, double y, HalfEdge* he=HNULL) except NULL:
        cdef Vert *vert = <Vert *>self.mem.alloc(1, sizeof(Vert))
        self.append_data(vert, &self.verts, &self.verts_end)

        vert.id = self.n_verts
        vert.x = x
        vert.y = y
        vert.he = he

        self.n_verts += 1
        return vert

    cdef Edge* __edge(self, HalfEdge* he=HNULL) except NULL:
        cdef Edge *edge = <Edge *>self.mem.alloc(1, sizeof(Edge))
        self.append_data(edge, &self.edges, &self.edges_end)

        edge.id = self.n_edges
        edge.he = he
        self.n_edges += 1

        return edge

    cdef Face* __face(self, HalfEdge* he=HNULL) except NULL:
        cdef Face *face = <Face *>self.mem.alloc(1, sizeof(Face))
        self.append_data(face, &self.faces, &self.faces_end)

        face.id = self.n_faces
        face.he = he
        self.n_faces += 1
        if he:
            he.face = face
        return face

    cdef HalfEdge* __half(self, HalfEdge* twin=HNULL, HalfEdge* next=HNULL,
                          Vert* vert=VNULL, Edge* edge=ENULL, Face* face=FNULL) except NULL:
        cdef HalfEdge *he = <HalfEdge *>self.mem.alloc(1, sizeof(HalfEdge))
        self.append_data(edge, &self.halfs, &self.halfs_end)

        he.id = self.n_halfs
        he.twin = twin
        he.next = next
        he.vert = vert
        he.edge = edge
        he.face = face
        self.n_halfs += 1
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
    cpdef int split_edges(self, double max_edge_length) except -1:
        cdef int i, n
        n = 0
        cdef Node* node
        cdef Edge* edge

        node = self.edges
        for i in range(self.n_edges):
            edge = <Edge *>node.data
            if self.edge_length(edge) >= max_edge_length:
                n += 1
                self.edge_split(edge)
            node = node.next

        return n

    cpdef void smooth(self) except *:
        """ Smooth each interior vertex by moving towared average of neighbors.
        """
        cdef:
            Vert *v
            Node *node
            Edge *edge
            int i, n_i, n_neighbors
            double n

        node = self.edges
        for i in range(self.n_edges):
            edge = <Edge *>node.data
            node = node.next
            self.flip_if_better(edge)

        node = self.verts
        for i in range(self.n_verts):
            v = <Vert *>node.data
            node = node.next

            if self.is_boundary_vert(v) == 0:
                v.x0 = 0
                v.y0 = 0
                n_neighbors = self.vert_neighbors(v)

                for n_i in range(n_neighbors):
                    v.x0 += self.vert_neighbor_buffer[n_i].x
                    v.y0 += self.vert_neighbor_buffer[n_i].y

                v.y0 /= n_neighbors
                v.x0 /= n_neighbors

        node = self.verts
        for i in range(self.n_verts):
            v = <Vert *>node.data
            node = node.next
            if self.is_boundary_vert(v) == 0:
                v.x = v.x0
                v.y = v.y0

    # Edge operations
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

        v_n.is_boundary = v_a.is_boundary and v_b.is_boundary

        return v_n

    cdef void flip_if_better(self, Edge* e):
        cdef:
            double d
            double epsilon = .01
            (Vert *) v1, v2

        if self.is_boundary_edge(e):
            return

        v1 = e.he.next.next.vert
        v2 = e.he.twin.next.next.vert
        d = sqrt((v1.x-v2.x)**2 + (v1.y-v2.y)**2)

        if self.edge_length(e) - d > epsilon:
            self.edge_flip(e)

    # Query
    def py_data(self):
        """ Return mesh as numpy arrays.
        """
        verts = np.zeros((self.n_verts, 2))
        edges = np.zeros((self.n_edges, 2), dtype='i')
        cdef (Vert*) v1, v2
        cdef Node *node
        cdef dict vid_to_idx = {}

        node = self.verts
        for i in range(self.n_verts):
            v = <Vert *>node.data
            node = node.next
            verts[i, 0] = v.x
            verts[i, 1] = v.y
            vid_to_idx[v.id] = i

        node = self.edges
        for i in range(self.n_edges):
            edge = <Edge *>node.data
            node = node.next
            self.edge_verts(edge, &v1, &v2)
            edges[i, 0] = vid_to_idx[v1.id]
            edges[i, 1] = vid_to_idx[v2.id]

        return {'vertices': verts, 'edges':edges}

    cdef void face_verts(self, Face* face, Vert* va, Vert* vb, Vert* vc):
        cdef HalfEdge *he = face.he
        va = he.vert
        vb = he.next.vert
        vc = he.next.next.vert

    cdef void face_halfs(self, Face* face, HalfEdge* ha, HalfEdge* hb, HalfEdge* hc):
        cdef HalfEdge *he = face.he
        ha = he
        hb = he.next
        hc = he.next.next

    cdef Edge* edge_between(self, Vert *v1, Vert *v2) except *:
        cdef Edge *e
        cdef int n_e = self.edge_neighbors(v1)
        cdef int i

        for i in range(n_e):
            e = self.edge_neighbor_buffer[i]
            if e.he.vert == v2 or e.he.twin.vert == v2:
                return e

        return NULL

    cdef inline bint is_boundary_edge(self, Edge* e):
        return e.he.face == NULL or e.he.twin.face == NULL

    cdef inline bint is_boundary_vert(self, Vert* v):
        return v.is_boundary
        # cdef Edge *e
        # cdef int n_e = self.edge_neighbors(v)
        # cdef int i

        # for i in range(n_e):
        #     e = self.edge_neighbor_buffer[i]
        #     if self.is_boundary_edge(e):
        #         return True
        # return False

    cdef int vert_neighbors(self, Vert* v):
        cdef:
            (HalfEdge *) h, start, h_twin
            int i = 0

        h = v.he
        start = h

        h_twin = h.twin
        v = h_twin.vert
        self.vert_neighbor_buffer[i] = v
        i += 1
        h = h_twin.next

        while h != start:
            h_twin = h.twin
            v = h_twin.vert
            self.vert_neighbor_buffer[i] = v
            i += 1
            h = h_twin.next

        return i

    cdef int edge_neighbors(self, Vert* v) nogil:
        cdef:
            (HalfEdge *) h, start, h_twin
            Edge *e,
            int i = 0

        h = v.he
        start = h

        h_twin = h.twin
        e = h_twin.edge
        self.edge_neighbor_buffer[i] = e
        i += 1
        h = h_twin.next

        while h != start:
            h_twin = h.twin
            e = h_twin.edge
            self.edge_neighbor_buffer[i] = e
            i += 1
            h = h_twin.next

        return i

    cdef inline void edge_verts(self, Edge* e, Vert** va, Vert** vb):
        va[0] = e.he.vert
        vb[0] = e.he.twin.vert

    cdef inline double edge_length(self, Edge* e):
        cdef Vert *p1 = e.he.vert
        cdef Vert *p2 = e.he.next.vert
        cdef double dx = p1.x-p2.x
        cdef double dy = p1.y-p2.y
        return sqrt(dx*dx + dy*dy)
