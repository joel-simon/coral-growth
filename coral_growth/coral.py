# cython: boundscheck=False
# cython: wraparound=True
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True

from __future__ import print_function
from math import isnan, sqrt, floor
import numpy as np
from pykdtree.kdtree import KDTree

from cymesh.mesh import Mesh
from cymesh.subdivision.sqrt3 import split
# from cymesh.operators.relax import relax_mesh, relax_mesh_cotangent, relax_vert_cotangent

from coral_growth.grow_polyps import grow_polyps
from coral_growth.modules import light, gravity
from coral_growth.modules.morphogens import Morphogens
from coral_growth.modules.collisions import MeshCollisionManager

def normed(x):
    return x / np.linalg.norm(x)

class Coral(object):
    num_inputs = 4 # [light, curvature, gravity, extra-bias-bit?]
    num_outputs = 1

    def __init__(self, obj_path, network, morphogens_params, params):
        self.mesh = Mesh.from_obj(obj_path)
        self.network = network

        self.volume = 0
        self.total_gametes = 0

        self.growth_scalar = params['growth_scalar']
        self.max_polyps = params['max_polyps']
        self.moprhogen_steps = params['morphogen_steps']
        self.n_memory = params['polyp_memory']
        self.morph_thresholds = params['morph_thresholds']
        self.C = params.get("C", 100)
        self.spring_strength = params.get("spring_strength", .3)
        self.morphogens = Morphogens(self, morphogens_params)

        mean_face = np.mean([f.area() for f in self.mesh.faces])
        self.target_edge_len = np.mean([e.length() for e in self.mesh.edges])
        self.max_face_area = mean_face * params['max_face_growth']

        self.max_edge_len = self.target_edge_len * params['max_face_growth']
        block_size = sqrt(4 * self.max_face_area / sqrt(3))
        # block_size = self.max_edge_len


        self.n_polyps = 0
        self.num_inputs = Coral.num_inputs + self.n_memory + len(morphogens_params) * (self.morph_thresholds-1)
        self.num_outputs = Coral.num_outputs + self.n_memory + len(morphogens_params)

        assert network.NumInputs() == self.num_inputs
        assert network.NumOutputs() == self.num_outputs

        self.polyp_inputs = np.zeros((self.max_polyps, self.num_inputs))
        # self.polyp_inputs = [0 for _ in range(self.num_inputs)]
        # self.polyp_inputs[self.num_inputs-1] = 1 # The last input is always used as bias.

        self.polyp_verts = [None] * self.max_polyps
        self.polyp_light = np.zeros(self.max_polyps)
        self.polyp_energy = np.zeros(self.max_polyps)
        self.polyp_flow = np.zeros(self.max_polyps)
        self.polyp_pos = np.zeros((self.max_polyps, 3))
        self.polyp_pos_next = np.zeros((self.max_polyps, 3))
        self.polyp_normal = np.zeros((self.max_polyps, 3))
        # self.polyp_last_pos = np.zeros((self.max_polyps, 3))
        self.polyp_gravity = np.zeros(self.max_polyps)
        self.polyp_collided = np.zeros(self.max_polyps, dtype='uint8')
        assert self.n_memory <= 32
        self.polyp_memory = np.zeros((self.max_polyps), dtype='uint32')

        self.collisionManager = MeshCollisionManager(self.mesh, self.polyp_pos, block_size)

        for vert in self.mesh.verts:
            self.createPolyp(vert)

        self.mesh.calculateNormals()
        self.mesh.calculateCurvature()
        self.updateAttributes()
        self.age = 0

    def __str__(self):
        s = 'Coral: {npolyps:%i, volume:%f}' % (len(self.n_polyps), self.volume)
        return s

    def step(self):
        self.polypsGrow()
        # self.correctGrowth()
        self.polypDivision() # Divide mesh and create new polyps.
        self.updateAttributes()
        self.age += 1

    def polypsGrow(self):
        """ Calculate the changes to coral by neural network.
        """
        # grow_polyps(self)
#
        for i in range(self.n_polyps):
            self.createPolypInputs(i)
            self.network.Flush() # Compute feed-forward network results.
            self.network.Input(self.polyp_inputs)
            self.network.ActivateFast()
            output = self.network.Output()

            assert len(output) == self.num_outputs

            # Move in normal direction by growth amount.
            growth = output[0] * self.growth_scalar
            self.polyp_pos_next[i, :] = self.polyp_pos[i] + growth * self.polyp_normal[i]

            # Output morphogens.
            out_idx = 1
            for mi in range(self.morphogens.n_morphogens):
                if output[out_idx] > 0.5:
                    self.morphogens.V[mi, i] = 1
                out_idx += 1

            for mi in range(self.n_memory):
                if output[out_idx] > 0.5:
                    self.polyp_memory[i] |= ( 1 << mi )
                out_idx += 1

        spring_target = np.zeros(3)
        for i in range(self.n_polyps):
            vert = self.mesh.verts[i]

            if vert.p[1] < 0:
                continue

            neighbors = vert.neighbors()
            spring_target *= 0

            for neighbor in neighbors:
                spring_target += self.target_edge_len * normed(np.array(neighbor.p) - vert.p)

            spring_target /= len(neighbors)
            spring_target += vert.p

            spring_strength = .3
            p = (1-spring_strength) * (self.polyp_pos_next[i]) + (spring_strength * spring_target)
            self.collisionManager.attemptVertUpdate(vert.id, p)

    # def correctGrowth(self):
    #     self.mesh.calculateNormals()
    #     self.mesh.calculateCurvature()

    #     self.max_curvature = .3

    #     for vi in range(self.n_polyps):
    #         vert = self.mesh.verts[vi]
    #         invalid = False

    #         if self.polyp_pos[vi, 1] < 0:
    #             invalid = True
    #         elif abs(vert.curvature) > self.max_curvature:
    #             invalid = True

    #         if invalid:
    #             vert.p[:] = self.polyp_last_pos[vi]

    def updateAttributes(self):

        self.mesh.calculateNormals()
        self.mesh.calculateCurvature()
        # print(max([abs(v.curvature) for v in self.mesh.verts]))
        light.calculate_light(self) # Update the light

        self.polyp_light[self.polyp_light != 0] -= .5
        self.polyp_light *= 2 # all light values go from 0-1

        # Adjust values to depend on height of polpy.
        # Make polyp on bottom get half light of one on top.
        # Height goes to about 10.
        self.polyp_light *= (.2 + self.polyp_pos[:, 1] * .08)

        gravity.calculate_gravity(self)
        self.morphogens.update(self.moprhogen_steps) # Update the morphogens.

    def createPolypInputs(self, i):

        """ Map polyp stats to nerual input in [-1, 1] range. """
        self.polyp_inputs = [-1] * self.num_inputs

        self.polyp_inputs[0] = (self.polyp_light[i] * 2) - 1
        self.polyp_inputs[1] = (self.polyp_verts[i].curvature * 2)
        self.polyp_inputs[2] = (self.polyp_gravity[i] * 2) - 1

        input_idx = 3
        for mi in range(self.morphogens.n_morphogens):
            mbin = int(floor(self.morphogens.U[mi, i] * self.morph_thresholds))
            mbin = min(self.morph_thresholds - 1, mbin)

            if mbin > 0:
                self.polyp_inputs[input_idx + (mbin-1)] = 1

            input_idx += (self.morph_thresholds-1)

        for mi in range(self.n_memory):
            if self.polyp_memory[i] & (1 << mi):
                self.polyp_inputs[input_idx] = 1
            else:
                self.polyp_inputs[input_idx] = -1
            input_idx += 1

    def createPolyp(self, vert):
        if self.n_polyps == self.max_polyps:
            return

        idx = self.n_polyps
        self.n_polyps += 1
        vert.data['polyp'] = idx
        self.polyp_pos[idx, :] = vert.p
        vert.normal = self.polyp_normal[idx]
        vert.p = self.polyp_pos[idx]
        self.polyp_verts[idx] = vert

        foo = np.zeros(self.n_memory, dtype='uint32')
        neighbors = vert.neighbors()
        half = len(neighbors) // 2

        for vert_n in neighbors:
            if 'polyp' in vert_n.data:
                memory = self.polyp_memory[vert_n.data['polyp']]
                for i in range(self.n_memory):
                    if memory & (1 << i):
                        foo[i] += 1

        for i in range(self.n_memory):
            if foo[i] > half:
                self.polyp_memory[idx] |= (1 << i)

        self.collisionManager.newVert(vert.id)

        assert vert.id == idx

    def splitFace(self, face):
        return False
        # if face.area() > self.max_face_area:
        #     return True

        # edges = face.edges()
        # if edges[0].length >
        # # assert len(edges) == 3, edges

    def polypDivision(self):
        """ Update the mesh and create new polyps.
        """
        # edge_splits = set()
        to_divide = set()
        # for face in self.mesh.faces:
        #     l1 = face.he.edge.length()
        #     l2 = face.he.next.edge.length()
        #     l3 = face.he.next.next.edge.length()
        #     minl = min(l1, l2, l3)
        #     maxl = max(l1, l2, l3)

        #     if maxl > 3 * minl:
        #         if maxl == l1:
        #             edge_splits.add(face.he.edge)
        #         elif maxl == l2:
        #             edge_splits.add(face.he.next.edge)
        #         else:
        #             edge_splits.add(face.he.next.next.edge)

        # for edge in edge_splits:
        #     if len(self.mesh.verts) == self.max_polyps:
        #         break
        #     self.mesh.splitEdge(edge)

        # for edge in self.mesh.edges:
        #     if edge.length() > self.max_edge_len:
        #         to_divide.add(edge.he.face)
        #         to_divide.add(edge.he.twin.face)

        # to_divide = []
        # for face in self.mesh.faces:
        #     if self.splitFace(face):
        #         to_divide.append(face)

        # for face in to_divide:
        #     if len(self.mesh.verts) == self.max_polyps:
        #         break
        #     split(self.mesh, face, self.max_polyps)

        old = set([ e.id for e in self.mesh.edges ])

        for edge in self.mesh.edges:
            if edge.length() > self.max_edge_len:
                self.mesh.splitEdge(edge)

            if len(self.mesh.verts) == self.max_polyps:
                break

        for edge in self.mesh.edges:
            if edge.id not in old:
                v1 = edge.he.next.next.vert
                v2 = edge.he.twin.next.next.vert

                d = sqrt((v1.p[0] - v2.p[0])**2 + (v1.p[1] - v2.p[1])**2 + (v1.p[2] - v2.p[2])**2)

                if edge.length() > d:
                    edge.flip()

        for vert in self.mesh.verts:
            if 'polyp' not in vert.data:
                self.createPolyp(vert)

    def fitness(self):
        light = 0

        volume = self.mesh.volume()

        capture = 0
        tree = KDTree(self.polyp_pos[:self.n_polyps], leafsize=16)
        query = np.zeros((1, 3))

        for face in self.mesh.faces:
            area = face.area()

            if isnan(area):
                v1, v2, v3 = face.vertices()
                p1 = v1.p
                p2 = v2.p
                p3 = v3.p
                a = (p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 + (p1[2] - p2[2])**2 # 1-2
                b = (p3[0] - p2[0])**2 + (p3[1] - p2[1])**2 + (p3[2] - p2[2])**2 # 2-3
                c = (p1[0] - p3[0])**2 + (p1[1] - p3[1])**2 + (p1[2] - p3[2])**2 # 1-3
                print(2*a*b + 2*b*c + 2*c*a - a*a - b*b - c*c)
                print(sqrt(2*a*b + 2*b*c + 2*c*a - a*a - b*b - c*c))
                assert not isnan(area), ([list(v.p) for v in face.vertices()])

            p = face.midpoint()
            if p[1] > .1:
                query[0] = p
                d, indx = tree.query(query, k=10)
                capture += area * np.mean(d)

            light += area * sum(self.polyp_light[v.id] for v in face.vertices())

        # Normalized values (values for seed).
        # print(light, capture, volume)
        light /= 0.257166
        capture /= 0.1255804
        volume /= 0.99041421

        # print(light, capture, volume)
        light_percent = .8
        fitness = self.C * (light_percent*light + (1-light_percent)*capture) / volume

        assert not isnan(fitness), (self.C, light, capture, volume)

        return fitness

    def export(self, out):
        """ Export the coral to .coral.obj file
            A .coral.obj file is a 3d mesh with polyp specific information.
            it is a compatable superset of the .obj file format.
            In addition to the content of a .obj file a .coral.obj file has:

            1. A header row that begins with '#coral' that lists space
                deliminated polyp attributes
            2. A line that begins with 'c' for each vert that contains values
                for each attribute. Ordered the same as the vertices.
        """
        self.mesh.calculateNormals()
        self.mesh.calculateCurvature()

        header = [ 'light', 'gravity', 'curvature', 'memory']
        for i in range(self.morphogens.n_morphogens):
            header.append( 'u%i' % i )

        out.write('#Exported from coral_growth\n')
        out.write('#coral ' + ' '.join(header) + '\n')

        mesh_data = self.mesh.export()

        id_to_indx = dict()

        for i, vert in enumerate(self.mesh.verts):
            r, g, b = 0, 0, 0

            if self.morphogens.n_morphogens > 0:
                g = self.morphogens.U[0, i]

            if self.morphogens.n_morphogens > 1:
                b = self.morphogens.U[1, i]

            out.write('v %f %f %f %f %f %f\n' % (tuple(vert.p)+(r, g, b)))
            id_to_indx[vert.id] = i

        out.write('\n\n')

        polyp_attributes = [None] * self.n_polyps

        for i in range(self.n_polyps):
            indx = id_to_indx[self.polyp_verts[i].id]

            polyp_attributes[indx] = [ self.polyp_light[i],
                                       self.polyp_gravity[i],
                                       self.polyp_verts[i].curvature,
                                       self.polyp_memory[i] ]

            for j in range(self.morphogens.n_morphogens):
                polyp_attributes[indx].append(self.morphogens.U[j, i])

            assert len(polyp_attributes[indx]) == len(header)

        for attributes in polyp_attributes:
            out.write('c ' + ' '.join(map(str, attributes)) + '\n')

        out.write('\n')

        for face in mesh_data['faces']:
            out.write('f %i %i %i\n' % tuple(face + 1))
