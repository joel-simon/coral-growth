from cymem.cymem cimport Pool
from plant_growth.plant cimport Plant
from plant_growth.mesh cimport Face
from plant_growth.tri_hash_3d cimport TriHash3D
from plant_growth.tri_hash_2d cimport TriHash2D

ctypedef unsigned int uint

cdef inline bint pnt_in_tri(double p[2], double p0[2], double p1[2], double p2[2]):
    # https://stackoverflow.com/questions/2049582/how-to-determine-if-a-point-is-in-a-2d-triangle
    # http://jsfiddle.net/PerroAZUL/zdaY8/1/
    cdef double A = 1/2 * (-p1[1] * p2[0] + p0[1] * (-p1[0] + p2[0]) + p0[0] * (p1[1] - p2[1]) + p1[0] * p2[1])
    cdef int sign = -1 if A < 0 else 1
    cdef double s = (p0[1] * p2[0] - p0[0] * p2[1] + (p2[1] - p0[1]) * p[0] + (p0[0] - p2[0]) * p[1]) * sign
    cdef double t = (p0[0] * p1[1] - p0[1] * p1[0] + (p0[1] - p1[1]) * p[0] + (p1[0] - p0[0]) * p[1]) * sign
    return s > 0 and t > 0 and (s + t) < 2 * A * sign

cdef class World:
    cdef Pool mem
    cdef public int soil_height, max_plants, use_physics, step
    cdef uint max_face_neighbors
    cdef public list plants
    cdef void **face_neighbors
    cdef public TriHash3D th3d
    cdef public TriHash2D th2d
    cdef public bint verbose

    cpdef int add_plant(self, str obj_path, object network, double efficiency) except -1
    cpdef void simulation_step(self) except *

    cdef void add_plant_to_hash(self, Plant plant) except *
    cdef void restrict_growth(self) except *
    cdef int valid_face_position(self, Plant plant, Face *faceid) except -1
    cdef void calculate_light(self, Plant plant) except *
