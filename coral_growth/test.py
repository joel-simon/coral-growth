import sys
from OpenGL.GLUT import *
from OpenGL.GL import *

ESCAPE = '\033'

PROMPT = ("Press keys '1' - '0' to start callbacks",
          "Press ESCAPE to exit.")

global AllTimers
AllTimers = []

class TimerCBOwner:
    def __init__(self, name, delay, repeat):
        global AllTimers
        self.name   = name
        self.delay  = delay
        self.repeat = repeat
        self.state  = "WAITING"
        glutTimerFunc(self.delay, self.cb, 0)
        AllTimers += (self,)
        glutPostRedisplay()


    def getDescription(self):
        return "%s: %s"%(self.name, self.state)

    def cb(self, value):
        self.state = "CALL %d"%value
        if value + 1 == self.repeat:
             self.state += " (LAST!)"

        if value < self.repeat:
            glutTimerFunc(self.delay, self.cb, value+1)
        else:
            AllTimers.remove(self)

        glutPostRedisplay()

def keyboard(key, foo, bar):
    if key == ESCAPE:
        sys.exit()
    else:
        TimerCBOwner(key, 2000, 5)

def display():
    global AllTimers
    w = float(glutGet(GLUT_WINDOW_WIDTH))
    h = float(glutGet(GLUT_WINDOW_HEIGHT))
    glViewport(0, 0, int(w), int(h))
    glClearColor(0.0, 0.0, 0.0, 0.0)
    glClear(GL_COLOR_BUFFER_BIT)
    glColor4f(1.0, 1.0, 0.5, 1.0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glTranslate(-1.0, 1.0, 0.0)
    scale = 1.0/w
    glScale(scale, -scale*w/h, 1.0)
    glTranslate(1.0, 1.0, 0.0)
    y = 25.0
    for s in PROMPT:
        glRasterPos(40.0, y)
        y += 30.0
        for c in s:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))

    y = 100.0
    for t in AllTimers:
        glRasterPos(80.0, y)
        for c in t.getDescription():
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
        y += 30.0

    glutSwapBuffers()

def main():
    glutInit([])
    glutInitWindowSize(640, 480)
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE)
    glutCreateWindow("glutTimerFunc test case")
    glutDisplayFunc(display)
    glutKeyboardFunc(keyboard)
    glutMainLoop()

main()
