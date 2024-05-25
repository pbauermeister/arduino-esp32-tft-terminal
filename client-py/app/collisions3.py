"""Particles simulation.

Quite crowded, no gravity, bubble grow with time and pop on mutual collision.
"""

from app.collisions import Collisions, Simulation, TIME_SUBQUANTAS, Color, Particle
from lib.board import Board

RADIUS_MIN = 0.5
RADIUS_MAX = 25.0
RADIUS_GROWTH = 0.5


class Simulation3(Simulation):
    def mutate(self) -> None:
        for p in self.particles:
            if p.radius < RADIUS_MAX:
                p.radius += RADIUS_GROWTH / TIME_SUBQUANTAS

    def after_draw(self) -> None:
        for i, _ in enumerate(self.particles):
            p = self.particles[i]
            if p.is_hit_by_other:
                p = self.create_particle(RADIUS_MIN, p.rgb, p.rgb_hit)
                self.particles[i] = p

    def resolve_collision(self, a: Particle, b: Particle) -> None:
        a.is_hit_by_other = True
        b.is_hit_by_other = True

    def handle_wall_collisions(self, p: Particle) -> None:
        """Bounce the particles off the walls elastically."""
        super().handle_wall_collisions(p)
        if p.is_hit_by_wall:
            p.is_hit_by_other = True


class Collisions3(Collisions):
    def __init__(self, board: Board):
        super().__init__(board, Simulation3, name="Soap bubbles")

    def set_collisions_params(self) -> None:
        super().set_collisions_params()
        self.nb = 20
        self.radius_min = RADIUS_MIN
        self.radius_max = RADIUS_MIN
        self.v_min = 500.0
        self.v_max = 1200.0 * 0.6
        # TODO: avoid de-collision
