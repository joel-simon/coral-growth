# cython: boundscheck=False
# cython: wraparound=True
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True

from __future__ import print_function

from math import isnan, sqrt
from random import random, shuffle

import numpy as np
from cymesh.mesh import Mesh
from cymesh.collisions.findCollisions import findCollisions

from plant_growth.divide_mesh import divide_mesh, relax_mesh

from plant_growth.divide_mesh import face_area
from plant_growth.light import calculate_light
from plant_growth.cell import Cell

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

        mean_face = np.mean([face_area(f) for f in self.mesh.faces])
        self.max_face = mean_face * config['max_face_growth']

        self.cells = []
        self.cell_inputs = [0 for _ in range(Plant.num_inputs+1)]
        self.cell_inputs[Plant.num_inputs] = 1 # The last input is always used as bias.

        for vert in self.mesh.verts:
            self.createPolyp(vert, None, None)

        self.updateAttributes()
        self.age = 0

    def __str__(self):
        s = 'Plant: {ncells:%i, volume:%f}' % (len(self.cells), self.volume)
        return s

    def step(self):

        self.polypsGrow()
        self.polypDivision()
        # relax_mesh(self.mesh)
        self.updateAttributes()
        self.age += 1

    def polypsGrow(self):
        """ Calculate the changes to plant by neural network.
        """
        self.total_gametes = 0
        for cell in self.cells:
            self.createPolypInputs(cell)

            # Compute feed-forward network results.
            self.network.Flush()
            self.network.Input(self.cell_inputs)
            self.network.ActivateFast()

            self.handlePolypOutputs(cell, self.network.Output())

        self.handleCollisions()

    def createPolypInputs(self, cell):
        """ Map cell stats to nerual input in [-1, 1] range. """
        self.cell_inputs[0] = (cell.light * 2) - 1
        self.cell_inputs[1] = (cell.vert.curvature * 2) - 1

    def handlePolypOutputs(self, cell, output):
        growth_energy = output[0]

        self.total_gametes += 1 - growth_energy

        # Move in nomral direction by growth amount.
        cell.last_p[:] = cell.vert.p
        growth = growth_energy * self.growth_scalar
        cell.vert.p[0] += cell.vert.normal[0] * growth
        cell.vert.p[1] += cell.vert.normal[1] * growth
        cell.vert.p[2] += cell.vert.normal[2] * growth

    def handleCollisions(self):
        collisions = findCollisions(self.mesh)

        for vi, collided in enumerate(collisions):
            if collided:
                vert = self.mesh.verts[vi]
                polyp = vert.data['cell']
                # vert.data['collided'] = True
                vert.p[:] = polyp.last_p

    def updateAttributes(self):
        """ In each simulation step, grow is called on all plants then
            updateAttributes. Grow has used up all spare energy.
        """
        # self.volume = self.mesh.volume()
        self.mesh.calculateNormals()
        self.mesh.calculateCurvature()
        calculate_light(self) # Call the light module

        for cell in self.cells:
            assert (not isnan(cell.light))

        # self.calculate_flow() # TODO
        # self.diffuseEnergy() # TODO

    def createPolyp(self, vert, p1, p2):
        cell = Cell(vert.id, vert)
        self.cells.append(cell)
        vert.data['cell'] = cell

        return cell

    def polypDivision(self):
        """ Update the mesh and create new cells.
        """
        divide_mesh(self.mesh, self.max_face)

        for vert in self.mesh.verts:
            if 'cell' not in vert.data:
                cell = self.createPolyp(vert, None, None)
                vert.data['cell'] = cell

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
        i = 0
        header = [ 'light', 'flow', 'ctype' ]

        out.write('#Exported from plant_growth\n')
        out.write('#plant: ' + ' '.join(header) + '\n')

        mesh_data = self.mesh.export()

        id_to_indx = dict()

        for vert in self.mesh.verts:
            out.write('v %f %f %f\n' % (tuple(vert.p)))
            id_to_indx[vert.id] = i
            i += 1

        out.write('\n\n')

        for vn in mesh_data['vertice_normals']:
            out.write('vn %f %f %f\n' % tuple(vn))

        cell_attributes = [None] * len(self.cells)

        for cell in self.cells:
            indx = id_to_indx[cell.vert.id]
            cell_attributes[indx] = [ cell.light, cell.flow, cell.ctype ]

        for attributes in cell_attributes:
            out.write('c ' + ' '.join(map(str, attributes)) + '\n')

        out.write('\n')

        for face in mesh_data['faces']:
            out.write('f %i %i %i\n' % tuple(face+1))
