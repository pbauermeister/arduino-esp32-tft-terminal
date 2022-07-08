import datetime
import math

from lib import *
import config
from app import App, TimeEscaper

class Cube(App):
    def __init__(self, board):
        super().__init__(board)
        if self.board.wait_no_button(2): return
        self.board.begin_auto_read_buttons()

    def run(self):
        """Rotating Cube, by Al Sweigart al@inventwithpython.com A rotating
        cube animation. Press Ctrl-C to stop.  This code is available
        at https://nostarch.com/big-book-small-python-programming
        Tags: large, artistic, math

        https://inventwithpython.com/bigbookpython/project62.html"""

        # Set up the constants:
        SIZE = min(config.WIDTH, config.HEIGHT)
        OFFSET_X = (config.WIDTH-SIZE) // 2
        OFFSET_Y = (config.HEIGHT-SIZE) // 2
        SCALEX = SCALEY = SIZE // 4

        TRANSLATEX = (config.WIDTH - 4) // 2
        TRANSLATEY = (config.HEIGHT - 4) // 2 + 4

        # (!) Try changing this to '#' or '*' or some other character:
        LINE_CHAR = chr(9608)  # Character 9608 is a solid block.

        # (!) Try setting two of these values to zero to rotate the cube only
        # along a single axis:
        X_ROTATE_SPEED = 0.03
        Y_ROTATE_SPEED = 0.08
        Z_ROTATE_SPEED = 0.13

        # This program stores XYZ coordinates in lists, with the X coordinate
        # at index 0, Y at 1, and Z at 2. These constants make our code more
        # readable when accessing the coordinates in these lists.
        X = 0
        Y = 1
        Z = 2

        i = 0

        def line(x1, y1, x2, y2, c):
            self.command(f'drawLine {x1+.5} {y1+.5} {x2+.5} {y2+.5} {c}')

        def rotatePoint(x, y, z, ax, ay, az):
            """Returns an (x, y, z) tuple of the x, y, z arguments rotated.

            The rotation happens around the 0, 0, 0 origin by angles
            ax, ay, az (in radians).
                Directions of each axis:
                 -y
                  |
                  +-- +x
                 /
                +z
            """

            # Rotate around x axis:
            rotatedX = x
            rotatedY = (y * math.cos(ax)) - (z * math.sin(ax))
            rotatedZ = (y * math.sin(ax)) + (z * math.cos(ax))
            x, y, z = rotatedX, rotatedY, rotatedZ

            # Rotate around y axis:
            rotatedX = (z * math.sin(ay)) + (x * math.cos(ay))
            rotatedY = y
            rotatedZ = (z * math.cos(ay)) - (x * math.sin(ay))
            x, y, z = rotatedX, rotatedY, rotatedZ

            # Rotate around z axis:
            rotatedX = (x * math.cos(az)) - (y * math.sin(az))
            rotatedY = (x * math.sin(az)) + (y * math.cos(az))
            rotatedZ = z

            # False perspective
            k = 1 if alt else 1.5**z *.6 + .25

            return (rotatedX*k, rotatedY*k, rotatedZ)


        def adjustPoint(point):
            """Adjusts the 3D XYZ point to a 2D XY point fit for displaying on
            the screen. This resizes this 2D point by a scale of SCALEX and
            SCALEY, then moves the point by TRANSLATEX and TRANSLATEY."""
            return (int(point[X] * SCALEX + TRANSLATEX),
                    int(point[Y] * SCALEY + TRANSLATEY))

        def cube(rotatedCorners, xRotation, yRotation, zRotation, c):
            for i in range(len(CUBE_CORNERS)):
                x = CUBE_CORNERS[i][X]
                y = CUBE_CORNERS[i][Y]
                z = CUBE_CORNERS[i][Z]
                rotatedCorners[i] = rotatePoint(x, y, z, xRotation,
                    yRotation, zRotation)

            # Find farthest point to omit hidden edges
            minZ = 0
            for fromCornerIndex, toCornerIndex in CUBE_EDGES:
                fromPoint = rotatedCorners[fromCornerIndex]
                toPoint = rotatedCorners[toCornerIndex]
                minZ = min(minZ, fromPoint[Z])
                minZ = min(minZ, toPoint[Z])

            # Get the points of the cube lines:
            for fromCornerIndex, toCornerIndex in CUBE_EDGES:
                fromPoint = rotatedCorners[fromCornerIndex]
                toPoint = rotatedCorners[toCornerIndex]
                fromX, fromY = adjustPoint(fromPoint)
                toX, toY = adjustPoint(toPoint)
                if alt:
                    if fromPoint[Z] == minZ or toPoint[Z] == minZ:
                        continue  # bound to farthest point: hidden edge
                line(fromX, fromY, toX, toY, c)

        """CUBE_CORNERS stores the XYZ coordinates of the corners of a cube.
        The indexes for each corner in CUBE_CORNERS are marked in this diagram:
              0------1
             /|     /|
            2------3 |
            | 4----|-5
            |/     |/
            6------7
        """
        CUBE_CORNERS = [[-1, -1, -1], # Point 0
                        [ 1, -1, -1], # Point 1
                        [-1, -1,  1], # Point 2
                        [ 1, -1,  1], # Point 3
                        [-1,  1, -1], # Point 4
                        [ 1,  1, -1], # Point 5
                        [-1,  1,  1], # Point 6
                        [ 1,  1,  1]] # Point 7
        CUBE_EDGES = (
            (0, 1), (1, 3), (3, 2), (2, 0),
            (0, 4), (1, 5), (2, 6), (3, 7),
            (4, 5), (5, 7), (7, 6), (6, 4),
        )

        # rotatedCorners stores the XYZ coordinates from CUBE_CORNERS after
        # they've been rotated by rx, ry, and rz amounts:
        rotatedCorners = [None, None, None, None, None, None, None, None]
        # Rotation amounts for each axis:
        xRotation = 0.0
        yRotation = 0.0
        zRotation = 0.0

        previous = None
        undraw = False
        escaper = TimeEscaper(self)
        start = datetime.datetime.now()
        while True:  # Main program loop.
            if self.board.auto_read_buttons(): break

            alt = (i%50) > 25
            if not undraw:
                self.command('clearDisplay')

            if previous and undraw:
                xRotation, yRotation, zRotation = previous
                cube(rotatedCorners, xRotation, yRotation, zRotation, 0)

            # Rotate the cube along different axes by different amounts:
            xRotation += X_ROTATE_SPEED
            yRotation += Y_ROTATE_SPEED
            zRotation += Z_ROTATE_SPEED
            cube(rotatedCorners, xRotation, yRotation, zRotation, 1)

            if undraw:
                previous = xRotation, yRotation, zRotation

            if escaper.check(): break
            self.command('display')
            i += 1

        if 'R' in self.board.end_auto_read_buttons(): return True
