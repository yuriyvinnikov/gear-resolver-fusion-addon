"""Central tolerances in millimeters and radians."""

from dataclasses import dataclass
from math import isfinite, pi


@dataclass(frozen=True)
class GeometryTolerance:
    distance_mm: float = 1e-6
    angle_rad: float = 1e-8

    def __post_init__(self) -> None:
        if not isfinite(self.distance_mm) or self.distance_mm <= 0:
            raise ValueError("Distance tolerance must be finite and positive.")
        if not isfinite(self.angle_rad) or not 0 < self.angle_rad < pi / 2:
            raise ValueError("Angular tolerance must be between 0 and pi/2 radians.")


DEFAULT_TOLERANCE = GeometryTolerance()
