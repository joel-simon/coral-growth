cdef class Vert:
    cdef public int id
    cdef public double x, y, x0, y0, deform_x, deform_y, prev_x, prev_y, accel_x, accel_y
    cdef public bint fixed
    cdef public HalfEdge he
    cdef public object cid

cdef class Edge:
    cdef public int id
    cdef public double target, strain
    cdef public HalfEdge he

cdef class Face:
    cdef public int id
    cdef public HalfEdge he

cdef class HalfEdge(object):
    cdef public HalfEdge twin, next
    cdef public Vert vert
    cdef public Edge edge
    cdef public Face face

# cdef struct Vert:
#     int id
#     double x, y, x0, y0, deform_x, deform_y, prev_x, prev_y, accel_x, accel_y
#     bint fixed
#     HalfEdge* he
#     object cid

# cdef struct HalfEdge:
#     HalfEdge *twin
#     HalfEdge *next
#     Vert *vert
#     Edge *edge
#     Face *face

cdef class Mesh:
    # cdef public vector[HalfEdge] halfs
    cdef public list verts, halfs, edges, faces
    cdef public HalfEdge boundary_start
    cdef public dict cid_to_vert
    cdef int __v_id, __e_id, __f_id

    # Constructor functions.
    cdef Vert __vert(self, double x, double y, he=*)
    cdef Edge __edge(self, he=*)
    cdef Face __face(self, he=*)
    # cdef HalfEdge __half(self, twin=*, next=*, vert=*, edge=*, face=*)
    # cdef HalfEdge __half(self, HalfEdge* twin=*, HalfEdge* next=*, Vert* vert=*, Edge* edge=*, Face* face=*)
    cdef HalfEdge __half(self, HalfEdge twin=*, HalfEdge next=*, Vert vert=*, Edge edge=*, Face face=*)

    # Public functions.
    cpdef void edge_flip(self, Edge edge)
    cpdef Vert edge_split(self, Edge edge)
    cpdef void flip_if_better(self, Edge edge)
    cpdef void smooth(self)
    cpdef list adapt(self, double max_edge_length)

    # Query
    cpdef list face_verts(self, Face face)
    cpdef list face_halfs(self, Face face)
    cpdef tuple face_center(self, Face face)
    cpdef list boundary(self)
    cpdef bint is_boundary_edge(self, Edge e)
    cpdef bint is_boundary_vert(self, Vert v)
    cpdef list vert_neighbors(self, Vert v)
    cpdef list edge_neighbors(self, Vert v)
    cpdef tuple edge_verts(self, Edge e)
    cpdef double edge_length(self, Edge e)
