from cymem.cymem cimport Pool

cdef struct Vert:
    int id
    double p[3]
    double p0[3] # Used to hold temporary values when smoothing.
    # double next_p[3]
    HalfEdge *he
    double normal[3]
    double curvature
    bint is_boundary

cdef struct Edge:
    int id
    double target, strain
    HalfEdge *he

cdef struct Face:
    int id
    HalfEdge *he
    double normal[3]

cdef struct HalfEdge:
    int id
    HalfEdge *twin
    HalfEdge *next
    Vert *vert
    Edge *edge
    Face *face

cdef struct Node:
    void *data
    Node *next

cdef inline double signed_triangle_volume(double p1[3], double p2[3], double p3[3]):
    cdef double v321 = p3[0] * p2[1] * p1[2]
    cdef double v231 = p2[0] * p3[1] * p1[2]
    cdef double v312 = p3[0] * p1[1] * p2[2]
    cdef double v132 = p1[0] * p3[1] * p2[2]
    cdef double v213 = p2[0] * p1[1] * p3[2]
    cdef double v123 = p1[0] * p2[1] * p3[2]
    return (1./6.0) * (-v321 + v231 + v312 - v132 - v213 + v123)

cdef class Mesh:
    cdef Pool mem

    cdef Node* verts
    cdef Node* faces
    cdef Node* edges
    cdef Node* halfs

    cdef Node* verts_end
    cdef Node* faces_end
    cdef Node* edges_end
    cdef Node* halfs_end

    cdef Vert **vert_neighbor_buffer
    cdef Edge **edge_neighbor_buffer
    cdef Face **vert_faces_buffer
    cdef public int n_verts, n_edges, n_faces, n_halfs

    # Constructor functions.
    cdef Vert* __vert(self, double x, double y, double z, HalfEdge* he=*) except NULL
    cdef Edge* __edge(self, HalfEdge* he=*) except NULL
    cdef Face* __face(self, HalfEdge* he=*) except NULL
    cdef HalfEdge* __half(self, HalfEdge* twin=*, HalfEdge* next=*,
                          Vert* vert=*, Edge* edge=*, Face* face=*) except NULL

    # Private functions.
    cdef void append_data(self, void *data, Node **list_start, Node **list_end)

    # Public functions.
    cpdef int split_edges(self, double max_edge_length) except -1
    cpdef void smooth(self) except *
    cpdef double volume(self)

    cpdef void calculate_normals(self)
    cpdef void calculate_curvature(self)

    cdef void edge_flip(self, Edge* e)
    cdef Vert* edge_split(self, Edge* e)
    cdef void flip_if_better(self, Edge* e)

    # Queries
    cdef void face_verts(self, Face* face, Vert** va, Vert** vb, Vert** vc)
    cdef void face_halfs(self, Face* face, HalfEdge* ha, HalfEdge* hb, HalfEdge* hc)

    cdef Node* vert_faces(self, Vert* v) except *
    cdef int vert_neighbors(self, Vert* v)
    # cdef int edge_neighbors(self, Vert* v)

    # cdef Edge* edge_between(self, Vert *v1, Vert *v2) except *
    cdef inline bint is_boundary_edge(self, Edge *e)
    cdef inline bint is_boundary_vert(self, Vert *v)

    cdef inline void edge_verts(self, Edge *e, Vert **va, Vert **vb)
    cdef inline double edge_length(self, Edge* e)
