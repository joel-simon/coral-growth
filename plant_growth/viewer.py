# Basic OBJ file viewer. needs objloader from:
#  http://www.pygame.org/wiki/OBJFileLoader
# LMB + move: rotate
# RMB + move: pan
# Scroll wheel: zoom in/out
import sys, pygame, math
from pygame.locals import *
from pygame.constants import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

from .primitive import make_plane, G_OBJ_PLANE, G_OBJ_SPHERE

from OpenGL.arrays import vbo
from OpenGL.raw.GL.ARB.vertex_array_object import glGenVertexArrays, \
                                                  glBindVertexArray


class Viewer(object):
    def __init__(self, view_size=(800, 600)):
        # self.bounds = bounds
        self.on = True
        self.animation = None
        self.animation_playing = False
        self.draw_grid = False

        pygame.init()
        glutInit()
        viewport = view_size

        hx = viewport[0]/2
        hy = viewport[1]/2
        srf = pygame.display.set_mode(viewport, OPENGL | DOUBLEBUF)

        glLightfv(GL_LIGHT0, GL_POSITION,  (-40, 200, 100, 0.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.2, 0.2, 0.2, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.5, 0.5, 0.5, 1.0))
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHTING)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glEnable(GL_COLOR_MATERIAL)
        # glClearColor(0.4, 0.4, 0.4, 0.0)
        glClearColor(1.0, 1.0, 1.0, 0.0)

        glEnable(GL_DEPTH_TEST)
        glShadeModel(GL_SMOOTH)

        # glCullFace(GL_BACK)
        glDisable( GL_CULL_FACE )

        # glPolygonMode ( GL_FRONT_AND_BACK, GL_LINE )

        # Transparancy?
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_BLEND)


        self.clock = pygame.time.Clock()

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        width, height = viewport
        gluPerspective(90.0, width/float(height), 1, 100.0)
        glEnable(GL_DEPTH_TEST)
        glMatrixMode(GL_MODELVIEW)

        glTranslated(-15, -15, -15)
        make_plane(5)

        self.rx, self.ry = (0,0)
        self.tx, self.ty = (0,0)
        self.zpos = 10

        self.gl_lists = []


    def start_draw(self):
        self.gl_list = glGenLists(1)
        glNewList(self.gl_list, GL_COMPILE)

    def end_draw(self):
        glEndList()
        self.gl_lists.append(self.gl_list)
        self.gl_list = None


    def build_compiled_gllist(self, mesh):
        """this time, the vertices must be specified globally, and referenced by
        indices in order to use the list paradigm. vertices is a list of 3-vectors, and
        facets are dicts containing 'normal' (a 3-vector) 'vertices' (indices to the
        other argument) and 'color' (the color the triangle should be)."""

        # first flatten out the arrays:
        vertices = mesh['vertices'].flatten()
        normals = mesh['vertice_normals'].flatten()
        indices = mesh['faces'].astype('uint32').flatten()
        colors = mesh['vert_colors'].flatten()

        # then convert to OpenGL / ctypes arrays:
        vertices = (GLfloat * len(vertices))(*vertices)
        normals = (GLfloat * len(normals))(*normals)
        indices = (GLuint * len(indices))(*indices)
        colors = (GLfloat * len(colors))(*colors)
        # colors = [1] * len(colors)
        # finally, build the list:
        # list = glGenLists(1)
        # glNewList(list, GL_COMPILE)

        glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, vertices)
        glNormalPointer(GL_FLOAT, 0, normals)
        glColorPointer(3, GL_FLOAT, 0, colors)
        glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, indices)
        # glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, indices)
        glPopClientAttrib()
        # glEndList()
        # return list

    def draw_mesh(self, mesh):
        verts = mesh['vertices']
        edges = mesh['edges']
        faces = mesh['faces'].astype('uint32')
        face_normals = mesh['face_normals']
        vert_normals = mesh['vertice_normals']
        curvature = mesh['curvature']
        # print(curvature)
        norm_length = .15
        glColor(1, 1, 1)

        glBegin(GL_TRIANGLES)
        for face in faces:
            for vid in face:
                glNormal3fv(vert_normals[vid])
                glVertex3fv(verts[vid])
        glEnd()

        # Draw edges
        glColor(.9, .9, .9)
        for i, j in edges:
            glLineWidth(1)
            glBegin(GL_LINES)
            glVertex3fv(verts[i]*1.001)
            glVertex3fv(verts[j]*1.001)
            glEnd()
        glLineWidth(1)

        # face normals
        # glColor(0,0,1)
        # for face, norm in zip(faces, face_normals):
        #     glBegin(GL_LINES)
        #     center = (verts[face[0]] + verts[face[1]] + verts[face[2]]) /3
        #     norm *= norm_length
        #     glVertex3fv(center)
        #     glVertex3fv(center + norm)
        #     glEnd()

        # Draw curvature
        # glColor(0, 1, 0)
        # glLineWidth(3)

        # for vert, norm, curve in zip(verts, vert_normals, curvature):
        #     glBegin(GL_LINES)
        #     norm *= curve
        #     glVertex3fv(vert)
        #     glVertex3fv(vert + norm)
        #     glEnd()


        # vert normals
        # glColor(1,0,0)
        # for vert, norm in zip(verts, vert_normals):
        #     glBegin(GL_LINES)
        #     norm *= norm_length
        #     glVertex3fv(vert)
        #     glVertex3fv(vert + norm)
        #     glEnd()

    def clear(self):
        self.gl_lists = []

    def handle_input(self, e):
        if e.type == QUIT:
            self.on = False

        elif e.type == KEYDOWN and e.key == K_ESCAPE:
            self.on = False

        elif e.type == MOUSEBUTTONDOWN:
            if e.button == 4: self.zpos = max(1, self.zpos-1)
            elif e.button == 5: self.zpos += 1
            elif e.button == 1: self.rotate = True
            elif e.button == 3: self.move = True

        elif e.type == MOUSEBUTTONUP:
            if e.button == 1: self.rotate = False
            elif e.button == 3: self.move = False

        elif e.type == MOUSEMOTION:
            i, j = e.rel
            if self.rotate:
                self.rx += i
                self.ry += j
            if self.move:
                self.tx += i
                self.ty -= j

        if e.type == KEYDOWN:
            if e.key == K_g:
                self.draw_grid = not self.draw_grid

    def step(self, i):
        pass

    def main_loop(self):
        self.rotate = False
        self.move = False
        i = 0

        while self.on:
            self.clock.tick(15)
            self.step(i)

            for e in pygame.event.get():
                self.handle_input(e)

            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glLoadIdentity()

            # RENDER OBJECT
            glTranslate(self.tx/20., self.ty/20., - self.zpos)
            glRotate(self.ry, 1, 0, 0)
            glRotate(self.rx, 0, 1, 0)

            for gl_list in self.gl_lists:
                glCallList(gl_list)

            glLineWidth(1)
            if self.draw_grid:
                glCallList(G_OBJ_PLANE)

            pygame.display.flip()
            i += 1

class AnimationViewer(Viewer):
    def __init__(self, animation, view_size):
        super(AnimationViewer, self).__init__(view_size)

        self.frame = 0
        self.frame_lists = []
        self.animation_playing = False

        print('Loading Animation')

        for i, frame in enumerate(animation):
            self.start_draw()

            print(i, 'n_verts=', len(frame[0]['vertices']))

            for mesh in frame:
                self.build_compiled_gllist(mesh)

            self.frame_lists.append(self.gl_list)
            glEndList()
            self.gl_list = None

        self.gl_lists = [self.frame_lists[self.frame]]
        print('Finished Loading Animation')

    def handle_input(self, e):
        super(AnimationViewer, self).handle_input(e)

        if e.type == KEYDOWN:
            if e.key == K_RIGHT:
                if self.frame < len(self.frame_lists) - 1:
                    self.frame += 1
                    self.gl_lists = [self.frame_lists[self.frame]]

            elif e.key == K_LEFT:
                if self.frame > 0:
                    self.frame -= 1
                    self.gl_lists = [self.frame_lists[self.frame]]

            elif e.key == K_r:
                self.frame = 0
                self.gl_lists = [self.frame_lists[self.frame]]

            elif e.key == K_SPACE:
                self.animation_playing = not self.animation_playing

    def step(self, i):
        if self.animation_playing:
            self.rx += 1
            self.zpos += .25

        if self.animation_playing and self.frame < len(self.frame_lists) - 1:
            self.frame += 1
            self.gl_lists = [self.frame_lists[self.frame]]

