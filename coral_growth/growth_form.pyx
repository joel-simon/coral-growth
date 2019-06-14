# cython: boundscheck=False
# cython: wraparound=True
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True
# cython: profile=True

from __future__ import division, print_function
from libc.math cimport floor, atan, acos, cos, sin, M_PI
import numpy as np
cimport numpy as np

from coral_growth.modules.morphogens import Morphogens
from coral_growth.modules.collisions import MeshCollisionManager

from cymesh.vector3D cimport inormalized, vadd, vsub, vmultf, vset, dot, vangle
from cymesh.mesh cimport Mesh
from cymesh.structures cimport Vert, Face

from cymesh.subdivision.sqrt3 import split
from cymesh.operators.relax import relax_mesh

cdef class GrowthForm:
    def __init__(self, attributes, obj_path, network, net_depth, traits, params):
        assert type(attributes) == list
        self.params = params
        self.network = network
        self.mesh = Mesh.from_obj(obj_path)
        self.attributes = attributes
        self.n_attributes = len(attributes)
        self.n_morphogens = params.n_morphogens
        self.n_signals = params.n_signals
        self.n_memory = params.n_memory
        self.net_depth = net_depth
        self.C = params.C
        self.max_nodes = params.max_nodes
        self.max_growth = params.max_growth
        self.morphogens = Morphogens(self, traits, params.n_morphogens)

        # Some parameters are evolved traits.
        self.traits = traits
        # self.signal_decay = np.array([ traits['signal_decay%i'%i] \
        #                                for i in range(params.n_signals) ])

        # Constants for simulation dependent on start mesh.
        self.target_edge_len = np.mean([e.length() for e in self.mesh.edges])
        self.node_size = self.target_edge_len * 0.5
        self.max_edge_len = self.target_edge_len * 1.3
        self.max_face_area = np.mean([f.area() for f in self.mesh.faces]) * params.max_face_growth
        self.voxel_length = self.target_edge_len

        # Data
        n_inputs, n_outputs = self.calculate_inouts(params)
        self.n_inputs = n_inputs
        self.n_outputs = n_outputs

        self.age = 0
        self.n_nodes = 0
        self.volume = 0
        self.node_inputs = np.zeros((self.max_nodes, self.n_inputs))
        self.node_verts = [None] * self.max_nodes
        self.node_energy = np.ones(self.max_nodes)
        self.node_pos = np.zeros((self.max_nodes, 3))
        self.node_pos_next = np.zeros((self.max_nodes, 3))
        self.node_normal = np.zeros((self.max_nodes, 3))
        self.node_gravity = np.zeros(self.max_nodes)

        self.node_signals = np.zeros((self.max_nodes, self.params.n_signals))
        self.node_memory = np.zeros((self.max_nodes, self.params.n_signals), dtype='int32')
        self.buffer = np.zeros((self.max_nodes)) # For tmp calculation values.
        self.buffer3 = np.zeros((self.max_nodes, 3))
        self.node_attributes = np.zeros((self.max_nodes, self.n_attributes))

        self.collisionManager = MeshCollisionManager(self.mesh, self.node_pos,\
                                                     self.node_normal, self.node_size)
        for vert in self.mesh.verts:
            self.createNode(vert)
        self.calculateAttributes()

    @classmethod
    def calculate_inouts(cls, params):
        n_inputs = 4 # energy, gravity, curvature, extra-bias-bit.
        n_inputs += params.n_signals * (params.signal_thresholds-1)
        n_inputs += params.n_morphogens * (params.morphogen_thresholds-1)
        n_inputs += (4 * params.use_polar_direction)
        n_inputs += params.n_memory

        n_outputs = 1 # Growth.
        n_outputs += params.n_signals + params.n_morphogens + params.n_memory

        return n_inputs, n_outputs

    cpdef void step(self) except *:
        self.createNodeInputs()
        self.grow()
        for i in range(self.n_nodes):
            self.collisionManager.attemptVertUpdate(self.mesh.verts[i], self.node_pos_next[i])
        self.smoothSharp()
        relax_mesh(self.mesh)
        self.subdivision() # Divide mesh and create new nodes.
        self.calculateAttributes()
        self.age += 1

    cpdef void calculateAttributes(self) except *:
        self.mesh.calculateNormals()
        self.mesh.calculateDefect()
        self.mesh.calculateCurvature()
        self.calculateEnergy()
        self.volume = self.mesh.volume()
        self.calculateGravity()
        # self.decaySignals()
        self.morphogens.update(self.params.morphogen_steps)
        self.diffuse()

    cpdef void smoothSharp(self, n=0.5) except *:
        cdef Vert vert, vert_neighbor
        cdef double max_defect = self.params.max_defect
        cdef list neighbors
        cdef double m = 1-n
        self.mesh.calculateDefect()
        self.buffer3[:, :] = 0

        # For pointy nodes get the average position of neighbors.
        for vert in self.mesh.verts:
            if abs(vert.defect) > max_defect:
                neighbors = vert.neighbors()
                for vert_neighbor in neighbors:
                    vadd(self.buffer3[vert.id], self.buffer3[vert.id], vert_neighbor.p)

                vmultf(self.buffer3[vert.id], self.buffer3[vert.id], 1.0/len(neighbors))

        # Move to average.
        for vert in self.mesh.verts:
            if abs(vert.defect) > max_defect:
                vert.p[0] = m*vert.p[0] + n*self.buffer3[vert.id, 0]
                vert.p[1] = m*vert.p[1] + n*self.buffer3[vert.id, 1]
                vert.p[2] = m*vert.p[2] + n*self.buffer3[vert.id, 2]

    cpdef void calculateEnergy(self) except *:
        """ Calculate how much each node is allowed to grow. If sub-classes do
            not override this method then all nodes can grow at 100%.
        """
        pass

    cpdef void calculateGravity(self) except *:
        cdef int i = 0
        cdef double[:] down = np.array([0, -1.0, 0])
        for i in range(self.n_nodes):
            self.node_gravity[i] = vangle(down, self.node_normal[i]) / M_PI

    cpdef void createNode(self, Vert vert) except *:
        if self.n_nodes == self.max_nodes:
            return

        cdef Vert vert_n
        cdef int i
        cdef int idx = self.n_nodes
        self.n_nodes += 1
        vert.data['node'] = idx
        self.node_pos[idx, :] = vert.p
        vert.normal = self.node_normal[idx]
        vert.p = self.node_pos[idx]
        self.node_verts[idx] = vert
        self.collisionManager.newVert(vert)

        cdef int n = 0
        for vert_n in vert.neighbors():
            for i in range(self.n_memory):
                self.node_memory[idx, i] += self.node_memory[vert_n.id, i]
            # for i in range(self.n_signals):
            #     self.node_signals[idx, i] += self.node_signals[vert_n.id, i]
            n += 1

        # Signals are average of neighbors.
        # for i in range(self.n_signals):
        #     self.node_signals[idx, i] /= n

        # Take Memory if majority of neighbours have it.
        for i in range(self.n_memory):
            self.node_memory[idx, i] = 1 if self.node_memory[idx, i] > n/2 else 0

        assert vert.id == idx

    cpdef void subdivision(self) except *:
        """ Adaptively subdivide the mesh and create new nodes.
        """
        cdef Face face
        cdef Vert vert
        for face in self.mesh.faces:
            if face.area() > self.max_face_area:
                split(self.mesh, face, max_vertices=self.max_nodes)
                if self.n_nodes == self.max_nodes:
                    break

        for vert in self.mesh.verts:
            if 'node' not in vert.data:
                self.createNode(vert)

    cpdef void diffuse(self) except *:
        """ Diffuse energy and signals across surface.
        """
        cdef int i, mi, steps
        cdef float nsum
        cdef Vert vert
        cdef list neighbors = [ vert.neighbors() for vert in self.mesh.verts ]

        for _ in range(self.traits['energy_diffuse_steps']):
            for i in range(self.n_nodes):
                nsum = 0
                for vert in neighbors[i]:
                    nsum += self.node_energy[vert.id]
                self.buffer[i] = .5*self.node_energy[i] + .5*nsum / len(neighbors[i])

            for i in range(self.n_nodes):
                self.node_energy[i] = self.buffer[i]

        for mi in range(self.n_signals):
            steps = self.traits['signal_diffuse_steps%i'%mi]
            for _ in range(steps):
                for i in range(self.n_nodes):
                    nsum = 0
                    for vert in neighbors[i]:
                        nsum += self.node_signals[vert.id, mi]
                    self.buffer[i] = .5*self.node_signals[i, mi] + .5*nsum / len(neighbors[i])

                for i in range(self.n_nodes):
                    self.node_signals[i, mi] = self.buffer[i]

    # cpdef void decaySignals(self) except *:
    #     cdef int i, si
    #     for i in range(self.n_nodes):
    #         for si in range(self.n_signals):
    #             self.node_signals[i, si] = min(1.0, self.node_signals[i, si])
    #             self.node_signals[i, si] *= (1 - self.signal_decay[si])

    cpdef void createNodeInputs(self) except *:
        """ Map node stats to neural input in [-1, 1] range. """
        cdef int input_idx, i, j, mi, mbin
        cdef int morphogen_thresholds = self.params.morphogen_thresholds
        cdef int signal_thresholds = self.params.signal_thresholds
        cdef double[:,:] morphogensU = self.morphogens.U
        cdef bint use_polar_direction = self.params.use_polar_direction
        cdef double signal_sum, azimuthal_angle, polar_angle

        self.node_inputs[:, :] = -1

        for i in range(self.n_nodes):
            self.node_inputs[i, 0] = (self.node_energy[i] * 2) - 1
            self.node_inputs[i, 1] = self.node_gravity[i]
            self.node_inputs[i, 2] = self.mesh.verts[i].curvature
            input_idx = 3

            for j in range(self.n_attributes):
                self.node_inputs[i, input_idx] = self.node_attributes[i, j]
                input_idx += 1

            # Morphogens.
            for mi in range(self.n_morphogens):
                mbin = <int>(floor(morphogensU[mi, i] * morphogen_thresholds))
                mbin = min(morphogen_thresholds - 1, mbin)
                if mbin > 0:
                    self.node_inputs[i, input_idx + (mbin-1)] = 1
                input_idx += (morphogen_thresholds-1)

            # Signals.
            for mi in range(self.n_signals):
                mbin = <int>(floor(self.node_signals[i, mi] * signal_thresholds))
                mbin = min(signal_thresholds - 1, mbin)
                if mbin > 0:
                    self.node_inputs[i, input_idx + (mbin-1)] = 1
                input_idx += (signal_thresholds-1)

            # Memory.
            for mi in range(self.n_memory):
                self.node_inputs[i, input_idx] = -1.0 + self.node_memory[i, mi] * 2.0
                input_idx += 1

            if use_polar_direction:
                azimuthal_angle = atan(self.node_normal[i, 1] / self.node_normal[i, 0])
                polar_angle = acos(self.node_normal[i, 2])
                self.node_inputs[i, input_idx] = cos(azimuthal_angle)
                self.node_inputs[i, input_idx+1] = sin(azimuthal_angle)
                self.node_inputs[i, input_idx+2] = cos(polar_angle)
                self.node_inputs[i, input_idx+3] = sin(polar_angle)
                input_idx += 4

            self.node_inputs[i, input_idx] = 1 # Bias Bit
            input_idx += 1

            assert input_idx == self.n_inputs, (input_idx, self.n_inputs)

    cpdef void grow(self) except *:
        cdef int i, out_idx, mi, n
        cdef Vert vert
        cdef double growth
        cdef object output
        cdef double[:,:] morphogensV = self.morphogens.V

        # Boost library for neural network wants numpy array or list.
        cdef object inputs = np.asarray(self.node_inputs)

        for i in range(self.n_nodes):

            # Compute feed-forward network results.
            self.network.Flush()
            self.network.Input(inputs[i])
            for _ in range(self.net_depth):
                self.network.ActivateFast()
            output = self.network.Output()

            # Move in normal direction by growth amount.
            growth = min(output[0], self.node_energy[i]) * self.C
            growth = min(growth, self.max_growth)
            self.buffer[i] = growth

            # Morphogens.
            out_idx = 1
            for mi in range(self.n_morphogens):
                if output[out_idx] > 0.5:
                    morphogensV[mi, i] = 1.0
                out_idx += 1

            # Signals
            for mi in range(self.n_signals):
                self.node_signals[i, mi] = <int>(output[out_idx] > 0.5)
                out_idx += 1

            # Memory
            for mi in range(self.n_memory):
                if output[out_idx] > 0.75:
                    self.node_memory[i, mi] = 1
                out_idx += 1

        for i in range(self.n_nodes):
            growth = 0.0
            n = 0

            for vert in self.mesh.verts[i].neighbors():
                growth += self.buffer[vert.id]
                n += 1

            growth = ((growth/n) + self.buffer[i]) * 0.5

            self.node_pos_next[i, 0] = self.node_pos[i, 0] + growth * self.node_normal[i, 0]
            self.node_pos_next[i, 1] = self.node_pos[i, 1] + growth * self.node_normal[i, 1]
            self.node_pos_next[i, 2] = self.node_pos[i, 2] + growth * self.node_normal[i, 2]

        if self.params.has_ground: # Can't go below ground.
            for i in range(self.n_nodes):
                self.node_pos_next[i, 1] = max(0, self.node_pos_next[i, 1])

    cpdef void export(self, str path) except *:
        """ Export the coral to .coral.obj file
            A .coral.obj file is a 3d mesh with node specific information.
            it is a compatable superset of the .obj file format.
            In addition to the content of a .obj file a .coral.obj file has:

            1. A header row that begins with '#coral' that lists space
                deliminated node attributes
            2. A line that begins with 'c' for each vert that contains values
                for each attribute. Ordered the same as the vertices.
        """
        cdef int i, j
        out = open(path, 'w+')
        cdef list header = [a for a in self.attributes]
        header.extend([ 'energy', 'curvature', 'gravity' ])
        for i in range(self.n_morphogens):
            header.append( 'mu_%i' % i )
        for i in range(self.n_signals):
            header.append( 'sig_%i' % i )
        for i in range(self.n_memory):
            header.append( 'memory_%i' % i )

        out.write('#Exported from growth_forms\n')
        out.write('#form ' + ' '.join(header) + '\n')

        p_attributes = [None] * self.n_nodes

        for i in range(self.n_nodes):
            p_attributes[i] = []

            for j in range(self.n_attributes):
                p_attributes[i].append(self.node_attributes[i, j])

            p_attributes[i].append( self.node_energy[i] )
            p_attributes[i].append( self.node_verts[i].curvature )
            p_attributes[i].append( self.node_gravity[i] )

            for j in range(self.n_morphogens):
                p_attributes[i].append(self.morphogens.U[j, i])

            for j in range(self.n_signals):
                p_attributes[i].append(self.node_signals[i, j])

            for j in range(self.n_memory):
                p_attributes[i].append(self.node_memory[i, j])

        assert len(p_attributes[0]) == len(header)

        # Write vertices (position and color).
        for i, vert in enumerate(self.mesh.verts):
            r, g, b = p_attributes[i][:3]
            out.write('v %f %f %f %f %f %f\n' % (tuple(vert.p)+(r, g, b)))
        out.write('\n')

        # Write coral data lines.
        for attributes in p_attributes:
            out.write('c ' + ' '.join(map(str, attributes)) + '\n')
        out.write('\n')

        # Write Faces
        for face in self.mesh.faces:
            v1, v2, v3 = face.vertices()
            out.write('f %i %i %i\n' % (v1.id+1, v2.id+1, v3.id+1))
        out.close()
