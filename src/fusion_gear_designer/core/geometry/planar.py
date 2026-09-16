"""Project-owned XY primitives; all lengths in millimeters."""

from dataclasses import dataclass
from math import cos, hypot, isfinite, sin


@dataclass(frozen=True)
class Vec2:
    x: float
    y: float

    def __post_init__(self) -> None:
        if not isfinite(self.x) or not isfinite(self.y):
            raise ValueError("Planar coordinates must be finite.")

    def __add__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scale: float) -> "Vec2":
        return Vec2(self.x * scale, self.y * scale)

    def dot(self, other: "Vec2") -> float:
        return self.x * other.x + self.y * other.y

    def cross(self, other: "Vec2") -> float:
        return self.x * other.y - self.y * other.x

    @property
    def length(self) -> float:
        return hypot(self.x, self.y)

    def rotate(self, angle_rad: float) -> "Vec2":
        c, s = cos(angle_rad), sin(angle_rad)
        return Vec2(c * self.x - s * self.y, s * self.x + c * self.y)

    def mirror_y(self) -> "Vec2":
        return Vec2(self.x, -self.y)


def segment_intersection(p: Vec2, p_end: Vec2, q: Vec2, q_end: Vec2,
                         *, tolerance_mm: float = 1e-9) -> Vec2 | None:
    """Unique XY intersection, including endpoints; None for disjoint segments.

    Degenerate segments and overlapping collinear intervals have no unique
    well-conditioned solution and raise ValueError. No point truthiness test.
    """
    if not isfinite(tolerance_mm) or tolerance_mm <= 0:
        raise ValueError("Intersection tolerance must be finite and positive.")
    a, b, delta = p_end - p, q_end - q, q - p
    la, lb = a.length, b.length
    if min(la, lb) <= tolerance_mm:
        raise ValueError("Degenerate segment.")
    u, v = a * (1 / la), b * (1 / lb)
    denominator = u.cross(v)
    if abs(denominator) <= tolerance_mm / max(la, lb):
        if abs(delta.cross(u)) > tolerance_mm:
            return None
        first, last = sorted((delta.dot(u), (q_end - p).dot(u)))
        lo, hi = max(0.0, first), min(la, last)
        if hi < lo - tolerance_mm:
            return None
        if hi - lo > tolerance_mm:
            raise ValueError("Collinear overlap has no unique intersection.")
        return p + u * ((lo + hi) / 2)
    t, s = delta.cross(v) / denominator, delta.cross(u) / denominator
    if not (-tolerance_mm <= t <= la + tolerance_mm and
            -tolerance_mm <= s <= lb + tolerance_mm):
        return None
    return p + u * min(la, max(0.0, t))
