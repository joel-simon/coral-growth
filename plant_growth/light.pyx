# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True

from libc.math cimport M_PI, sin, cos, fmax
import numpy as np
cimport numpy as np

from cymesh.mesh cimport Mesh
from cymesh.structures cimport Vert, Face, Edge
from cymesh.vector3D cimport vangle

from plant_growth.tri_hash_2d cimport TriHash2D

cdef bint pnt_in_tri(double[:] p, double[:] p0, double[:] p1, double[:] p2):
    # https://stackoverflow.com/questions/2049582/how-to-determine-if-a-point-is-in-a-2d-triangle
    cdef double s = p0[1] * p2[0] - p0[0] * p2[1] + (p2[1] - p0[1]) * p[0] + \
                                                    (p0[0] - p2[0]) * p[1]
    cdef double t = p0[0] * p1[1] - p0[1] * p1[0] + (p0[1] - p1[1]) * p[0] + \
                                                    (p1[0] - p0[0]) * p[1]

    if (s < 0) != (t < 0):
        return False

    cdef double A = -p1[1] * p2[0] + p0[1] * (p2[0] - p1[0]) + p0[0] * \
                                     (p1[1] - p2[1]) + p1[0] * p2[1]

    if A < 0.0:
        s = -s
        t = -t
        A = -A

    return s > 0 and t > 0 and (s + t) <= A

cpdef void calculate_light(plant) except *:
    """ Calculate the light on each polyp of a plant.
    """
    cdef:
        Vert v1, v2, v3, vert
        Face face
        Edge e
        double[:] p = np.zeros(2)
        double[:] a = np.zeros(2)
        double[:] b = np.zeros(2)
        double[:] c = np.zeros(2)

        double[:] p1
        double[:] p2
        double[:] p3
        double angle_to_light
        int i, j, n, v1_id, v2_id, v3_id, face_id

    # Memeoryviews of coral.
    cdef double[:] polyp_light = plant.polyp_light
    cdef double[:,:] polyp_pos = plant.polyp_pos
    cdef double[:,:] polyp_normal = plant.polyp_normal

    cdef double[:] boundingBox = plant.mesh.boundingBox()
    cdef double world_size = max(boundingBox[1]- boundingBox[0], boundingBox[3]- boundingBox[2])


    cdef double max_e = 0
    for e in plant.mesh.edges:
        max_e = fmax(max_e, e.length())

    cdef int[:] face_buffer = np.zeros(1000, dtype='int32')
    cdef double[:] light = np.array([0, 1.0, 0], dtype='float64')
    cdef TriHash2D th2d = TriHash2D(cell_size=max_e, world_size=world_size)

    cdef int[:,:] faces = np.zeros((len(plant.mesh.faces), 3), dtype='i')

    for i, face in enumerate(plant.mesh.faces):
        v1 = face.he.vert
        v2 = face.he.next.vert
        v3 = face.he.next.next.vert

        faces[i, 0] = v1.id
        faces[i, 1] = v2.id
        faces[i, 2] = v3.id

        a[0] = v1.p[0]
        a[1] = v1.p[2]

        b[0] = v2.p[0]
        b[1] = v2.p[2]

        c[0] = v3.p[0]
        c[1] = v3.p[2]

        th2d.add_tri(i, a, b, c)

    for i in range(plant.n_cells):
        angle_to_light = vangle(light, polyp_normal[i]) / M_PI

        if angle_to_light > .5:
            polyp_light[i] = 0
            continue

        polyp_light[i] = 1 - angle_to_light

        # Take position in xz plane.
        p[0] = polyp_pos[i, 0]
        p[1] = polyp_pos[i, 2]

        n = th2d.neighbors(p, face_buffer)

        for j in range(n):
            face_id = face_buffer[j]

            v1_id = faces[face_id, 0]
            v2_id = faces[face_id, 1]
            v3_id = faces[face_id, 2]

            if v1_id == i or v2_id == i or v3_id == i:
                continue

            p1 = polyp_pos[v1_id]
            p2 = polyp_pos[v2_id]
            p3 = polyp_pos[v3_id]

            # If face is below vert, it does not block.
            if (p1[1] + p2[1] + p3[1]) / 3.0 < polyp_pos[i, 1]:
                continue

            a[0] = p1[0]
            a[1] = p1[2]

            b[0] = p2[0]
            b[1] = p2[2]

            c[0] = p3[0]
            c[1] = p3[2]

            if pnt_in_tri(p, a, b, c):
                polyp_light[i] = 0
                break

        # assert (not isnan(plant.polyp_light[i]))
