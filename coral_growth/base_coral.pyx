# cython: boundscheck=False
# cython: wraparound=True
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True
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

cdef class BaseCoral:
    cpdef void calculateEnergy(self) except *:
        cdef int i
        cdef double light_amount = self.params.light_amount
        self.light = 0
        self.collection = 0
        self.energy = 0
        for i in range(self.n_polyps):
            self.light += self.polyp_light[i]
            self.collection += self.polyp_collection[i]
            self.polyp_energy[i] = light_amount * self.polyp_light[i] + \
                                   (1-light_amount)*self.polyp_collection[i]

        self.energy = light_amount*self.light + (1-light_amount)*self.collection

    cpdef void calculateGravity(self) except *:
        cdef int i = 0
        cdef double[:] down = np.array([0, -1.0, 0])
        for i in range(self.n_polyps):
            self.polyp_gravity[i] = vangle(down, self.polyp_normal[i]) / M_PI

    cpdef void createPolyp(self, Vert vert) except *:
        if self.n_polyps == self.max_polyps:
            return

        cdef Vert vert_n
        cdef int i, n, idx

        idx = self.n_polyps
        self.n_polyps += 1
        vert.data['polyp'] = idx
        self.polyp_pos[idx, :] = vert.p
        vert.normal = self.polyp_normal[idx]
        vert.p = self.polyp_pos[idx]
        self.polyp_verts[idx] = vert

        # n = 0
        # for vert_n in vert.neighbors():
        #     if self.polyp_signals[vert_n.id, 0] == 0.0:
        #         for i in range(self.n_signals):
        #             self.polyp_signals[idx, i] += self.polyp_signals[vert_n.id, i]
        #     n += 1

        # for i in range(self.n_signals):
        #     self.polyp_signals[idx, i] /= n

        self.collisionManager.newVert(vert.id)

        assert vert.id == idx

    cpdef void polypDivision(self) except *:
        """ Update the mesh and create new polyps.
        """
        cdef Face face
        cdef Vert vert
        for face in self.mesh.faces:
            if face.area() > self.max_face_area:
                split(self.mesh, face, max_vertices=self.max_polyps)
                if self.n_polyps == self.max_polyps:
                    break

        for vert in self.mesh.verts:
            if 'polyp' not in vert.data:
                self.createPolyp(vert)

    cpdef void applyHeightScale(self) except *:
        cdef int i
        cdef double scale
        cdef double bott = self.params.gradient_bottom
        cdef double height = self.params.gradient_height
        if height == 0:
            return
        for i in range(self.n_polyps):
            scale = bott + min(1, self.polyp_pos[i, 1] / height) * (1 - bott)
            self.polyp_collection[i] *= scale
            self.polyp_light[i] *= scale

    cpdef void diffuse(self) except *:
        """ Diffuse energy and signals across surface.
        """
        cdef int i, mi, steps
        cdef float nsum
        cdef Vert vert
        cdef list neighbors = [ vert.neighbors() for vert in self.mesh.verts ]

        for _ in range(self.traits['energy_diffuse_steps']):
            for i in range(self.n_polyps):
                nsum = 0
                for vert in neighbors[i]:
                    nsum += self.polyp_energy[vert.id]
                self.buffer[i] = .5*self.polyp_energy[i] + .5*nsum / len(neighbors[i])

            for i in range(self.n_polyps):
                self.polyp_energy[i] = self.buffer[i]

        for mi in range(self.n_signals):
            steps = self.traits['signal_diffuse_steps%i'%mi]
            for _ in range(steps):
                for i in range(self.n_polyps):
                    nsum = 0
                    for vert in neighbors[i]:
                        nsum += self.polyp_signals[vert.id, mi]
                    self.buffer[i] = .5*self.polyp_signals[i, mi] + .5*nsum / len(neighbors[i])

                for i in range(self.n_polyps):
                    self.polyp_signals[i, mi] = self.buffer[i]

    cpdef void decaySignals(self) except *:
        cdef int i, si
        for i in range(self.n_polyps):
            for si in range(self.n_signals):
                self.polyp_signals[i, si] = min(1.0, self.polyp_signals[i, si])
                self.polyp_signals[i, si] *= (1 - self.signal_decay[si])

    cpdef void createPolypInputs(self) except *:
        """ Map polyp stats to nerual input in [-1, 1] range. """
        cdef int input_idx, i, mi, mbin
        cdef int morphogen_thresholds = self.params.morphogen_thresholds
        cdef double[:,:] morphogensU = self.morphogens.U
        cdef bint use_polar_direction = self.params.use_polar_direction
        cdef double signal_sum, azimuthal_angle, polar_angle

        self.polyp_inputs[:, :] = -1

        for i in range(self.n_polyps):
            self.polyp_inputs[i, 0] = (self.polyp_light[i] * 2) - 1
            self.polyp_inputs[i, 1] = (self.polyp_collection[i] * 2) - 1
            self.polyp_inputs[i, 2] = (self.polyp_energy[i] * 2) - 1
            self.polyp_inputs[i, 3] = self.polyp_gravity[i]
            self.polyp_inputs[i, 4] = self.mesh.verts[i].curvature
            # assert (not np.isnan(self.mesh.verts[i].curvature)), 'nan curv'
            input_idx = 5

            # Morphogens
            for mi in range(self.n_morphogens):
                mbin = <int>(floor(morphogensU[mi, i] * morphogen_thresholds))
                mbin = min(morphogen_thresholds - 1, mbin)

                if mbin > 0:
                    self.polyp_inputs[i, input_idx + (mbin-1)] = 1

                input_idx += (morphogen_thresholds-1)

            # Signals
            for mi in range(self.n_signals):
                self.polyp_inputs[i, input_idx] = self.polyp_signals[i, mi] > 0.5
                input_idx += 1

            # # Memory
            # for mi in range(self.n_memory):
            #     self.polyp_inputs[i, input_idx] = self.polyp_signals[i, mi] > 0.5
            #     input_idx += 1

            if use_polar_direction:
                azimuthal_angle = atan(self.polyp_normal[i, 1] / self.polyp_normal[i, 0])
                polar_angle = acos(self.polyp_normal[i, 2])
                self.polyp_inputs[i, input_idx] = cos(azimuthal_angle)
                self.polyp_inputs[i, input_idx+1] = sin(azimuthal_angle)
                self.polyp_inputs[i, input_idx+2] = cos(polar_angle)
                self.polyp_inputs[i, input_idx+3] = sin(polar_angle)
                input_idx += 4

            self.polyp_inputs[i, input_idx] = 1 # Bias Bit

            assert input_idx == (self.n_inputs-1)

    cpdef void growPolyps(self) except *:
        cdef int i, out_idx, mi
        cdef double growth
        cdef object output
        cdef double[:,:] morphogensV = self.morphogens.V

        self.createPolypInputs()

        # Boost library for neural network wants numpy array or list.
        cdef object inputs = np.asarray(self.polyp_inputs)

        for i in range(self.n_polyps):

            # Compute feed-forward network results.
            self.network.Flush()
            self.network.Input(inputs[i])
            for _ in range(self.net_depth):
                self.network.ActivateFast()
            output = self.network.Output()

            # Move in normal direction by growth amount.
            growth = min(output[0], self.polyp_energy[i]) * self.C
            self.polyp_pos_next[i, 0] = self.polyp_pos[i, 0] + growth * self.polyp_normal[i, 0]
            self.polyp_pos_next[i, 1] = self.polyp_pos[i, 1] + growth * self.polyp_normal[i, 1]
            self.polyp_pos_next[i, 2] = self.polyp_pos[i, 2] + growth * self.polyp_normal[i, 2]
            self.polyp_pos_next[i, 1] = max(0, self.polyp_pos_next[i, 1]) # Can't go below ground

            # Morphogens.
            out_idx = 1
            for mi in range(self.n_morphogens):
                if output[out_idx] > 0.5:
                    morphogensV[mi, i] = 1.0
                out_idx += 1

            # Signals
            for mi in range(self.n_signals):
                if output[out_idx] > 0.5:
                    self.polyp_signals[i, mi] = 1.0
                out_idx += 1

        for i in range(self.n_polyps):
            self.polyp_collided[i] = self.collisionManager.attemptVertUpdate(i, self.polyp_pos_next[i])

    cpdef void export(self, str path) except *:
        """ Export the coral to .coral.obj file
            A .coral.obj file is a 3d mesh with polyp specific information.
            it is a compatable superset of the .obj file format.
            In addition to the content of a .obj file a .coral.obj file has:

            1. A header row that begins with '#coral' that lists space
                deliminated polyp attributes
            2. A line that begins with 'c' for each vert that contains values
                for each attribute. Ordered the same as the vertices.
        """
        cdef int i
        out = open(path, 'w+')
        cdef list header = []

        for i in range(self.n_morphogens):
            header.append( 'mu_%i' % i )
        for i in range(self.n_signals):
            header.append( 'sig_%i' % i )

        header.extend([ 'light', 'collection', 'energy', 'curvature' ])
        out.write('#Exported from coral_growth\n')
        out.write('#attr light:%f collection:%f energy:%f\n' % \
                                     (self.light, self.collection, self.energy))
        out.write('#coral ' + ' '.join(header) + '\n')

        p_attributes = [None] * self.n_polyps
        for i in range(self.n_polyps):
            p_attributes[i] = []

            for j in range(self.n_morphogens):
                p_attributes[i].append(self.morphogens.U[j, i])

            p_attributes[i].extend(self.polyp_signals[i])
            p_attributes[i].extend([ self.polyp_light[i],
                                        self.polyp_collection[i],
                                        self.polyp_energy[i],
                                        self.polyp_verts[i].curvature ])

            assert len(p_attributes[i]) == len(header)

        # Write vertices (position and color)
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

        # if self.save_flow_data:
        #     f = open(path+'.flow_grid.p', 'wb')
        #     pickle.dump((self.voxel_length, self.flow_data), f)
        #     f.close()