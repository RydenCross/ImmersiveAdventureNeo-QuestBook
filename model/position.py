from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Position:
    x: float = 0.0
    y: float = 0.0

    def moved(self, dx: float = 0.0, dy: float = 0.0) -> "Position":
        return Position(self.x + dx, self.y + dy)
