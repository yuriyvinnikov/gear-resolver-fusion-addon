"""Infinite axes with origins in millimeters and unit directions."""

from dataclasses import dataclass
from math import atan2

from .vector import Vec3


@dataclass(frozen=True)
class Line3D:
    origin: Vec3
    direction: Vec3

    def __post_init__(self) -> None:
        object.__setattr__(self, "direction", self.direction.normalized())

    def point_at(self, distance_mm: float) -> Vec3:
        return self.origin + self.direction * distance_mm


def angle_between_axes(first: Line3D, second: Line3D) -> float:
    """Unoriented shaft angle in [0, pi/2]; reversed axes are equivalent."""
    return atan2(first.direction.cross(second.direction).length,
                 abs(first.direction.dot(second.direction)))


def shortest_distance(first: Line3D, second: Line3D) -> float:
    """True infinite-line distance, without snapping near-parallel lines.

    A nonzero cross product defines the common normal even for very small
    angles. Exact parallelism has no such normal; use point-to-line distance.
    Classification tolerances deliberately belong to axis_relation instead.
    """
    delta = second.origin - first.origin
    normal = first.direction.cross(second.direction)
    if normal.length <= 0.0:
        return delta.cross(first.direction).length
    return abs(delta.dot(normal.normalized()))
