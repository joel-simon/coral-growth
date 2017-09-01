from plant_growth.world cimport World
from cymem.cymem cimport Pool
from plant_growth.mesh cimport Mesh, Node, Vert, Face, Edge

cdef struct Cell:
    int id
    Vert *vert
    bint alive
    double next_p[3]
    double rotated[3]
    double flower
    double light
    bint water
    double curvature
    unsigned int ctype

cdef class Plant:
    cdef Pool mem
    cdef public Mesh mesh
    cdef Mesh mesh0
    cdef public object network
    cdef public double efficiency, energy, volume, light, flowers, water
    cdef double growth_scalar

    cdef public bint alive
    cdef public int age, n_cells, max_cells, cell_types

    cdef Cell *cells
    cdef World world
    cdef list cell_inputs

    cdef void update_attributes(self) except *
    cdef void grow(self) except *

    cdef void calculate_energy(self)
    cpdef double seed_spread(self)  except -1

    cdef int create_cell(self, Vert *vert, Cell *p1, Cell *p2) except -1
    cdef list cell_output(self, Cell *cell)
    cdef void cell_division(self)
    cdef double _calculate_energy_transfer(self) except *
    cdef void _calculate_light(self) except *
