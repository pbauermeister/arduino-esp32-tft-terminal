import datetime
import math
import time
from dataclasses import dataclass

import config
from app import App, TimeEscaper
from lib.board import Board

ISOMETRIC = True
BOUNCE_SIZE = True


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


PointIndex = int


@dataclass
class Edge:
    a: PointIndex
    b: PointIndex


EdgeIndex = int


@dataclass
class Face:
    edges: tuple[EdgeIndex, EdgeIndex, EdgeIndex, EdgeIndex]
    normal: Edge


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
        SCALE = SIZE // 4

        TRANSLATEX = (config.WIDTH - 4) // 2 + int(config.WIDTH / 8)
        TRANSLATEY = (config.HEIGHT - 4) // 2 + 4 + 8

        # (!) Try changing this to '#' or '*' or some other character:
        LINE_CHAR = chr(9608)  # Character 9608 is a solid block.

        # (!) Try setting two of these values to zero to rotate the cube only
        # along a single axis:
        K = 0.7
        X_ROTATE_SPEED = 0.03 * K
        Y_ROTATE_SPEED = 0.08 * K
        Z_ROTATE_SPEED = 0.13 * K

        LINES_RGB = 96, 255, 96
        TEXT_RGB = int(96 / 2), int(255 / 2), int(96 / 2)

        hue = 0
        mode = 0

        def line(x1: float, y1: float, x2: float, y2: float, c: int) -> None:
            self.gfx.draw_line(
                int(x1 + 0.5), int(y1 + 0.5), int(x2 + 0.5), int(y2 + 0.5), c
            )

        def triangle(u: Point2, v: Point2, w: Point2, c: int) -> None:
            self.gfx.fill_triangle(
                int(u.x + 0.5),
                int(u.y + 0.5),
                int(v.x + 0.5),
                int(v.y + 0.5),
                int(w.x + 0.5),
                int(w.y + 0.5),
                c,
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
            k = 1 if ISOMETRIC else 1.5**z * 0.6 + 0.25

            return Point(rotated_x * k, rotated_y * k, rotated_z)

        def adjust_point(p: Point) -> Point2:
            """Adjusts the 3D XYZ point to a 2D XY point fit for displaying on
            the screen. This resizes this 2D point by a scale of SCALEX and
            SCALEY, then moves the point by TRANSLATEX and TRANSLATEY."""
            scale = (
                SCALE * (0.8 + math.sin(hue / 360 * math.pi * 2) * 0.2)
                if BOUNCE_SIZE
                else SCALE
            )
            return Point2(int(p.x * scale + TRANSLATEX), int(p.y * scale + TRANSLATEY))

        def cube(
            corners: list[Point], rotation: Vector, lines: list[Line], clear: bool
        ) -> None:
            # apply rotations
            for i, point in enumerate(CUBE_CORNERS):
                corners[i] = rotate_point(point, rotation)

            if clear:
                self.gfx.clear()

            match mode:
                case 0:
                    title = "Wireframe"
                    cube_wireframe(corners, lines, False)
                case 1:
                    title = "Opaque"
                    cube_wireframe(corners, lines, True)
                case 2:
                    title = "Shaded"
                    cube_shaded(corners, False, False)
                case 3:
                    title = "No flicker"
                    cube_shaded(corners, True, False)
                case 4:
                    title = "Contour"
                    cube_shaded(corners, True, True)

            if clear or mode == 2:
                self.gfx.set_text_color(*TEXT_RGB)
                self.gfx.home()
                self.gfx.set_text_size(1, 1.5)
                self.gfx.print(title)

        def cube_wireframe(
            corners: list[Point],
            lines: list[Line],
            hidden: bool,
        ) -> None:

            # Erase old
            for l in lines:
                line(l.x1, l.y1, l.x2, l.y2, 0)
            lines.clear()

            # Find farthest point to omit hidden edges
            min_z: float = 0
            if hidden:
                for edge in CUBE_EDGES:
                    from_corner_index, to_corner_index = edge.a, edge.b
                    from_point = corners[from_corner_index]
                    to_point = corners[to_corner_index]
                    min_z = min(min_z, from_point.z)
                    min_z = min(min_z, to_point.z)

            # Get the points of the cube lines:
            for edge in CUBE_EDGES:
                from_corner_index, to_corner_index = edge.a, edge.b
                from_point = corners[from_corner_index]
                to_point = corners[to_corner_index]
                src = adjust_point(from_point)
                dst = adjust_point(to_point)
                if ISOMETRIC and hidden:
                    if from_point.z == min_z or to_point.z == min_z:
                        continue  # bound to farthest point: hidden edge
                lines.append(Line(src.x, src.y, dst.x, dst.y))

            # Draw
            self.gfx.set_fg_color(*LINES_RGB)
            for l in lines:
                line(l.x1, l.y1, l.x2, l.y2, 1)

        self.last_x0 = self.last_x1 = self.last_y0 = self.last_y1 = 0
        self.has_last = False

        def cube_shaded(
            corners: list[Point],
            smart_erase: bool,
            contour: bool,
        ) -> None:

            def extrema(
                point: Point2,
                top: Point2,
                bottom: Point2,
                left: Point2,
                right: Point2,
            ) -> tuple[Point2, Point2, Point2, Point2]:
                if point.y < top.y:
                    top = point
                if point.y > bottom.y:
                    bottom = point
                if point.x < left.x:
                    left = point
                if point.x > right.x:
                    right = point
                return top, bottom, left, right

            # determine visible faces
            visible_faces_indices: set[int] = set()
            value_by_face_index: dict[int, float] = {}
            for i, face in enumerate(CUBE_FACES):
                src = corners[face.normal.a]
                dst = corners[face.normal.b]
                dx, dy, dz = dst.x - src.x, dst.y - src.y, dst.z - src.z
                if dz > 0:
                    visible_faces_indices.add(i)
                    value_by_face_index[i] = (dz + dx) / 3

            # determine outer edges
            usage_by_edge_index: dict[int, int] = {}
            for i in visible_faces_indices:
                face = CUBE_FACES[i]
                for j in face.edges:
                    usage_by_edge_index.setdefault(j, 0)
                    usage_by_edge_index[j] += 1
            outer_edges_indices = [k for k, v in usage_by_edge_index.items() if v == 1]

            # find enclosing rectangle
            outer_points_ixs: set[int] = set()
            for i in outer_edges_indices:
                edge = CUBE_EDGES[i]
                outer_points_ixs.add(edge.a)
                outer_points_ixs.add(edge.b)
            outer_points_2d: list[Point2] = []
            for ix in outer_points_ixs:
                outer_points_2d.append(adjust_point(corners[ix]))
            top = bottom = left = right = outer_points_2d[0]
            for point in outer_points_2d[1:]:
                top, bottom, left, right = extrema(point, top, bottom, left, right)
            x0, y0 = left.x, top.y
            x1, y1 = right.x, bottom.y
            top_left = Point2(x0, y0)
            top_right = Point2(x1, y0)
            bot_left = Point2(x0, y1)
            bot_right = Point2(x1, y1)
            center = Point2(TRANSLATEX, TRANSLATEY)

            if smart_erase:
                # erase frame (between enclosing rectangle and last enclosing rectangle)
                if self.has_last:
                    if self.last_x0 < x0:
                        u0, u1 = self.last_x0, x0
                        v0 = min(self.last_y0, y0)
                        v1 = max(self.last_y1, y1)
                        self.gfx.fill_rect(u0, v0, u1 - u0, v1 - v0, 0)
                    if self.last_x1 > x1:
                        u0, u1 = x1, self.last_x1
                        v0 = min(self.last_y0, y0)
                        v1 = max(self.last_y1, y1)
                        self.gfx.fill_rect(u0, v0, u1 - u0, v1 - v0, 0)
                    if self.last_y0 < y0:
                        v0, v1 = self.last_y0, y0
                        u0 = min(self.last_x0, x0)
                        u1 = max(self.last_x1, x1)
                        self.gfx.fill_rect(u0, v0, u1 - u0, v1 - v0, 0)
                    if self.last_y1 > y1:
                        v0, v1 = y1, self.last_y1
                        u0 = min(self.last_x0, x0)
                        u1 = max(self.last_x1, x1)
                        self.gfx.fill_rect(u0, v0, u1 - u0, v1 - v0, 0)
                self.has_last = True
                self.last_x0, self.last_y0, self.last_x1, self.last_y1 = (
                    x0 - 1,
                    y0 - 1,
                    x1 + 1,
                    y1 + 1,
                )

                # erase outer edges to enclosing rectangle
                for i in outer_edges_indices:
                    edge = CUBE_EDGES[i]
                    from_point_ix, to_point_ix = edge.a, edge.b
                    from_point = corners[from_point_ix]
                    to_point = corners[to_point_ix]
                    src2 = adjust_point(from_point)
                    dst2 = adjust_point(to_point)

                    # right
                    if src2.x == x1 and src2.y < dst2.y:
                        triangle(src2, dst2, bot_right, 0)
                    elif dst2.x == x1 and src2.y > dst2.y:
                        triangle(src2, dst2, bot_right, 0)

                    elif src2.x == x1 and src2.y > dst2.y:
                        triangle(src2, dst2, top_right, 0)
                    elif dst2.x == x1 and src2.y < dst2.y:
                        triangle(src2, dst2, top_right, 0)

                    # left
                    elif src2.x == x0 and src2.y < dst2.y:
                        triangle(src2, dst2, bot_left, 0)
                    elif dst2.x == x0 and src2.y > dst2.y:
                        triangle(src2, dst2, bot_left, 0)

                    elif src2.x == x0 and src2.y > dst2.y:
                        triangle(src2, dst2, top_left, 0)
                    elif dst2.x == x0 and src2.y < dst2.y:
                        triangle(src2, dst2, top_left, 0)

                    # top
                    if src2.y == y0 and src2.x < dst2.x:
                        triangle(src2, dst2, top_right, 0)
                    elif dst2.y == y0 and src2.x > dst2.x:
                        triangle(src2, dst2, top_right, 0)

                    if src2.y == y0 and src2.x > dst2.x:
                        triangle(src2, dst2, top_left, 0)
                    elif dst2.y == y0 and src2.x < dst2.x:
                        triangle(src2, dst2, top_left, 0)

                    # bottom
                    if src2.y == y1 and src2.x < dst2.x:
                        triangle(src2, dst2, bot_right, 0)
                    elif dst2.y == y1 and src2.x > dst2.x:
                        triangle(src2, dst2, bot_right, 0)

                    if src2.y == y1 and src2.x > dst2.x:
                        triangle(src2, dst2, bot_left, 0)
                    elif dst2.y == y1 and src2.x < dst2.x:
                        triangle(src2, dst2, bot_left, 0)
            else:
                self.gfx.clear()

            # draw visible faces
            for i in visible_faces_indices:
                face = CUBE_FACES[i]
                point_indices: set[int] = set()
                for j in face.edges:
                    edge = CUBE_EDGES[j]
                    point_indices.add(edge.a)
                    point_indices.add(edge.b)
                    usage_by_edge_index.setdefault(j, 0)
                    usage_by_edge_index[j] += 1
                points = [adjust_point(corners[k]) for k in point_indices]
                a, b, c, d = points[0], points[1], points[2], points[3]

                mag2 = 50
                v = int(value_by_face_index[i] * mag2 + mag2)
                rgb = self.gfx.hsv_to_rgb(hue, 60, v)
                self.gfx.set_fg_color(*rgb)
                triangle(a, b, c, 1)
                triangle(b, c, d, 1)

            # draw contour
            if contour:
                self.gfx.set_fg_color(*LINES_RGB)
                for i in outer_edges_indices:
                    edge = CUBE_EDGES[i]
                    from_point_ix, to_point_ix = edge.a, edge.b
                    from_point = corners[from_point_ix]
                    to_point = corners[to_point_ix]
                    src2 = adjust_point(from_point)
                    dst2 = adjust_point(to_point)
                    self.gfx.draw_line(src2.x, src2.y, dst2.x, dst2.y, 1)

            # done
            self.gfx.set_fg_color(*LINES_RGB)

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

        CUBE_EDGES: tuple[
            Edge, Edge, Edge, Edge, Edge, Edge, Edge, Edge, Edge, Edge, Edge, Edge
        ] = (
            Edge(0, 1),  # edge 0
            Edge(1, 3),  # edge 1
            Edge(3, 2),  # edge 2
            Edge(2, 0),  # edge 3
            Edge(0, 4),  # edge 4
            Edge(1, 5),  # edge 5
            Edge(2, 6),  # edge 6
            Edge(3, 7),  # edge 7
            Edge(4, 5),  # edge 8
            Edge(5, 7),  # edge 9
            Edge(7, 6),  # edge 10
            Edge(6, 4),  # edge 11
        )

        CUBE_FACES: tuple[Face, Face, Face, Face, Face, Face] = (
            Face((0, 1, 2, 3), Edge(4, 0)),
            Face((5, 9, 7, 1), Edge(0, 1)),
            Face((2, 7, 10, 6), Edge(0, 2)),
            Face((4, 11, 6, 3), Edge(1, 0)),
            Face((0, 5, 8, 4), Edge(2, 0)),
            Face((8, 9, 10, 11), Edge(0, 4)),
        )

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
        clear = True
        nb_modes = 5
        hue_step = 8 if config.once else 5

        while True:  # Main program loop.
            btns = self.board.auto_read_buttons()
            if 'R' in btns:
                return True
            if 'A' in btns:
                return True
            if 'B' in btns:
                escaper.retrigger()
                self.board.wait_button_up(0)
                continue
            if 'C' in btns:
                escaper.retrigger()
                mode = (mode + 1) % nb_modes
                clear = True
                hue = 0
                self.board.wait_button_up(0)

            if not config.once and escaper.check():
                return False

            # self.gfx.clear()

            # Rotate the cube along different axes by different amounts:
            rotation.x += X_ROTATE_SPEED
            rotation.y += Y_ROTATE_SPEED
            rotation.z += Z_ROTATE_SPEED

            # Compute, erase old and display new
            cube(rotated_corners, rotation, lines, clear)
            self.gfx.display()
            clear = False

            new_hue = (hue + hue_step) % 360
            if new_hue < hue:
                mode = (mode + 1) % nb_modes
                clear = True
                #
                if mode == 0 and config.once:
                    return False
            hue = new_hue
