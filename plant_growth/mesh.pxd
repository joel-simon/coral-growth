
from libcpp.vector cimport vector
from libcpp.pair cimport pair
from libcpp.vector cimport tuple
# cdef class Vert:
#     cdef public int id
#     cdef public double x, y, x0, y0, deform_x, deform_y, prev_x, prev_y, accel_x, accel_y
#     cdef public bint fixed
#     cdef public HalfEdge he
#     cdef public object cid

# cdef class Edge:
#     cdef public int id
#     cdef public double target, strain
#     cdef public HalfEdge he

# cdef class Face:
#     cdef public int id
#     cdef public HalfEdge he

# cdef class HalfEdge(object):
#     cdef public HalfEdge twin, next
#     cdef public Vert vert
#     cdef public Edge edge
#     cdef public Face face

cdef struct Vert:
    int id
    double x, y, x0, y0, deform_x, deform_y, prev_x, prev_y, accel_x, accel_y
    bint fixed
    HalfEdge *he
    int cid
ctypedef Vert* Vert_pntr
ctypedef pair[Vert_pntr, Vert_pntr] Vert_pair

cdef struct Edge:
    int id
    double target, strain
    HalfEdge *he

cdef struct Face:
    int id
    HalfEdge *he

cdef struct HalfEdge:
    HalfEdge *twin
    HalfEdge *next
    Vert *vert
    Edge *edge
    Face *face
ctypedef HalfEdge* HalfEdge_pntr

ctypedef (Vert_pntr, Vert_pntr, Vert_pntr) vert_three_tuple
ctypedef (HalfEdge_pntr, HalfEdge_pntr, HalfEdge_pntr) half_three_tuple

cdef struct VertPair:
    Vert* v1
    Vert* v2
ctypedef VertPair* VertPair_pntr

cdef class Mesh:
    cdef vector[Vert] verts
    cdef vector[Face] faces
    cdef vector[Edge] edges
    cdef vector[HalfEdge] halfs

    # cdef public list verts, halfs, edges, faces
    cdef ve
    cdef HalfEdge *boundary_start
    cdef public dict cid_to_vert
    cdef int __v_id, __e_id, __f_id

    # Constructor functions.
    cdef Vert* __vert(self, double x, double y, HalfEdge* he=*)
    cdef Edge* __edge(self, HalfEdge* he=*)
    cdef Face* __face(self, HalfEdge* he=*)
    cdef HalfEdge* __half(self, HalfEdge* twin=*, HalfEdge* next=*, Vert* vert=*, Edge* edge=*, Face* face=*)

    # cdef HalfEdge __half(self, twin=*, next=*, vert=*, edge=*, face=*)
    # cdef HalfEdge __half(self, HalfEdge* twin=*, HalfEdge* next=*, Vert* vert=*, Edge* edge=*, Face* face=*)


    # Public functions.
    cdef void edge_flip(self, Edge* e)
    cdef Vert* edge_split(self, Edge* e)
    cdef void flip_if_better(self, Edge* e)
    cdef void smooth(self)
    # cdef list adapt(self, double max_edge_length)

    # Query
    cdef vert_three_tuple face_verts(self, Face* face)
    cdef half_three_tuple face_halfs(self, Face* face)
    cdef tuple face_center(self, Face* face)
    # cdef list boundary(self)
    cdef bint is_boundary_edge(self, Edge* e)
    cdef bint is_boundary_vert(self, Vert* v)
    cdef vector[Vert*]& vert_neighbors(self, Vert* v)
    cdef vector[Edge*]& edge_neighbors(self, Vert* v)
    cdef Vert_pair edge_verts(self, Edge* e)
    cdef double edge_length(self, Edge* e)
