import datetime
import math
from dataclasses import dataclass

import config
from app import App, TimeEscaper
from lib.board import Board

ISOMETRIC = True


@dataclass
class Point:
    x: float
    y: float
    z: float


@dataclass
class Vector:
    x: float
    y: float
    z: float


@dataclass
class Point2:
    x: int
    y: int


@dataclass
class Line:
    x1: int
    y1: int
    x2: int
    y2: int


class Cube(App):
    def __init__(self, board: Board):
        super().__init__(board, auto_read=True)

    def _run(self) -> bool:
        """Rotating Cube, by Al Sweigart al@inventwithpython.com A rotating
        cube animation. Press Ctrl-C to stop.  This code is available
        at https://nostarch.com/big-book-small-python-programming
        Tags: large, artistic, math

        https://inventwithpython.com/bigbookpython/project62.html"""

        # Set up the constants:
        SIZE = min(config.WIDTH, config.HEIGHT)
        OFFSET_X = (config.WIDTH - SIZE) // 2
        OFFSET_Y = (config.HEIGHT - SIZE) // 2
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

        def line(x1: float, y1: float, x2: float, y2: float, c: int) -> None:
            self.gfx.draw_line(
                int(x1 + 0.5), int(y1 + 0.5), int(x2 + 0.5), int(y2 + 0.5), c
            )

        def rotate_point(p: Point, a: Vector) -> Point:
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
            rotated_x = p.x
            rotated_y = (p.y * math.cos(a.x)) - (p.z * math.sin(a.x))
            rotated_z = (p.y * math.sin(a.x)) + (p.z * math.cos(a.x))
            x, y, z = rotated_x, rotated_y, rotated_z

            # Rotate around y axis:
            rotated_x = (z * math.sin(a.y)) + (x * math.cos(a.y))
            rotated_y = y
            rotated_z = (z * math.cos(a.y)) - (x * math.sin(a.y))
            x, y, z = rotated_x, rotated_y, rotated_z

            # Rotate around z axis:
            rotated_x = (x * math.cos(a.z)) - (y * math.sin(a.z))
            rotated_y = (x * math.sin(a.z)) + (y * math.cos(a.z))
            rotated_z = z

            # False perspective
            k = 1 if ISOMETRIC else 1.5 ** z * 0.6 + 0.25

            return Point(rotated_x * k, rotated_y * k, rotated_z)

        def adjust_point(p: Point) -> Point2:
            """Adjusts the 3D XYZ point to a 2D XY point fit for displaying on
            the screen. This resizes this 2D point by a scale of SCALEX and
            SCALEY, then moves the point by TRANSLATEX and TRANSLATEY."""
            return Point2(
                int(p.x * SCALEX + TRANSLATEX), int(p.y * SCALEY + TRANSLATEY)
            )

        def cube(corners: list[Point], rotation: Vector, lines: list[Line]) -> None:
            # apply rotations
            for i, point in enumerate(CUBE_CORNERS):
                corners[i] = rotate_point(point, rotation)

            # Find farthest point to omit hidden edges
            min_z: float = 0
            for from_corner_index, to_corner_index in CUBE_EDGES:
                from_point = corners[from_corner_index]
                to_point = corners[to_corner_index]
                min_z = min(min_z, from_point.z)
                min_z = min(min_z, to_point.z)

            # Get the points of the cube lines:
            for from_corner_index, to_corner_index in CUBE_EDGES:
                from_point = corners[from_corner_index]
                to_point = corners[to_corner_index]
                src = adjust_point(from_point)
                dst = adjust_point(to_point)
                if ISOMETRIC:
                    if from_point.z == min_z or to_point.z == min_z:
                        continue  # bound to farthest point: hidden edge
                lines.append(Line(src.x, src.y, dst.x, dst.y))

        """CUBE_CORNERS stores the XYZ coordinates of the corners of a cube.
        The indexes for each corner in CUBE_CORNERS are marked in this diagram:
              0------1
             /|     /|
            2------3 |
            | 4----|-5
            |/     |/
            6------7
        """

        CUBE_CORNERS: list[Point] = [
            Point(-1, -1, -1),  # Point 0
            Point(+1, -1, -1),  # Point 1
            Point(-1, -1, +1),  # Point 2
            Point(+1, -1, +1),  # Point 3
            Point(-1, +1, -1),  # Point 4
            Point(+1, +1, -1),  # Point 5
            Point(-1, +1, +1),  # Point 6
            Point(+1, +1, +1),  # Point 7
        ]

        CUBE_EDGES: list[tuple[int, int]] = [
            (0, 1),  # edge 0
            (1, 3),  # edge 1
            (3, 2),  # edge 2
            (2, 0),  # edge 3
            (0, 4),  # edge 4
            (1, 5),  # edge 5
            (2, 6),  # edge 6
            (3, 7),  # edge 7
            (4, 5),  # edge 8
            (5, 7),  # edge 9
            (7, 6),  # edge 10
            (6, 4),  # edge 11
        ]

        # rotatedCorners stores the XYZ coordinates from CUBE_CORNERS after
        # they've been rotated by rx, ry, and rz amounts:
        unset = Point(0, 0, 0)
        rotated_corners: list[Point] = [
            unset,
            unset,
            unset,
            unset,
            unset,
            unset,
            unset,
            unset,
        ]
        # Rotation amounts for each axis:
        rotation = Vector(0, 0, 0)

        previous: Vector | None = None
        escaper = TimeEscaper(self)
        start = datetime.datetime.now()
        # self.gfx.reset()

        lines: list[Line] = []
        while True:  # Main program loop.
            btns = self.board.auto_read_buttons()
            if 'R' in btns:
                return True
            if btns:
                return False
            if escaper.check():
                return False

            # self.gfx.clear()

            # Rotate the cube along different axes by different amounts:
            rotation.x += X_ROTATE_SPEED
            rotation.y += Y_ROTATE_SPEED
            rotation.z += Z_ROTATE_SPEED

            # Erase old
            for l in lines:
                line(l.x1, l.y1, l.x2, l.y2, 0)

            # Compute and display new
            lines.clear()
            cube(rotated_corners, rotation, lines)
            for l in lines:
                line(l.x1, l.y1, l.x2, l.y2, 1)
            self.gfx.display()
