from __future__ import division, print_function


from plant_growth.vector3D cimport cross, dot, vadd, vsub, vdivf, vdist, inormalized, vmultf

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
        self.vert_faces_buffer = <Face **>self.mem.alloc(64, sizeof(Face *))

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
            verts[i] = self.__vert(p[0], p[1], p[2], he=NULL)

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

    @classmethod
    def from_obj(cls, filename):
        points = []
        faces = []

        for line in open(filename, 'r'):
            if line.startswith('#'):
                continue
            values = line.split()
            if not values:continue
            if values[0] == 'v':
                # points.append(list(map(float, values[1:4])))
                points.append([float(v) for v in values[1:4]])
            elif values[0] == 'f':
                face = []
                for v in values[1:]:
                    w = v.split('/')
                    face.append(int(w[0]) - 1) # .obj uses 1 based indexing.
                faces.append(face)

        return cls(points, faces)

    cdef void append_data(self, void *data, Node **list_start, Node **list_end):
        cdef Node *node = <Node *>self.mem.alloc(1, sizeof(Node))
        node.data = data
        node.next = NULL

        if list_start[0] == NULL:
            list_start[0] = node
            list_end[0] = node
        else:
            list_end[0].next = node
            list_end[0] = node

    # Constructor functions.
    cdef Vert* __vert(self, double x, double y, double z, HalfEdge* he=HNULL) except NULL:
        cdef Vert *vert = <Vert *>self.mem.alloc(1, sizeof(Vert))
        self.append_data(vert, &self.verts, &self.verts_end)

        vert.id = self.n_verts

        vert.p[0] = x
        vert.p[1] = y
        vert.p[2] = z
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
        face.normal[0] = 0
        face.normal[1] = 0
        face.normal[2] = 0
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

    # Mesh modifying
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
            # double n, x, y, z

        node = self.edges
        for i in range(self.n_edges):
            edge = <Edge *>node.data
            node = node.next
            self.flip_if_better(edge)

        node = self.verts
        for i in range(self.n_verts):
            v = <Vert *>node.data
            node = node.next

            if not self.is_boundary_vert(v):
                v.p0.x = 0
                v.p0.y = 0
                v.p0.z = 0
                n_neighbors = self.vert_neighbors(v)

                for n_i in range(n_neighbors):
                    v.p0.x += self.vert_neighbor_buffer[n_i].p.x
                    v.p0.y += self.vert_neighbor_buffer[n_i].p.y
                    v.p0.z += self.vert_neighbor_buffer[n_i].p.y

                vdivf(v.p0, v.p0, n_neighbors)

        node = self.verts
        for i in range(self.n_verts):
            v = <Vert *>node.data
            node = node.next
            if not self.is_boundary_vert(v):
                v.p.x = v.p0.x
                v.p.y = v.p0.y

    # Mesh calculation
    cpdef void calculate_normals(self):
        cdef:
            Node *node
            Face *face
            (Vert *) va, vb, vc
            double vab[3]
            double vbc[3]

        """ Calculate face normals. """
        node = self.faces
        for i in range(self.n_faces):
            face = <Face *>node.data
            node = node.next

            self.face_verts(face, &va, &vb, &vc)
            vsub(vab, vb.p, va.p)
            vsub(vbc, vc.p, vb.p)
            cross(face.normal, vab, vbc)
            inormalized(face.normal)

        """ Initialize vert norm values. """
        node = self.verts
        for _ in range(self.n_verts):
            va = <Vert *> node.data
            node = node.next
            vmultf(va.normal, va.normal, 0)

        """ Add face normal to all adjacent verts. """
        node = self.faces
        for _ in range(self.n_faces):
            face = <Face *>node.data
            node = node.next

            self.face_verts(face, &va, &vb, &vc)
            vadd(va.normal, va.normal, face.normal)
            vadd(vb.normal, vb.normal, face.normal)
            vadd(vc.normal, vc.normal, face.normal)

        """ Normalize normals. """
        node = self.verts
        for i in range(self.n_verts):
            va = <Vert *> node.data
            inormalized(va.normal)
            node = node.next

        # node = self.faces
        # for i in range(self.n_faces):
        #     face = <Face *> node.data
        #     inormalized(&face.normal)
        #     node = node.next

    cpdef void calculate_curvature(self):
        # https://computergraphics.stackexchange.com/questions/1718/what-is-the-simplest-way-to-compute-principal-curvature-for-a-mesh-triangle
        cdef:
            Node *vnode = self.verts
            Node *enode = self.edges
            Edge *e
            (Face *) f1, f2
            (Vert *) v1, v2
            (HalfEdge *) h, start, h_twin
            int i = 0
            double a[3], b[3]
            double total_curvature, d

        while vnode != NULL:
            v1 = <Vert *>vnode.data
            i = 0
            total_curvature = 0

            h = v1.he
            start = h

            while True:
                h_twin = h.twin

                ###################
                # Curvature logic.
                e = h.edge
                f1 = h.face
                f2 = h_twin.face

                vsub(a, h.vert.normal, h.twin.vert.normal)
                vsub(b, h.vert.p, h.twin.vert.p)
                d = vdist(h.vert.p, h_twin.vert.p)

                if d != 0:
                    total_curvature += dot(a, b) / d
                    i += 1

                ####################
                i += 1
                h = h_twin.next

                if h == start:
                    break

            if i != 0:
                v1.curvature = total_curvature / i

            vnode = vnode.next

    cpdef double volume(self):
        # https://stackoverflow.com/a/1568551/2175411
        cdef size_t i = 0
        cdef double s = 0
        cdef (Vert *) v1, v2, v3
        cdef Node *node = self.faces
        cdef Face *face

        for i in range(self.n_faces):
            face = <Face *> node.data
            self.face_verts(face, &v1, &v2, &v3)
            s += signed_triangle_volume(v1.p, v2.p, v3.p)
            node = node.next

        return abs(s)

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
        cdef double x, y, z

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
        x = (v_a.p[0] + v_b.p[0]) / 2.0
        y = (v_a.p[1] + v_b.p[1]) / 2.0
        z = (v_a.p[2] + v_b.p[2]) / 2.0
        v_n = self.__vert(x, y, z)

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
        d = vdist(v1.p, v2.p)

        if self.edge_length(e) - d > epsilon:
            self.edge_flip(e)

    # Query
    def export(self):
        """ Return mesh as numpy arrays.
        """
        cdef:
            (Vert*) v1, v2, v3
            Node *node
            Edge *edge
            Face *face
            dict vid_to_idx = {}

        self.calculate_normals()
        self.calculate_curvature()

        verts = np.zeros((self.n_verts, 3))
        vert_normals = np.zeros((self.n_verts, 3))
        curvature = np.zeros(self.n_verts)

        edges = np.zeros((self.n_edges, 2), dtype='i')
        faces = np.zeros((self.n_faces, 3), dtype='i')
        face_normals = np.zeros((self.n_faces, 3))

        node = self.verts
        for i in range(self.n_verts):
            v = <Vert *>node.data
            verts[i, 0] = v.p[0]
            verts[i, 1] = v.p[1]
            verts[i, 2] = v.p[2]
            vid_to_idx[v.id] = i
            vert_normals[i] = v.normal#[v.normal.x, v.normal.y, v.normal.z]
            curvature[i] = v.curvature
            node = node.next

        node = self.edges
        for i in range(self.n_edges):
            edge = <Edge *>node.data
            self.edge_verts(edge, &v1, &v2)
            edges[i, 0] = vid_to_idx[v1.id]
            edges[i, 1] = vid_to_idx[v2.id]
            node = node.next

        node = self.faces
        for i in range(self.n_faces):
            face = <Face *>node.data
            self.face_verts(face, &v1, &v2, &v3)
            faces[i, 0] = vid_to_idx[v1.id]
            faces[i, 1] = vid_to_idx[v2.id]
            faces[i, 2] = vid_to_idx[v3.id]
            face_normals[i] = face.normal#[face.normal.x, face.normal.y, face.normal.z]
            node = node.next

        return {'vertices': verts, 'edges':edges, 'faces':faces,
                'vertice_normals': vert_normals, 'face_normals':face_normals,
                'curvature': curvature}

    cdef void face_verts(self, Face* face, Vert** va, Vert** vb, Vert** vc):
        cdef HalfEdge *he = face.he
        va[0] = he.vert
        vb[0] = he.next.vert
        vc[0] = he.next.next.vert

    cdef void face_halfs(self, Face* face, HalfEdge* ha, HalfEdge* hb, HalfEdge* hc):
        cdef HalfEdge *he = face.he
        ha = he
        hb = he.next
        hc = he.next.next

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

    cdef Node* vert_faces(self, Vert* v) except *:
        cdef:
            (HalfEdge *) h, start, h_twin
            (Node *) start_node, last_node, node

        h = v.he
        start = h

        start_node = NULL

        while True:
            node = <Node *>self.mem.alloc(1, sizeof(Node))
            node.data = <void *>h.face
            if start_node == NULL: # First iteration.
                start_node = node

            else:
                last_node.next = node

            last_node = node

            h_twin = h.twin
            h = h_twin.next

            if h == start:
                break

        node.next = NULL
        return start_node

    cdef int vert_neighbors(self, Vert* v):
        cdef:
            (HalfEdge *) h, start, h_twin
            int i = 0

        h = v.he
        start = h

        while True:
            h_twin = h.twin
            v = h_twin.vert
            self.vert_neighbor_buffer[i] = v
            i += 1
            h = h_twin.next

            if h == start:
                break

        return i

    cdef inline void edge_verts(self, Edge* e, Vert** va, Vert** vb):
        va[0] = e.he.vert
        vb[0] = e.he.twin.vert

    cdef inline double edge_length(self, Edge* e):
        cdef Vert *v1 = e.he.vert
        cdef Vert *v2 = e.he.next.vert
        # cdef double dx = p1.x-p2.x
        # cdef double dy = p1.y-p2.y
        return vdist(v1.p, v2.p)
