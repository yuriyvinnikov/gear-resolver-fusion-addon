"""Finite three-dimensional vectors, independent of physical units."""

from dataclasses import dataclass
from math import atan2, hypot, isfinite


@dataclass(frozen=True)
class Vec3:
    x: float
    y: float
    z: float

    def __post_init__(self) -> None:
        if not all(isfinite(v) for v in (self.x, self.y, self.z)):
            raise ValueError("Vector coordinates must be finite.")

    def __add__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> "Vec3":
        return Vec3(self.x * scalar, self.y * scalar, self.z * scalar)

    def dot(self, other: "Vec3") -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: "Vec3") -> "Vec3":
        return Vec3(self.y * other.z - self.z * other.y,
                    self.z * other.x - self.x * other.z,
                    self.x * other.y - self.y * other.x)

    @property
    def length(self) -> float:
        return hypot(self.x, self.y, self.z)

    def normalized(self) -> "Vec3":
        # Scale first: directions have no length unit, and even tiny nonzero
        # vectors are valid. This also avoids overflow for large coordinates.
        scale = max(abs(self.x), abs(self.y), abs(self.z))
        if scale <= 0.0:
            raise ValueError("A zero vector cannot define an axis direction.")
        scaled = Vec3(self.x / scale, self.y / scale, self.z / scale)
        return scaled * (1.0 / scaled.length)


def angle_between_vectors(first: Vec3, second: Vec3) -> float:
    """Directed-vector angle in [0, pi], stable close to parallel."""
    a, b = first.normalized(), second.normalized()
    return atan2(a.cross(b).length, a.dot(b))
