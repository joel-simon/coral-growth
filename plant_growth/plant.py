# cython: boundscheck=False
# cython: wraparound=True
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True

from __future__ import print_function
from math import isnan, sqrt
import numpy as np

from cymesh.mesh import Mesh
from cymesh.collisions.findCollisions import findCollisions
from cymesh.subdivision.sqrt3 import divide_adaptive
from cymesh.operators.relax import relax_mesh

from plant_growth.light import calculate_light

class Plant(object):
    num_inputs = 2
    num_outputs = 1

    def __init__(self, obj_path, network, config):
        self.mesh = Mesh.from_obj(obj_path)
        self.network = network

        self.volume = 0
        self.total_gametes = 0

        self.growth_scalar = config['growth_scalar']
        self.max_cells = config['max_cells']

        mean_face = np.mean([f.area() for f in self.mesh.faces])
        self.max_face = mean_face * config['max_face_growth']

        self.n_cells = 0
        # self.cells = []
        self.cell_inputs = [0 for _ in range(Plant.num_inputs+1)]
        self.cell_inputs[Plant.num_inputs] = 1 # The last input is always used as bias.

        self.polyp_verts = [None] * self.max_cells
        self.polyp_light = np.zeros(self.max_cells)
        self.polyp_flow = np.zeros(self.max_cells)
        self.polyp_pos = np.zeros((self.max_cells, 3))
        self.polyp_normal = np.zeros((self.max_cells, 3))
        self.polyp_last_pos = np.zeros((self.max_cells, 3))
        self.poly_collided = np.zeros((self.max_cells, 3), dtype='uint8')

        for vert in self.mesh.verts:
            self.createPolyp(vert)

        self.updateAttributes()
        self.age = 0


    def __str__(self):
        s = 'Plant: {ncells:%i, volume:%f}' % (len(self.n_cells), self.volume)
        return s

    def step(self):
        self.polypsGrow()
        self.polypDivision()
        relax_mesh(self.mesh)
        self.updateAttributes()
        self.age += 1

    def polypsGrow(self):
        """ Calculate the changes to plant by neural network.
        """
        self.total_gametes = 0

        self.polyp_last_pos[:, :] = self.polyp_pos

        for i in range(self.n_cells):
            self.createPolypInputs(i)
            self.network.Flush() # Compute feed-forward network results.
            self.network.Input(self.cell_inputs)
            self.network.ActivateFast()
            output =  self.network.Output()

            growth_energy = output[0]
            self.total_gametes += 1 - growth_energy
            # Move in nomral direction by growth amount.
            growth = growth_energy * self.growth_scalar
            self.polyp_pos[i] += self.polyp_normal[i] * growth

        self.handleCollisions()

    def createPolypInputs(self, i):
        """ Map cell stats to nerual input in [-1, 1] range. """
        assert self.polyp_verts[i]
        self.cell_inputs[0] = (self.polyp_light[i] * 2) - 1
        self.cell_inputs[1] = (self.polyp_verts[i].curvature * 2) - 1

    def handleCollisions(self):
        collisions = findCollisions(self.mesh)

        for vi, collided in enumerate(collisions):
            if collided:
                vert = self.mesh.verts[vi]
                vert.p[:] = self.polyp_last_pos[vi]
                self.poly_collided[vi] = 1

    def updateAttributes(self):
        """ In each simulation step, grow is called on all plants then
            updateAttributes. Grow has used up all spare energy.
        """
        # self.volume = self.mesh.volume()
        self.mesh.calculateNormals()
        self.mesh.calculateCurvature()
        calculate_light(self) # Call the light module

        # self.calculate_flow() # TODO
        # self.diffuseEnergy() # TODO

    def createPolyp(self, vert):
        if self.n_cells == self.max_cells:
            return
        i = self.n_cells
        self.n_cells += 1
        vert.data['cell'] = i
        self.polyp_pos[i, :] = vert.p
        vert.normal = self.polyp_normal[i]
        vert.p = self.polyp_pos[i]
        self.polyp_verts[i] = vert

    def polypDivision(self):
        """ Update the mesh and create new cells.
        """
        divide_adaptive(self.mesh, self.max_face)

        for vert in self.mesh.verts:
            if 'cell' not in vert.data:
                self.createPolyp(vert)

    def export(self, out):
        """ Export the plant to .plant.obj file
            A .plant.obj file is a 3d mesh with cell specific information.
            it is a compatable superset of the .obj file format.
            In addition to the content of a .obj file a .plant file has:

            1. A header row that begins with '#plant' that lists space
                deiminated cell attributes
            2. A line that begins with 'c' for each vert that contains values for
                cell for each attribute. Ordered the same as the vertices.
        """
        header = [ 'light', 'flow', 'ctype' ]

        out.write('#Exported from plant_growth\n')
        out.write('#plant: ' + ' '.join(header) + '\n')

        mesh_data = self.mesh.export()

        id_to_indx = dict()

        for i, vert in enumerate(self.mesh.verts):
            out.write('v %f %f %f\n' % (tuple(vert.p)))
            id_to_indx[vert.id] = i

        out.write('\n\n')

        for vn in mesh_data['vertice_normals']:
            out.write('vn %f %f %f\n' % tuple(vn))

        cell_attributes = [None] * self.n_cells

        # for cell in self.cells:
        for i in range(self.n_cells):
            indx = id_to_indx[self.polyp_verts[i].id]
            cell_attributes[indx] = [ self.polyp_light[i], self.polyp_flow[i] ]

        for attributes in cell_attributes:
            out.write('c ' + ' '.join(map(str, attributes)) + '\n')

        out.write('\n')

        for face in mesh_data['faces']:
            out.write('f %i %i %i\n' % tuple(face+1))
