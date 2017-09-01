from __future__ import print_function
from OpenGL.GL import *
from OpenGL.GLU import gluDeleteQuadric, gluNewQuadric, gluSphere

G_OBJ_PLANE = 1
G_OBJ_SPHERE = 2
G_OBJ_CUBE = 3


def make_plane2(n):
    glNewList(G_OBJ_PLANE, GL_COMPILE)
    glColor3f(153./255, 90./255, 0)
    glBegin(GL_QUADS)

    x = 100
    glVertex4f(-x, 0, -n, .1)
    glVertex4f(-x, 0, x, .1)
    glVertex4f(x, 0, x, .1)
    glVertex4f(x, 0, -x, .1)
    # glVertex4f(-1,0,  -1, 0)
    # glVertex4f(-1,0,  1, 0)
    # glVertex4f(1,0,  1, 0)
    # glVertex4f(1,0,  -1, 0)
    glEnd()
    glEndList()



def make_plane(n):
    glNewList(G_OBJ_PLANE, GL_COMPILE)
    glBegin(GL_LINES)
    glColor3f(0, 0, 0)

    for i in range(-n, n+1):
        glVertex3f(i, 0, -n)
        glVertex3f(i, 0, n)
        glVertex3f(-n, 0, i)
        glVertex3f(n, 0, i)

    # Axes
    glEnd()
    glLineWidth(5)

    glBegin(GL_LINES)
    glColor3f(0.5, 0.7, 0.5)
    glVertex3f(0, 0, 0)
    glVertex3f(4.5, 0, 0)
    glEnd()

    glBegin(GL_LINES)
    glColor3f(0.5, 0.7, 0.5)

    glVertex3f(0, 0, 0)
    glVertex3f(0, 4.5, 0)
    glEnd()

    glBegin(GL_LINES)
    glColor3f(0.5, 0.7, 0.5)

    glVertex3f(0, 0, 0)
    glVertex3f(0, 0, 4.5)
    glEnd()

    # Draw the Y.
    glBegin(GL_LINES)
    glColor3f(0.0, 0.0, 0.0)

    glVertex3f(-.5, 4.5, -.5)
    glVertex3f(-.5, 5.0, -.5)
    glVertex3f(-.5, 5.0, -.5)
    glVertex3f(-1, 5.5, -.5)
    glVertex3f(-.5, 5.0, -.5)
    glVertex3f(0.0, 5.5, -.5)

    # Draw the Z.
    glVertex3f(-1., -.5, 4.5)
    glVertex3f(0.0, -0.5, 4.5)
    glVertex3f(0.0, -0.5, 4.5)
    glVertex3f(-1.0, -.5, 5.5)
    glVertex3f(-1.0, -.5, 5.5)
    glVertex3f(0.0, -.5, 5.5)

    # Draw the X.
    glVertex3f(4.5, -.5, 0.0)
    glVertex3f(5.5, -.5, -1)
    glVertex3f(4.5, -.5, -1.0)
    glVertex3f(5.5, -.5, 0.0)

    glEnd()
    glLineWidth(1)
    glEndList()

def make_sphere():
    glNewList(G_OBJ_SPHERE, GL_COMPILE)
    quad = gluNewQuadric()
    gluSphere(quad, 0.5, 30, 30)
    gluDeleteQuadric(quad)
    glEndList()

def make_cube():
    glNewList(G_OBJ_CUBE, GL_COMPILE)
    vertices = [((-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, 0.5), (-0.5, 0.5, -0.5)),
                ((-0.5, -0.5, -0.5), (-0.5, 0.5, -0.5), (0.5, 0.5, -0.5), (0.5, -0.5, -0.5)),
                ((0.5, -0.5, -0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5), (0.5, -0.5, 0.5)),
                ((-0.5, -0.5, 0.5), (0.5, -0.5, 0.5), (0.5, 0.5, 0.5), (-0.5, 0.5, 0.5)),
                ((-0.5, -0.5, 0.5), (-0.5, -0.5, -0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5)),
                ((-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (0.5, 0.5, 0.5), (0.5, 0.5, -0.5))]
    normals = [(-1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, -1.0, 0.0), (0.0, 1.0, 0.0)]

    glBegin(GL_QUADS)
    for i in range(6):
        glNormal3f(normals[i][0], normals[i][1], normals[i][2])
        for j in range(4):
            glVertex3f(vertices[i][j][0], vertices[i][j][1], vertices[i][j][2])
    glEnd()
    glEndList()

def init_primitives():
    make_plane()
    make_sphere()
    make_cube()
