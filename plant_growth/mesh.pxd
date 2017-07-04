
from cymem.cymem cimport Pool

cdef struct Vert:
    int id
    double x, y, x0, y0
    bint is_boundary
    HalfEdge *he

    # Physics
    bint fixed
    double deform_x, deform_y, prev_x, prev_y, accel_x, accel_y

cdef struct Edge:
    int id
    double target, strain
    HalfEdge *he

cdef struct Face:
    int id
    HalfEdge *he

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

    cdef Vert** vert_neighbor_buffer
    cdef Edge** edge_neighbor_buffer

    # cdef HalfEdge *boundary_start

    cdef public int n_verts, n_edges, n_faces, n_halfs

    cdef void append_data(self, void *data, Node **list_start, Node **list_end)
    # Constructor functions.
    cdef Vert* __vert(self, double x, double y, HalfEdge* he=*) except NULL
    cdef Edge* __edge(self, HalfEdge* he=*) except NULL
    cdef Face* __face(self, HalfEdge* he=*) except NULL
    cdef HalfEdge* __half(self, HalfEdge* twin=*, HalfEdge* next=*,
                          Vert* vert=*, Edge* edge=*, Face* face=*) except NULL

    # Public functions.
    cpdef int split_edges(self, double max_edge_length) except -1
    cpdef void smooth(self) except *

    cdef void edge_flip(self, Edge* e)
    cdef Vert* edge_split(self, Edge* e)
    cdef void flip_if_better(self, Edge* e)
    # cdef list adapt(self, double max_edge_length)

    # Query
    cdef void face_verts(self, Face* face, Vert* va, Vert* vb, Vert* vc)
    cdef void face_halfs(self, Face* face, HalfEdge* ha, HalfEdge* hb, HalfEdge* hc)
    # cdef void face_center(self, Face* face, double *x, double *y):
    # cdef list boundary(self)

    cdef Edge* edge_between(self, Vert *v1, Vert *v2) except *
    # cdef void edge_between(self, Vert *v1, Vert *v2, Edge** edge) except *
    cdef inline bint is_boundary_edge(self, Edge* e)
    cdef inline bint is_boundary_vert(self, Vert* v)
    cdef int vert_neighbors(self, Vert* v)
    cdef int edge_neighbors(self, Vert* v) nogil

    cdef inline void edge_verts(self, Edge* e, Vert** va, Vert** vb)
    cdef inline double edge_length(self, Edge* e)
