# Program based on
# https://scipython.com/blog/two-dimensional-collisions/?utm_source=pocket_saves

"""Particles simulation.

Quite crowded, no gravity, elastic bumps.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from itertools import combinations
from typing import Any, Callable

import numpy as np
from numpy.typing import NDArray

import config
from app import App, TimeEscaper
from lib.board import Board
from lib.gfx import Gfx

COLOR_BORDER = 127, 127, 125
Color = tuple[int, int, int]
TIME_SUBQUANTAS = 20


class Particle:
    """A class representing a two-dimensional particle."""

    def __init__(self, x: float, y: float, vx: float, vy: float,
                 rgb: Color, rgb_hit: Color,
                 radius: float = 0.01) -> None:
        """Initialize the particle's position, velocity, and radius.

        Any key-value pairs passed in the styles dictionary will be passed
        as arguments to Matplotlib's Circle patch constructor.

        """

        self.r = np.array((x, y))
        self.v = np.array((vx, vy))
        self.radius = radius
        self.mass = self.radius**2
        self.rgb = rgb
        self.rgb_hit = rgb_hit
        self.is_hit_by_wall: bool = False
        self.is_hit_by_other: bool = False

    def set_from(self, other: Particle) -> None:
        self.__dict__ = other.__dict__.copy()

    def __repr__(self) -> str:
        return str(self.__dict__)

    @staticmethod
    def create_from(other: Particle) -> Particle:
        p = Particle(
            other.r[0], other.r[1],
            other.v[0], other.v[1],
            other.rgb, other.rgb_hit, other.radius
        )
        p.is_hit_by_wall = other.is_hit_by_wall
        p.is_hit_by_other = other.is_hit_by_other
        return p

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

        if self.radius == 0 or other.radius == 0:
            return False

        return bool(np.hypot(*(self.r - other.r)) < self.radius + other.radius)

    def advance(self, dt: float, friction: float, kick: float) -> None:
        """Advance the Particle's position forward in time by dt."""
        if friction > 0:
            self.v *= (1 - friction/TIME_SUBQUANTAS)
        if kick > 0:
            self.v *= (1 + kick/TIME_SUBQUANTAS)
        self.r += self.v * dt / TIME_SUBQUANTAS


Floats = list[float]  # NDArray[np.float64]


class Simulation:
    """A class for a simple hard-circle molecular dynamics simulation.

    The simulation is carried out on a square domain: 0 <= x < 1, 0 <= y < 1.

    """

    ParticleClass = Particle

    def __init__(self, gfx: Gfx,
                 vmin: float, vmax: float,
                 room_width: int, room_height: int,
                 radii: Floats,
                 dt: float,
                 g: float) -> None:
        """Initialize the simulation with n Particles with radii radius.

        radius can be a single value or a sequence with n values.

        Any key-value pairs passed in the styles dictionary will be passed
        as arguments to Matplotlib's Circle patch constructor when drawing
        the Particles.

        """
        self.gfx = gfx
        self.vmin = vmin
        self.vmax = vmax
        self.room_width = room_width
        self.room_height = room_height
        self.dt = dt
        self.g = g
        self.particles: list[Particle] = []
        self.started = False
        self.init_particles(radii)
        self.started = True

    def create_particle(self, rad: float, rgb: Color, rgb_hit: Color,
                        post_create_fn: Callable[[Particle], None]|None=None) -> Particle:
        while True:
            # Choose x, y so that the Particle is entirely inside the
            # domain of the simulation.
            x = np.random.random()*(self.room_width - 2*rad) + rad
            y = np.random.random()*(self.room_height - 2*rad) + rad

            # Choose a random velocity (within some reasonable range of
            # values) for the Particle.
            vr = (self.vmax-self.vmin) * \
                np.sqrt(np.random.random()) + self.vmin
            vphi = 2*np.pi * np.random.random()
            vx, vy = vr * np.cos(vphi), vr * np.sin(vphi)
            particle = self.ParticleClass(
                x, y, vx, vy, rgb, rgb_hit, rad)
            if post_create_fn:
                post_create_fn(particle)

            # Check that the Particle doesn't overlap one that's already
            # been placed.
            for p2 in self.particles:
                if p2.overlaps(particle):
                    continue
            return particle

    def init_particles(self, radii: Floats) -> None:
        """Initialize the n Particles of the simulation.

        Positions and velocities are chosen randomly; radius can be a single
        value or a sequence with n values.
        """

        self.n = len(radii)
        self.particles = []

        for i, rad in enumerate(radii):
            hue = 360/self.n * i
            rgb = self.gfx.hsv_to_rgb(hue, 25, 100)
            rgb_hit = self.gfx.hsv_to_rgb(hue, 25, 50)

            p = self.create_particle(rad, rgb, rgb_hit)
            self.particles.append(p)

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

    def handle_mutual_collisions(self) -> None:
        """Detect and handle any collisions between the Particles.

        When two Particles collide, they do so elastically: their velocities
        change such that both energy and momentum are conserved.

        """
        # We're going to need a sequence of all of the pairs of particles when
        # we are detecting collisions. combinations generates pairs of indexes
        # into the self.particles list of Particles on the fly.
        pairs = combinations(range(self.n), 2)
        for i, j in pairs:
            a = self.particles[i]
            b = self.particles[j]
            if a.overlaps(b):
                self.resolve_collision(a, b)

    def resolve_collision(self, a: Particle, b: Particle) -> None:
        self.change_velocities(a, b)
        # Attempt to unstick particle pairs.
        # FIXME: in very crowded area, may  leads to "teleportation"
        while a.overlaps(b):
            a.advance(self.dt/2, 0, 0)
            b.advance(self.dt/2, 0, 0)
        a.advance(-self.dt, 0, 0)
        b.advance(-self.dt, 0, 0)
        a.is_hit_by_other = True
        b.is_hit_by_other = True

    def handle_wall_collisions(self, p: Particle) -> None:
        """Bounce the particles off the walls elastically."""
        hit = False
        if p.x - p.radius <= 0:
            p.x = p.radius+1
            p.vx = -p.vx
            hit = True
        if p.x + p.radius >= self.room_width-1:
            p.x = self.room_width-p.radius-1
            p.vx = -p.vx
            hit = True
        if p.y - p.radius <= 0:
            p.y = p.radius+1
            p.vy = -p.vy
            hit = True
        if p.y + p.radius >= self.room_height-1:
            p.y = self.room_height-p.radius-1
            p.vy = -p.vy
            hit = True
        p.is_hit_by_wall |= hit

    def apply_forces(self) -> None:
        """Override this method to accelerate the particles."""
        for p in self.particles:
            p.vy += self.g
        pass

    def mutate(self) -> None:
        """Override this method to mutate the particles."""
        pass

    def after_draw(self) -> None:
        """Override this method to do something after drawn."""
        pass

    def advance_animation(self, kick: float, friction: float) -> None:
        """Advance the animation by dt, returning the updated Circles list."""

        for i, p in enumerate(self.particles):
            p.advance(self.dt, friction, kick)

        self.handle_mutual_collisions()

        for p in self.particles:
            self.handle_wall_collisions(p)

        self.apply_forces()
        self.mutate()

    def animate(self, i: int, kick: float, friction: float) -> None:
        """The function passed to Matplotlib's FuncAnimation routine."""

        self.advance_animation(kick, friction)


class Collisions(App):
    def __init__(self, board: Board, simulation_cls: type[Simulation] = Simulation,
                 name="elastic collisions"):
        super().__init__(board, auto_read=True, name=name)
        self.simulation_cls = simulation_cls

    def set_collisions_params(self) -> None:
        self.nb = 10
        self.radius_min: float = 8
        self.radius_max: float = 25
        self.v_min: float = 100.0
        self.v_max: float = 1000.0
        self.dt: float = 0.01 / 3
        self.g: float = 0.0
        self.friction: float = 0.1
        self.kick: float = 0.1
        self.flash_on_hit_other = True
        self.flash_on_hit_wall = False

    def _run(self) -> bool:
        self.set_collisions_params()

        span = self.radius_max - self.radius_min

        radii = self.rand(self.radius_min,
                          self.radius_min + span/3,
                          int(self.nb*2/3))
        radii += self.rand(self.radius_max-span/3,
                           self.radius_max,
                           self.nb - len(radii))

        sim = self.simulation_cls(self.board.gfx,
                                  self.v_min, self.v_max,
                                  config.WIDTH, config.HEIGHT,
                                  radii, self.dt, self.g)

        escaper = TimeEscaper(self)
        previous_particles: list[Particle] = []

        kick = 0.0
        friction = 0.0
        self.gfx.set_auto_display_off()

        while True:
            for i in range(TIME_SUBQUANTAS):
                sim.animate(0, kick, friction)

            kick = 0.0
            friction = 0.0
            btns = self.board.auto_read_buttons()
            if 'R' in btns:
                return True
            elif 'B' in btns:
                kick = self.kick
                escaper.retrigger()
            elif 'C' in btns:
                friction = self.friction
                escaper.retrigger()
            elif btns:
                return False
            elif escaper.check():
                return False

            particles = sim.particles

            self.draw(previous_particles, erase=True)

            self.gfx.set_fg_color(*COLOR_BORDER)
            self.gfx.draw_rect(0, 0, config.WIDTH-1, config.HEIGHT-1, 1)

            self.draw(particles)
            self.gfx.display()

            previous_particles = [Particle.create_from(p) for p in particles]
            sim.after_draw()

            for p in particles:
                p.is_hit_by_wall = False
                p.is_hit_by_other = False

    def draw(self, particles: list[Particle], erase: bool = False) -> None:
        c = 0 if erase else 1
        for p in particles:
            if not erase:
                self.gfx.set_fg_color(*p.rgb)
            x = int(p.r[0])
            y = int(p.r[1])
            r = int(p.radius)
            flash = p.is_hit_by_other and self.flash_on_hit_other \
                or p.is_hit_by_wall and self.flash_on_hit_wall
            if flash:
                self.gfx.fill_circle(x, y, r, c)
            else:
                self.gfx.draw_circle(x, y, r, c)

    def rand(self, min: float, max: float, nb: int) -> Floats:
        return [random.random() * (max-min) + min for i in range(nb)]
