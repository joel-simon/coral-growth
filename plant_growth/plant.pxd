from plant_growth.vec2D cimport Vec2D

cdef class Plant:
    cdef public object world, network, polygon, mesh
    cdef public double efficiency, energy, volume, water, light, total_flowering, consumption
    cdef public bint alive
    cdef public int age, n_cells, cell_head, cell_tail, num_flowers
    cdef public double[:] cell_water, cell_light, cell_curvature
    cdef public int[:] cell_next, cell_prev, cell_flower, ordered_cell
    cdef public object[:] cell_p
    cdef int[:, :] grid
    cdef double[:,:] cell_norm
    cdef list cell_inputs

    cpdef void update_attributes(self)
    cpdef void grow(self)
    cpdef void create_circle(self, double x, double y, double r, int n)

    cdef void _insert_before(self, int node, int new_node)
    cdef void _append(self, int new_node)
    cdef int _create_cell(self, double x, double y, before=*)
    cdef void _cell_input(self, int cid)
    cdef void _order_cells(self)
    cdef list _output(self)
    cdef bint _valid_growth(self, Vec2D v_cell, Vec2D v_prev, Vec2D v_next)
    cdef object _make_polygon(self)
    cdef void _calculate_mesh(self)
    cdef void _calculate_norms(self)
    cdef void _split_links(self)
    cdef void _calculate_collision_grid(self)
    cdef void _calculate_light(self)
    cdef void _calculate_water(self)
    cdef void _calculate_curvature(self)
    cdef void _calculate_flowers(self)
