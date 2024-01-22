"""Particles simulation.

Quite crowded, no gravity, bubble grow with time and pop on mutual collision.
"""

from app.collisions import Collisions, Simulation, TIME_SUBQUANTAS, Color, Particle
from lib.board import Board

RADIUS_MIN = 0.5
RADIUS_MAX = 25.0
RADIUS_GROWTH = .5


class Simulation3(Simulation):
    def mutate(self) -> None:
        for p in self.particles:
            if p.radius < RADIUS_MAX:
                p.radius += RADIUS_GROWTH / TIME_SUBQUANTAS

    def after_draw(self) -> None:
        for i, _ in enumerate(self.particles):
            p = self.particles[i]
            if p.is_hit_by_other:
                p = self.place_particle(RADIUS_MIN, p.rgb, p.rgb_hit)
                self.particles[i] = p

    def _place_particle(self, rad: float, rgb: Color, rgb_hit: Color) -> Particle:
        p = super().place_particle(rad, rgb, rgb_hit)
        p.r[1] = self.room_height-1
        p.v[1] = abs(p.v[1])
        return p

    def resolve_collision(self, a: Particle, b: Particle) -> None:
        # Do nothing. do not attempt to unstick particles, as they will pop
        pass


class Collisions3(Collisions):
    def __init__(self, board: Board):
        super().__init__(board, Simulation3)

    def set_collisions_params(self) -> None:
        super().set_collisions_params()
        self.nb = 20
        self.radius_min = RADIUS_MIN
        self.radius_max = RADIUS_MIN
        self.v_min = 500.0
        self.v_max = 1200.0 * .6
        # TODO: avoid de-collision
