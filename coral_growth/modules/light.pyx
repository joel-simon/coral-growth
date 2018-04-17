# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True

from libc.math cimport M_PI, sin, cos, fmax
import numpy as np
cimport numpy as np

from coral_growth.growth_form cimport GrowthForm
from coral_growth.modules.tri_hash_2d cimport TriHash2D

from cymesh.mesh cimport Mesh
from cymesh.structures cimport Vert, Face, Edge
from cymesh.vector3D cimport vangle

cpdef void calculate_light(GrowthForm coral) except *:
    """ Calculate the light on each node of a coral.
    """
    cdef:
        Vert v1, v2, v3, vert
        Face face
        Edge e
        Mesh mesh = coral.mesh
        double[:] p = np.zeros(2)
        double[:] a = np.zeros(2)
        double[:] b = np.zeros(2)
        double[:] c = np.zeros(2)
        double angle_to_light, c_height
        int i, j, n, v1_id, v2_id, v3_id, face_id
        double[:] boundingBox = coral.mesh.boundingBox()
        double world_size = max(boundingBox[1]-boundingBox[0], boundingBox[3]-boundingBox[2])

    cdef double max_e = 0
    for e in coral.mesh.edges:
        max_e = fmax(max_e, e.length())

    cdef int[:] face_buffer = np.zeros(1000, dtype='int32')
    cdef double[:] light = np.array([0, 1.0, 0], dtype='float64')
    cdef TriHash2D th2d = TriHash2D(cell_size=max_e, world_size=world_size)

    cdef int[:,:] faces = np.zeros((len(coral.mesh.faces), 3), dtype='i')

    i = 0
    for face in mesh.faces:
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
        i += 1

    for i in range(coral.n_nodes):
        angle_to_light = vangle(light, coral.node_normal[i]) / M_PI

        if angle_to_light > .5:
            coral.node_light[i] = 0
            continue

        coral.node_light[i] = 2*(1 - angle_to_light - 0.5)

        # Take position in xz plane.
        p[0] = coral.node_pos[i, 0]
        p[1] = coral.node_pos[i, 2]

        n = th2d.neighbors(p, face_buffer)

        for j in range(n):
            face_id = face_buffer[j]

            v1_id = faces[face_id, 0]
            v2_id = faces[face_id, 1]
            v3_id = faces[face_id, 2]

            if v1_id == i or v2_id == i or v3_id == i:
                continue

            c_height = (coral.node_pos[v1_id, 1] + coral.node_pos[v2_id, 1] + \
                        coral.node_pos[v3_id, 1]) / 3.0

            # If face is below vert, it does not block.
            if c_height < coral.node_pos[i, 1]:
                continue

            a[0] = coral.node_pos[v1_id, 0]
            a[1] = coral.node_pos[v1_id, 2]
            b[0] = coral.node_pos[v2_id, 0]
            b[1] = coral.node_pos[v2_id, 2]
            c[0] = coral.node_pos[v3_id, 0]
            c[1] = coral.node_pos[v3_id, 2]

            if pnt_in_tri(p, a, b, c):
                coral.node_light[i] = 0
                break
