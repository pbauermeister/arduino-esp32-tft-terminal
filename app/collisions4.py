"""Particles simulation.

Very crowded, reverse gravity (buoyancy), bubble grow with time and merge on mutual collision.
"""

import math

from app.collisions import (TIME_SUBQUANTAS, Collisions, Color, Particle,
                            Simulation)
from lib.board import Board

RADIUS_MIN = 1
RADIUS_GROWTH = .95


class Simulation4(Simulation):

    def after_draw(self) -> None:
        """Grow bubbles, recreate the ones that hit something."""
        for i, _ in enumerate(self.particles):
            p = self.particles[i]

            # grow slowly
            p.radius += RADIUS_GROWTH / TIME_SUBQUANTAS

            # die when touches wall, recreate
            if p.is_hit_by_wall or p.is_hit_by_other:
                p.v[0] = p.v[1] = 0  # ignore zombie during placement of newborn
                p2 = self.create_particle(RADIUS_MIN, p.rgb, p.rgb_hit)
                p.set_from(p2)

    def create_particle(self, rad: float, rgb: Color, rgb_hit: Color) -> Particle:
        """Create particle at/near bottom, with up and rather vertical speed."""

        def post_create(p: Particle) -> None:
            if not self.started:
                k = .5
                p.r[1] = p.r[1]*k + self.room_height*(1-k)
            else:
                # start deep
                k = .25
                p.r[1] = p.r[1]*k + self.room_height*(1-k)
            #else:
            #    # start at floor
            #    p.r[1] = self.room_height-rad - 1

            # upwards speed, stronger verticality
            p.v[0] *= .5
            p.v[1] = -abs(p.v[1])


        p = super().create_particle(rad, rgb, rgb_hit, post_create_fn=post_create)
        return p

        return p

    def resolve_collision(self, a: Particle, b: Particle) -> None:
        """The biggest one grows, the smallest one bursts."""
        # manage that a is the biggest one
        if a.radius < b.radius:
            a, b = b, a

        # a guzzles b
        surface = a.radius*a.radius + b.radius + b.radius
        a.radius = math.sqrt(surface)
        a.v[0] = (a.v[0] + b.v[0]) / 2

        # flash and sentence b to death
        b.is_hit_by_other = True

    def apply_forces(self) -> None:
        """The biggest the particle, the more buoyancy."""
        for p in self.particles:
            p.vy -= p.radius * 1.5
        pass

    def handle_wall_collisions(self, p: Particle) -> None:
        "Burst particle when side or top is reached."
        hit = False
        if p.x - p.radius <= 0:
            hit = True
        if p.x + p.radius >= self.room_width-1:
            hit = True
        if p.y - p.radius <= 0:
            hit = True
        p.is_hit_by_wall |= hit


class Collisions4(Collisions):
    def __init__(self, board: Board):
        super().__init__(board, Simulation4, name="Air bubbles")

    def set_collisions_params(self) -> None:
        super().set_collisions_params()
        self.nb = 40
        self.radius_min = RADIUS_MIN
        self.radius_max = RADIUS_MIN
        self.v_min = 750.0
        self.v_max = 1200.0 * .6
        self.flash_on_hit_other = True
        self.flash_on_hit_wall = False
