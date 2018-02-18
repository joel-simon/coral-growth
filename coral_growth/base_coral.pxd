from cymesh.mesh cimport Mesh
from cymesh.structures cimport Vert

cdef class BaseCoral:
    cdef public Mesh mesh
    cdef public object network, params, morphogens, traits, collisionManager
    cdef public int n_polyps, n_signals, n_memory, max_polyps, n_morphogens, \
                    morphogen_thresholds, n_inputs, n_outputs, age
    cdef public double light, collection, energy, volume, max_face_area, C

    cdef public double[:,::1] polyp_inputs, polyp_pos, polyp_pos_next, polyp_normal, polyp_signals
    cdef public double[:] polyp_flow, polyp_gravity, polyp_collection, polyp_light,\
                          signal_decay, polyp_energy, buffer
    cdef public unsigned char[:] polyp_collided

    cpdef void calculateEnergy(self) except *
    cpdef void createPolyp(self, Vert vert) except *
    cpdef void polypDivision(self) except *

    cpdef void applyHeightScale(self) except *
    cpdef void diffuse(self) except *
    cpdef void createPolypInputs(self) except *
    cpdef void growPolyps(self) except *
    cpdef void decaySignals(self) except *
    cpdef void export(self, str path) except *