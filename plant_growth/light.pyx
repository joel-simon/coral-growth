# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True

from libc.math cimport M_PI, sin, cos
import numpy as np
cimport numpy as np

from cymesh.mesh cimport Mesh
from cymesh.structures cimport Vert, Face, Edge
from cymesh.vector3D cimport vangle

from plant_growth.tri_hash_2d cimport TriHash2D
from plant_growth.cell cimport Cell

cdef bint pnt_in_tri(double p[2], double p0[2], double p1[2], double p2[2]):
    # https://stackoverflow.com/questions/2049582/how-to-determine-if-a-point-is-in-a-2d-triangle
    cdef double s = p0[1] * p2[0] - p0[0] * p2[1] + (p2[1] - p0[1]) * p[0] + (p0[0] - p2[0]) * p[1]
    cdef double t = p0[0] * p1[1] - p0[1] * p1[0] + (p0[1] - p1[1]) * p[0] + (p1[0] - p0[0]) * p[1]

    if (s < 0) != (t < 0):
        return False

    cdef double A = -p1[1] * p2[0] + p0[1] * (p2[0] - p1[0]) + p0[0] * (p1[1] - p2[1]) + p1[0] * p2[1]

    if A < 0.0:
        s = -s
        t = -t
        A = -A

    return s > 0 and t > 0 and (s + t) <= A

cpdef void calculate_light(plant) except *:
    """ Calculate the light on each polyp of a plant.
    """
    cdef:
    #     uint m, n
        Cell cell
        Vert v1, v2, v3
        Face face
        double p[2], a[2], b[2], c[2]
        bint below
        double angle_to_light
        int i, j, n

    cdef double[:] boundingBox = plant.mesh.boundingBox()
    cdef double world_size = max(boundingBox[1]- boundingBox[0], boundingBox[3]- boundingBox[2])
    cdef max_e = max([e.length() for e in plant.mesh.edges])

    cdef int[:] face_buffer = np.zeros(1000, dtype='int32')
    cdef double[:] light = np.array([0, 1.0, 0], dtype='float64')
    cdef TriHash2D th2d = TriHash2D(cell_size=max_e, world_size=world_size)

    for face in plant.mesh.faces:
        v1, v2, v3 = face.vertices()
        a[0] = v1.p[0]
        a[1] = v1.p[2]

        b[0] = v2.p[0]
        b[1] = v2.p[2]

        c[0] = v3.p[0]
        c[1] = v3.p[2]

        th2d.add_tri(face.id, a, b, c)

    for cell in plant.cells:
        angle_to_light = vangle(light, cell.vert.normal) / M_PI

        if angle_to_light > .5:
            cell.light = 0
            continue

        cell.light = 1 - angle_to_light

        p[0] = cell.vert.p[0]
        p[1] = cell.vert.p[2]

        n = th2d.neighbors(p, face_buffer)

        for i in range(n):

            face = plant.mesh.faces[face_buffer[i]]

            v1, v2, v3 = face.vertices()

            if v1 is cell.vert or v2 is cell.vert or v3 is cell.vert:
                continue

            # If face is below vert, it does not block.
            if (v1.p[1] + v2.p[1] + v3.p[1]) / 3.0 < cell.vert.p[1]:
                continue

            a[0] = v1.p[0]
            a[1] = v1.p[2]

            b[0] = v2.p[0]
            b[1] = v2.p[2]

            c[0] = v3.p[0]
            c[1] = v3.p[2]

            if pnt_in_tri(p, a, b, c):
                cell.light = 0
                break
