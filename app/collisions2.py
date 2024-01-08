from app.collisions import Collisions


class Collisions2(Collisions):

    def set_collisions_params(self) -> None:
        self.nb = 4
        self.radius_min = 4
        self.radius_max = 24
        self.v_min = 100.0
        self.v_max = 1200.0
        self.dt = 0.01
