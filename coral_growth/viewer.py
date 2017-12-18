# Basic OBJ file viewer. needs objloader from:
#  http://www.pygame.org/wiki/OBJFileLoader
# LMB + move: rotate
# RMB + move: pan
# Scroll wheel: zoom in/out
import sys, pygame, math
from pygame.locals import *
import numpy as np
from pygame.constants import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import shutil
from coral_growth.primitive import make_plane, make_sphere, G_OBJ_PLANE, G_OBJ_SPHERE

from OpenGL.arrays import vbo
from OpenGL.raw.GL.ARB.vertex_array_object import glGenVertexArrays, \
                                                  glBindVertexArray
import string
import random
def rand_string(n):
    opts = string.ascii_uppercase + string.digits
    return ''.join(random.choice(opts) for _ in range(n))

class Viewer(object):
    def __init__(self, view_size=(800, 600), background=(0.7, 0.7, 0.7, 0.0)):
        # self.bounds = bounds
        self.on = True
        self.animation = None
        self.animation_playing = False
        self.draw_grid = True

        pygame.init()
        glutInit()
        self.width = view_size[0]
        self.height = view_size[1]
        viewport = view_size

        self.surface = pygame.display.set_mode(view_size, OPENGL | DOUBLEBUF )
        # glEnable(GL_DEPTH_CLAMP)

        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHTING)


        ambient = .2
        diffuse = .5
        # glLightfv(GL_LIGHT0, GL_POSITION, [0,0, 100, 0.0])
        glLightfv(GL_LIGHT0, GL_POSITION,  (-40, 200, 100, 0.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (ambient, ambient, ambient, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (diffuse, diffuse, diffuse, 1.0))
        # glLightfv(GL_LIGHT0, GL_SPECULAR, (foo, foo, foo, 1.0))

        # glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [.6, .6, .6, 1])
        # glLightfv(GL_LIGHT0, GL_SPOT_DIRECTION, GLfloat_3(0, 0, -1))

        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glEnable(GL_COLOR_MATERIAL)
        # glEnable(GL_MULTISAMPLE)

        # glDepthFunc(GL_LESS)

        glClearColor(*background)

        glShadeModel(GL_SMOOTH)
        glCullFace(GL_BACK)
        # glDisable( GL_CULL_FACE )
        # glPolygonMode ( GL_FRONT_AND_BACK, GL_LINE )

        self.clock = pygame.time.Clock()

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(90.0, self.width/float(self.height), 1, 100.0)
        glEnable(GL_DEPTH_TEST)
        glMatrixMode(GL_MODELVIEW)

        # Transparancy?
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_BLEND)

        glTranslated(-15, -15, -15)

        self.rx, self.ry = (0,0)
        self.tx, self.ty = (0,0)
        self.zpos = 10

        self.gl_lists = []

        make_plane(5)
        make_sphere(15)
        self.translation_matrix = np.identity(4)
        self.scaling_matrix = np.identity(4)

    def start_draw(self):
        self.gl_list = glGenLists(1)
        glNewList(self.gl_list, GL_COMPILE)

    def end_draw(self):
        glEndList()
        self.gl_lists.append(self.gl_list)
        self.gl_list = None

    def draw_mesh(self, mesh, offset_x=0, offset_y=0, offset_z=0):
        """this time, the vertices must be specified globally, and referenced by
        indices in order to use the list paradigm. vertices is a list of 3-vectors, and
        facets are dicts containing 'normal' (a 3-vector) 'vertices' (indices to the
        other argument) and 'color' (the color the triangle should be)."""

        # first flatten out the arrays:
        mesh['vertices'] += [ offset_x, offset_y, offset_z ]
        vertices = mesh['vertices'].flatten()
        normals  = mesh['vertice_normals'].flatten()
        findices = mesh['faces'].astype('uint32').flatten()
        eindices = mesh['edges'].astype('uint32').flatten()

        fcolors = mesh['vert_colors'].flatten()
        # ecolors = np.zeros_like(mesh['vert_colors']).flatten() + .5
        ecolors = fcolors - .1
        ecolors[ecolors <= 0] = 0

        # then convert to OpenGL / ctypes arrays:
        fvertices = (GLfloat * len(vertices))(*vertices)
        evertices = (GLfloat * len(vertices))(*(vertices + normals*.001))
        normals = (GLfloat * len(normals))(*normals)
        findices = (GLuint * len(findices))(*findices)
        eindices = (GLuint * len(eindices))(*eindices)
        fcolors = (GLfloat * len(fcolors))(*fcolors)
        ecolors = (GLfloat * len(ecolors))(*ecolors)

        glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, fvertices)
        glNormalPointer(GL_FLOAT, 0, normals)
        glColorPointer(3, GL_FLOAT, 0, fcolors)
        glDrawElements(GL_TRIANGLES, len(findices), GL_UNSIGNED_INT, findices)

        glColorPointer(3, GL_FLOAT, 0, ecolors)
        glVertexPointer(3, GL_FLOAT, 0, evertices)
        glDrawElements(GL_LINES, len(eindices), GL_UNSIGNED_INT, eindices)
        glPopClientAttrib()

    def draw_lines(self, lines, width=3, color=(0,0,0)):
        glLineWidth(width)

        glColor3f(*color)
        glBegin(GL_LINES)

        for p1, p2 in lines:
            glVertex3f(*p1)
            glVertex3f(*p2)

        glEnd()

    def draw_cube(self, x, y, z, s=1, color=(.5, .5, .5)):
        # glNewList(G_OBJ_CUBE, GL_COMPILE)
        glColor3f(*color)
        vertices = [[[-0.5, -0.5, -0.5], [-0.5, -0.5, 0.5], [-0.5, 0.5, 0.5], [-0.5, 0.5, -0.5]],
                    [[-0.5, -0.5, -0.5], [-0.5, 0.5, -0.5], [0.5, 0.5, -0.5], [0.5, -0.5, -0.5]],
                    [[0.5, -0.5, -0.5], [0.5, 0.5, -0.5], [0.5, 0.5, 0.5], [0.5, -0.5, 0.5]],
                    [[-0.5, -0.5, 0.5], [0.5, -0.5, 0.5], [0.5, 0.5, 0.5], [-0.5, 0.5, 0.5]],
                    [[-0.5, -0.5, 0.5], [-0.5, -0.5, -0.5], [0.5, -0.5, -0.5], [0.5, -0.5, 0.5]],
                    [[-0.5, 0.5, -0.5], [-0.5, 0.5, 0.5], [0.5, 0.5, 0.5], [0.5, 0.5, -0.5]]]

        vertices = np.array(vertices)
        vertices *= s
        vertices[:, :, 0] += x
        vertices[:, :, 1] += y
        vertices[:, :, 2] += z

        normals = [(-1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, -1.0, 0.0), (0.0, 1.0, 0.0)]

        glBegin(GL_QUADS)
        for i in range(6):
            glNormal3f(normals[i][0], normals[i][1], normals[i][2])
            for j in range(4):
                glVertex3f(vertices[i][j][0], vertices[i][j][1], vertices[i][j][2])
        glEnd()
        # glEndList()

    def draw_text(self, x, y, text, r=0.0, g=0.0, b=0.0):
        y = self.height - (y + 24)
        glWindowPos2f(x, y)
        glColor3f(r, g, b)

        for c in text:
            if c=='\n':
                glRasterPos2f(x, y-0.24)
            else:
                glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(c))

    def draw_sphere(self, p, r, color):
        glPushMatrix()

        self.translation_matrix[0, 3] = p[0]
        self.translation_matrix[1, 3] = p[1]
        self.translation_matrix[2, 3] = p[2]

        self.translation_matrix[0, 0] = r
        self.translation_matrix[1, 1] = r
        self.translation_matrix[2, 2] = r
        self.translation_matrix[3, 3] = 1

        glMultMatrixf(np.transpose(self.translation_matrix))
        # glMultMatrixf(self.scaling_matrix)

        glColor3f(color[0], color[1], color[2])

        emmision = False

        # if emmision:  # emit light if the node is selected
        #     glMaterialfv(GL_FRONT, GL_EMISSION, [0.3, 0.3, 0.3])

        glCallList(G_OBJ_SPHERE)

        # if emmision:
        #     glMaterialfv(GL_FRONT, GL_EMISSION, [0.0, 0.0, 0.0])

        glPopMatrix()


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

    def draw_step(self):
        pass

    def main_loop(self):
        self.rotate = False
        self.move = False
        i = 0

        while self.on:
            self.clock.tick(30)
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

            self.draw_step()

            pygame.display.flip()
            i += 1

    def save(self, path):
        pygame.image.save(self.surface, path)

from cymesh.mesh import Mesh
import numpy as np
from colorsys import hsv_to_rgb
import re

class AnimationViewer(Viewer):
    def __init__(self, files, view_size, color=(0.7, 0.7, 0.7, 0.0)):
        super(AnimationViewer, self).__init__(view_size, color)
        print('Loading Animation')

        self.frame = 0
        self.n_frames = len(files)
        self.animation_playing = False
        self.saving = False
        self.view = 0

        self.n_views = None
        self.view_lists = None#

        # dir = 'tmp'
        # if os.path.exists(dir):
            # shutil.rmtree(dir)
        # os.makedirs(dir)

        get_generation = re.compile('out_.*?\/([0-9]+)\/')

        for fi, file in enumerate(files):
            try:
                generation = int(get_generation.search(file).groups()[0])
            except AttributeError:
                generation = None

            # gidx = generations.index(generation)
            # step_x = 3
            # offset_x = (-len(generations)//2 + gidx) * step_x

            """ Read the file and store the colors.
            """
            raw_mesh = Mesh.from_obj(file)
            mesh = raw_mesh.export()
            mesh['vert_colors'] = np.zeros((mesh['vertices'].shape))
            polyp_data = []
            coral_data = {}

            for line in open(file, 'r').read().splitlines():
                if line.startswith("#attr"):
                    line = line.split(':')
                    coral_data[line[1]] = line[2]

                elif line.startswith("#coral"):
                    header = line.split(' ')[1:]

                    if self.n_views is None:
                        self.n_views = len(header) -1

                        self.view_lists = [[] for _ in range(self.n_views)]
                        self.view_names = ['morphogens'] + header[:-2]
                        print(header)
                        print(self.view_names)

                elif line.startswith('c'):
                    d = line.split(' ')[1:]
                    for i in range(self.n_views+1):
                        d[i] = float(d[i]) if '.' in d[i] else int(d[i])

                    polyp_data.append( d )

            assert self.n_views is not None

            int_colors = [hsv_to_rgb((i/float(8)), 1.0, 1.0) for i in range(8)]

            """ Now compile mesh for each view given color data and mesh data.
            """
            radius = float(coral_data['polyp_size'])
            # radii = []
            # for vert in raw_mesh.verts:
            #     edges = vert.edges()
            #     radii.append(min(edge.length() for edge in edges))
            #     # radii.append(sum(edge.length() for edge in edges) / len(edges))

            for view_idx in range(self.n_views):
                gl_list = glGenLists(1)
                glNewList(gl_list, GL_COMPILE)

                for polyp_idx, data in enumerate(polyp_data):
                    if view_idx == 0: #hardcode in 2 morphogens.
                        color = ( 0, data[-2], data[-1] )
                    else:
                        d = data[ view_idx - 1 ]
                        if isinstance(d, int):
                            color = int_colors[d]
                        # if (view_idx-1) in int_colors:
                            # print('int', int_colors, d)
                            # color = int_colors[view_idx-1][d]
                        else:
                            color = ( d, d, d )


                    # self.draw_sphere(mesh['vertices'][polyp_idx], radius, color)

                    mesh['vert_colors'][polyp_idx] = color

                self.draw_mesh(mesh)

                if generation is not None:
                    self.draw_text( 30, 30, 'Generation %i' % generation )

                self.view_lists[ view_idx ].append([ gl_list ])
                glEndList()

            print(fi, 'n_verts=', len(mesh['vertices']))

        self.gl_lists = self.view_lists[ self.view ][ self.frame ]
        print('Finished Loading Animation')

    def draw_step(self):
        self.draw_text( 30, 60, 'View: '+self.view_names[self.view])

    def handle_input(self, e):
        super(AnimationViewer, self).handle_input(e)

        if e.type == KEYDOWN:
            if e.key == K_RIGHT:
                if self.frame < self.n_frames - 1:
                    self.frame += 1
                    self.gl_lists = self.view_lists[self.view][self.frame]

            elif e.key == K_LEFT:
                if self.frame > 0:
                    self.frame -= 1
                    self.gl_lists = self.view_lists[self.view][self.frame]

            elif e.key == K_r:
                self.frame = 0
                self.gl_lists = self.view_lists[self.view][self.frame]

            elif e.key == K_s:
                self.save(rand_string(4)+'.jpg')

            elif e.key == K_f:
                self.saving = not self.saving
                print('Set saving=', self.saving)

            elif e.key == K_SPACE:
                print('Animation Playing', 'saving=', self.saving)
                self.animation_playing = not self.animation_playing

            else:
                if e.key == K_1:
                    self.view = 0
                elif e.key == K_2:
                    self.view = 1
                elif e.key == K_3:
                    self.view = 2
                elif e.key == K_4:
                    self.view = 3
                elif e.key == K_5:
                    self.view = 4
                elif e.key == K_6:
                    self.view = 5
                elif e.key == K_7:
                    self.view = 6

                self.view = min(self.view, self.n_views-1)

                print('switched to view', self.view_names[self.view])
                self.gl_lists = self.view_lists[self.view][self.frame]

    def step(self, i):
        if self.animation_playing:
            # Do two rotation steps for every growth step.
            # if i % 1 == 0:
            if self.frame < self.n_frames - 1:
                self.frame += 1
                self.gl_lists = self.view_lists[self.view][self.frame]

            if self.saving:
                self.save('tmp/%04d.jpg'%i)

            self.rx += .6




