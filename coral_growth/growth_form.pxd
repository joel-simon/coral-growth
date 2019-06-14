from cymesh.mesh cimport Mesh
from cymesh.structures cimport Vert

cdef class GrowthForm:
    cdef public Mesh mesh
    cdef public object network, params, morphogens, traits, collisionManager
    cdef public list attributes
    cdef public int n_nodes, n_signals, n_inputs, n_outputs, max_nodes, age, \
                    n_morphogens, morphogen_thresholds, n_attributes
    cdef public double energy, volume, max_face_area, C, max_growth
    cdef public double[:] node_gravity, signal_decay, node_energy, buffer
    cdef public int[:, ::1] node_memory
    cdef public double[:,::1] node_inputs, node_pos, node_pos_next, node_normal, node_signals, buffer3

    cpdef void step(self) except *
    cpdef void grow(self) except *
    cpdef void calculateAttributes(self) except *
    cpdef void calculateEnergy(self) except *
    cpdef void calculateGravity(self) except *
    cpdef void createNode(self, Vert vert) except *
    cpdef void subdivision(self) except *
    cpdef void diffuse(self) except *
    cpdef void createNodeInputs(self) except *
    cpdef void smoothSharp(self, n=*) except *
    # cpdef void decaySignals(self) except *
    cpdef void export(self, str path) except *