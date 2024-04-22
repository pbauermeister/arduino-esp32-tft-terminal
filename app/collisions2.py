"""Particles simulation.

Sparsely crowded, gravity, elastic bumps.
"""

from app.collisions import Collisions
from lib.board import Board


class Collisions2(Collisions):

    def __init__(self, board: Board, **kwargs) -> None:
        super().__init__(board, **kwargs, name="Collisions + gravity")

    def set_collisions_params(self) -> None:
        super().set_collisions_params()
        self.nb = 4
        self.radius_min = 4
        self.radius_max = 24
        self.v_min = 100.0
        self.v_max = 1200.0
        self.dt = 0.01
        self.g = 7.5
        self.friction = 0.1
        self.kick = 0.1
