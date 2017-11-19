import math
from cymesh.mesh import Mesh
from cymesh.structures import Vert, HalfEdge, Face, Edge

def _vert(self, x, y, z, he=None):
    vert = Vert(len(self.verts), x, y, z, he)
    self.verts.append(vert)
    vert.normal[:] = -1
    return vert

def _edge(self, he=None):
    edge = Edge(len(self.edges), he)
    self.edges.append(edge)
    return edge

def _face(self, he=None):
    face = Face(len(self.faces), he)
    self.faces.append(face)
    return face

def _half(self, twin=None, next=None, vert=None, edge=None, face=None):
    he = HalfEdge(len(self.halfs), twin, next, vert, edge, face)
    self.halfs.append(he)
    return he

def triangle_area(p1, p2, p3):
    # http://www.iquilezles.org/blog/?p=1579
    a = (p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 + (p1[2] - p2[2])**2 # 1-2
    b = (p3[0] - p2[0])**2 + (p3[1] - p2[1])**2 + (p3[2] - p2[2])**2 # 2-3
    c = (p1[0] - p3[0])**2 + (p1[1] - p3[1])**2 + (p1[2] - p3[2])**2 # 1-3
    return math.sqrt(2*a*b + 2*b*c + 2*c*a - a*a - b*b - c*c) / 16.0

def face_area(face):
    v1, v2, v3 = face.vertices()
    return triangle_area(v1.p, v2.p, v3.p)

def face_midpoint(face):
    v1, v2, v3 = face.vertices()
    x = (v1.p[0] + v2.p[0] + v3.p[0]) / 3.0
    y = (v1.p[1] + v2.p[1] + v3.p[1]) / 3.0
    z = (v1.p[2] + v2.p[2] + v3.p[2]) / 3.0
    return x, y, z

def split(mesh, f1):
    """ Root(3) subdivision, insert one vertex inside the face.
        http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.43.1955
    """
    generation = f1.generation

    if generation % 2 == 0:
        x, y, z = face_midpoint(f1)
        v4 = _vert(mesh, x, y, z)

        he1 = f1.he
        he2 = f1.he.next
        he3 = f1.he.next.next

        v1 = he1.vert
        v2 = he2.vert
        v3 = he3.vert

        f2 = _face(mesh)
        f3 = _face(mesh)

        # Create three new edges.
        e12 = _edge(mesh)
        e23 = _edge(mesh)
        e13 = _edge(mesh)

        # Create two new half-edges for each face.
        he11 = _half(mesh, vert=v2, face=f1, edge=e12)
        he12 = _half(mesh, vert=v4, face=f1, edge=e13, next=he1)

        he21 = _half(mesh, vert=v3, face=f2, edge=e23)
        he22 = _half(mesh, vert=v4, face=f2, edge=e12, next=he2)

        he31 = _half(mesh, vert=v1, face=f3, edge=e13)
        he32 = _half(mesh, vert=v4, face=f3, edge=e23, next=he3)

        # Set half edge twins and nexts.
        he1.next = he11
        he11.next = he12
        he11.twin = he22
        he12.twin = he31

        he2.next = he21
        he21.next = he22
        he21.twin = he32
        he22.twin = he11

        he3.next = he31
        he31.next = he32
        he31.twin = he12
        he32.twin = he21

        # Connect old to faces.
        he2.face = f2
        he3.face = f3

        #Connect elements ot half-edges
        f2.he = he2
        f3.he = he3
        e12.he = he11
        e23.he = he21
        e13.he = he31
        v4.he = he12

        # Adaptive Refinement Logic.
        f1.generation = generation + 1
        f2.generation = generation + 1
        f3.generation = generation + 1

        f1.mate = he1.twin.face
        f2.mate = he2.twin.face
        f3.mate = he3.twin.face

        if f1.mate.generation == f1.generation:
            he1.edge.flip()
            f1.generation += 1
            f1.mate.generation += 1

        if f2.mate.generation == f2.generation:
            he2.edge.flip()
            f2.generation += 1
            f2.mate.generation += 1

        if f3.mate.generation == f3.generation:
            he3.edge.flip()
            f3.generation += 1
            f3.mate.generation += 1
    else:
        assert f1.mate is not None
        if f1.mate.generation == f1.generation - 2:
            split(mesh, f1.mate)
        split(mesh, f1.mate)

def divide_mesh(mesh, max_face_area):
    for face in list(mesh.faces):
        if face_area(face) > max_face_area:
            split(mesh, face)

def relax_mesh(mesh):
    for vert in mesh.verts:
        N = vert.neighbors()
        mean_x = np.mean([n.p[0] for n in N])
        mean_y = np.mean([n.p[1] for n in N])
        mean_z = np.mean([n.p[2] for n in N])

        d = math.sqrt((vert.p[0] - mean_x)**2 + (vert.p[1] - mean_y)**2 + (vert.p[2] - mean_z)**2)
        vert.data['d'] = d

        vert.p[0] = mean_x
        vert.p[1] = mean_y
        vert.p[2] = mean_z

    mesh.calculateNormals()

    for vert in mesh.verts:
        vert.p[0] += vert.normal[0] * vert.data['d']
        vert.p[1] += vert.normal[1] * vert.data['d']
        vert.p[2] += vert.normal[2] * vert.data['d']
