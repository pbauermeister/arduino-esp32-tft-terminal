from __future__ import annotations
from dataclasses import dataclass

import random
from itertools import combinations
from typing import Any, Generator

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import animation
from numpy.typing import NDArray

import config
from app import App, Sprite, TimeEscaper
from lib.board import Board
from lib.gfx import Gfx


@dataclass
class Circle:
    x: float
    y: float
    r: float
    hit: bool = False

    @staticmethod
    def create_from(other: Circle) -> Circle:
        return Circle(other.x, other.y, other.r, other.hit)


class Particle:
    """A class representing a two-dimensional particle."""

    def __init__(self, x: float, y: float, vx: float, vy: float,
                 radius: float = 0.01) -> None:
        """Initialize the particle's position, velocity, and radius.

        Any key-value pairs passed in the styles dictionary will be passed
        as arguments to Matplotlib's Circle patch constructor.

        """

        self.r = np.array((x, y))
        self.v = np.array((vx, vy))
        self.radius = radius
        self.mass = self.radius**2

    # For convenience, map the components of the particle's position and
    # velocity vector onto the attributes x, y, vx and vy.
    @property
    def x(self) -> float:
        return self.r[0]  # type: ignore

    @x.setter
    def x(self, value: float) -> None:
        self.r[0] = value

    @property
    def y(self) -> float:
        return self.r[1]  # type: ignore

    @y.setter
    def y(self, value: float) -> None:
        self.r[1] = value

    @property
    def vx(self) -> float:
        return self.v[0]  # type: ignore

    @vx.setter
    def vx(self, value: float) -> None:
        self.v[0] = value

    @property
    def vy(self) -> float:
        return self.v[1]  # type: ignore

    @vy.setter
    def vy(self, value: float) -> None:
        self.v[1] = value

    def overlaps(self, other: Particle) -> bool:
        """Does the circle of this Particle overlap that of other?"""

        return bool(np.hypot(*(self.r - other.r)) < self.radius + other.radius)

    def draw(self) -> Circle:
        """Add this Particle's Circle patch to the Matplotlib Axes ax."""
        return Circle(self.r[0], self.r[1], self.radius)

    def advance(self, dt: float) -> None:
        """Advance the Particle's position forward in time by dt."""

        self.r += self.v * dt


class Simulation:
    """A class for a simple hard-circle molecular dynamics simulation.

    The simulation is carried out on a square domain: 0 <= x < 1, 0 <= y < 1.

    """

    ParticleClass = Particle

    def __init__(self, gfx: Gfx, n: int,
                 radius: np.ndarray[Any, np.dtype[np.float64]]) -> None:
        """Initialize the simulation with n Particles with radii radius.

        radius can be a single value or a sequence with n values.

        Any key-value pairs passed in the styles dictionary will be passed
        as arguments to Matplotlib's Circle patch constructor when drawing
        the Particles.

        """
        self.gfx = gfx
        self.init_particles(n, radius)
        self.dt = 0.01
        self.init()

    def place_particle(self, rad: float) -> bool:
        # Choose x, y so that the Particle is entirely inside the
        # domain of the simulation.
        x = random.random()*(1 - 2*rad) + rad
        y = random.random()*(1 - 2*rad) + rad
        # Choose a random velocity (within some reasonable range of
        # values) for the Particle.
        vr = 0.1 * np.sqrt(np.random.random()) + 0.05
        vphi = 2*np.pi * np.random.random()
        vx, vy = vr * np.cos(vphi), vr * np.sin(vphi)
        particle = self.ParticleClass(x, y, vx, vy, rad)
        # Check that the Particle doesn't overlap one that's already
        # been placed.
        for p2 in self.particles:
            if p2.overlaps(particle):
                break
        else:
            self.particles.append(particle)
            return True
        return False

    def init_particles(self, n: int, radius: NDArray[np.floating[Any]]) -> None:
        """Initialize the n Particles of the simulation.

        Positions and velocities are chosen randomly; radius can be a single
        value or a sequence with n values.

        """

        # iterator = iter(radius)
        assert n == len(radius)
        # try:
        #     iterator = iter(radius)
        #     assert n == len(radius)
        # except TypeError:
        #     # r isn't iterable: turn it into a generator that returns the
        #     # same value n times.
        #     def r_gen(n: int, radius: NDArray[np.floating[Any]]) -> Generator[np.floating[Any], None, None]:
        #         for i in range(n):
        #             yield radius
        #     radius_g = r_gen(n, radius)

        self.n = n
        self.particles: list[Particle] = []
        for i, rad in enumerate(radius):
            # Try to find a random initial position for this particle.
            while not self.place_particle(rad):
                pass

    def change_velocities(self, p1: Particle, p2: Particle) -> None:
        """
        Particles p1 and p2 have collided elastically: update their
        velocities.

        """

        m1, m2 = p1.mass, p2.mass
        M = m1 + m2
        r1, r2 = p1.r, p2.r
        d = np.linalg.norm(r1 - r2)**2  # type: ignore
        v1, v2 = p1.v, p2.v
        u1 = v1 - 2*m2 / M * np.dot(v1-v2, r1-r2) / d * (r1-r2)  # type:ignore
        u2 = v2 - 2*m1 / M * np.dot(v2-v1, r2-r1) / d * (r2-r1)  # type:ignore
        p1.v = u1
        p2.v = u2

    def handle_collisions(self) -> set[int]:
        """Detect and handle any collisions between the Particles.

        When two Particles collide, they do so elastically: their velocities
        change such that both energy and momentum are conserved.

        """
        hits: set[int] = set()

        # We're going to need a sequence of all of the pairs of particles when
        # we are detecting collisions. combinations generates pairs of indexes
        # into the self.particles list of Particles on the fly.
        pairs = combinations(range(self.n), 2)
        for i, j in pairs:
            if self.particles[i].overlaps(self.particles[j]):
                self.change_velocities(self.particles[i], self.particles[j])
                hits.add(i)
                hits.add(j)
        return hits

    def handle_boundary_collisions(self, p: Particle) -> None:
        """Bounce the particles off the walls elastically."""

        if p.x - p.radius < 0:
            p.x = p.radius
            p.vx = -p.vx
        if p.x + p.radius > 1:
            p.x = 1-p.radius
            p.vx = -p.vx
        if p.y - p.radius < 0:
            p.y = p.radius
            p.vy = -p.vy
        if p.y + p.radius > 1:
            p.y = 1-p.radius
            p.vy = -p.vy

    def apply_forces(self) -> None:
        """Override this method to accelerate the particles."""
        pass

    def advance_animation(self) -> list[Circle]:
        """Advance the animation by dt, returning the updated Circles list."""

        for i, p in enumerate(self.particles):
            p.advance(self.dt)
            self.handle_boundary_collisions(p)
            self.circles[i].x = p.r[0]
            self.circles[i].y = p.r[1]

        hits = self.handle_collisions()
        for i, _ in enumerate(self.particles):
            self.circles[i].hit = i in hits

        self.apply_forces()
        return self.circles

    def init(self) -> list[Circle]:
        """Initialize the Matplotlib animation."""

        self.circles: list[Circle] = []
        for particle in self.particles:
            self.circles.append(particle.draw())
        return self.circles

    def animate(self, i: int) -> list[Circle]:
        """The function passed to Matplotlib's FuncAnimation routine."""

        self.advance_animation()
        return self.circles

    def setup_animation(self) -> None:
        self.fig, self.ax = plt.subplots()
        for s in ['top', 'bottom', 'left', 'right']:
            self.ax.spines[s].set_linewidth(2)
        self.ax.set_aspect('equal', 'box')
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        self.ax.xaxis.set_ticks([])
        self.ax.yaxis.set_ticks([])

    def do_animation(self,  interval: int = 1) -> None:
        """Set up and carry out the animation of the molecular dynamics."""

        self.setup_animation()
        anim = animation.FuncAnimation(self.fig, self.animate,
                                       init_func=self.init, frames=800, interval=interval, blit=True)


class Collision(App):
    def __init__(self, board: Board):
        super().__init__(board, auto_read=True)

    def _run(self) -> bool:

        nparticles = 8

        rnd: np.ndarray[Any, np.dtype[np.float64]
                        ] = np.random.random(nparticles)
        radii: np.ndarray[Any, np.dtype[np.float64]] = rnd*0.03
        radii += 0.02
        radii *= 2

        sim = Simulation(self.board.gfx, nparticles, radii)
        sim.do_animation()

        escaper = TimeEscaper(self)

        previous_circles: list[Circle] = []

        while True:
            btns = self.board.auto_read_buttons()
            if 'R' in btns:
                return True
            if btns:
                return False
            if escaper.check():
                return False

            circles = sim.animate(0)

            # self.gfx.clear()
            self.draw(previous_circles, erase=True)
            self.draw(circles)
            self.gfx.display()

            previous_circles = [Circle.create_from(c) for c in circles]

    def draw(self, circles: list[Circle], erase=False) -> None:
        c = 0 if erase else 1
        for circle in circles:
            k = config.HEIGHT
            x = int(circle.x * k + .5)
            y = int(circle.y * k + .5)
            r = int(circle.r * k + .5)
            if circle.hit:
                self.gfx.fill_circle(x, y, r, c)
            else:
                self.gfx.draw_circle(x, y, r, c)
