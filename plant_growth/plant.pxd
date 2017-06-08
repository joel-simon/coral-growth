from plant_growth.world cimport World

cdef class Plant:
    cdef public object network, polygon, mesh
    cdef public double efficiency, energy_usage, volume, water, light, total_flowering, max_age
    cdef public bint alive
    cdef public int age, n_cells, cell_head, cell_tail, num_flowers
    cdef public double[:] cell_x, cell_y, cell_water, cell_light, cell_energy, cell_curvature, cell_next_x, cell_next_y
    cdef public int[:] cell_next, cell_prev, cell_flower, cell_order, cell_alive

    cdef World world
    cdef int[:, :] grid
    cdef public double[:,:] cell_norm
    cdef list cell_inputs, open_ids

    cpdef void update_attributes(self) except *
    cpdef void grow(self)
    cdef list split_links(self)
    cdef void order_cells(self)

    cpdef void create_circle(self, double x, double y, double r, int n)

    cdef void _insert_before(self, int node, int new_node)
    cdef void _append(self, int new_node)
    cdef int _create_cell(self, double x, double y, before=*)
    # cdef void _destroy_cell(self, int cid)
    cdef void _cell_input(self, int cid)
    cdef list _output(self)
    # cdef bint _valid_growth(self, double x_test, double y_test, double x_prev,
                                  # double y_prev, double x_next, double y_next)
    cdef bint _valid_growth(self, int cid, double x, double y)

    cdef object _make_polygon(self)
    cpdef void _calculate_mesh(self)
    cdef void _calculate_norms(self)
    cdef void _calculate_light(self) except *
    cdef void _calculate_water(self)
    cdef void _calculate_curvature(self)
    cdef void _calculate_flowers(self)
