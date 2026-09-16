"""Restricted rack-envelope adaptation of Osamu Takeuchi's Study Gears.

Copyright (c) 2025 Osamu Takeuchi <osamu@big.jp>
MIT: see licenses/Study-Gears-MIT.txt and THIRD_PARTY_NOTICES.md.
Source: modules/gear_curve.py at e8d0efcb3ad40e52c1e07b2f82ef4a24112c5094.
Local changes: immutable XY values, analytic envelope joins, bounded chord
sampling, strict validation; no helper submodule, Fusion, or undercut trimming.
"""

from collections.abc import Callable
from dataclasses import dataclass
from math import atan2, ceil, cos, hypot, isfinite, pi, sin, sqrt, tan

from ..geometry.planar import Vec2
from .spur import SpurGearSpec


@dataclass(frozen=True)
class RackGeometry:
    pitch_radius_mm: float
    fillet_center: Vec2
    fillet_radius_mm: float
    join_roll_rad: float
    bottom_roll_rad: float
    join_involute_parameter: float


def rack_geometry(spec: SpurGearSpec) -> RackGeometry:
    """Specialize upstream rack_geometry to full-radius standard rack tips.

    Addendum=1m, dedendum=1.25m, clearance=.25m. The clearance-limited
    fillet joins at -1m; a narrower rack tip caps its radius as in upstream.
    Analytic tangency removes curve intersection searches without undercut.
    """
    a, m, rp = spec.pressure_angle_rad, spec.module_mm, spec.pitch_radius_mm
    radius = spec.rack_fillet_radius_mm
    if radius <= 0:
        raise ValueError("No positive rack fillet fits the tooth gap.")
    center = Vec2(rp - 1.25*m + radius,
                  spec.backlash_mm/2 - 1.25*m*tan(a) - radius/tan(pi/4 + a/2))
    join_height = -1.25*m + radius*(1-sin(a))
    u = tan(a) + join_height / (rp*sin(a)*cos(a))
    if u < -1e-12:
        raise ValueError("Rack envelope requires undercut trimming; unsupported.")
    roll = (spec.backlash_mm/2 + join_height/(sin(a)*cos(a))) / rp
    return RackGeometry(rp, center, radius, roll, center.y/rp, max(0.0, u))


def flank_point(spec: SpurGearSpec, parameter: float) -> Vec2:
    """Lower flank, centered tooth along +X, using upstream rack_trace envelope.

    The straight-rack envelope is reduced algebraically to remove its derivative
    quotient. u=0 is the base circle; u=tan(alpha) is the pitch circle.
    """
    if not isfinite(parameter) or parameter < 0:
        raise ValueError("Flank parameter must be finite and nonnegative.")
    rp, a = spec.pitch_radius_mm, spec.pressure_angle_rad
    roll = parameter - tan(a) + spec.backlash_mm/(2*rp)
    k = rp * (parameter - tan(a))
    point = Vec2(rp + k*sin(a)*cos(a), -k*cos(a)**2)
    return point.rotate(roll - pi/(2*spec.teeth))


def root_point(spec: SpurGearSpec, rack: RackGeometry, roll_rad: float) -> Vec2:
    """Inner envelope of the moving rack-tip circle (upstream fillet_trace).

    The chosen inward normal is continuous between the tangent join and root
    circle, avoiding the upstream coordinate-based choice between two branches.
    """
    if not isfinite(roll_rad):
        raise ValueError("Root roll parameter must be finite.")
    rp, center, radius = rack.pitch_radius_mm, rack.fillet_center, rack.fillet_radius_mm
    moving = Vec2(center.x, center.y - rp*roll_rad)
    normal = Vec2(rp - center.x, rp*roll_rad - center.y)
    length = normal.length
    if length <= 0:
        raise ValueError("Singular rack-tip envelope.")
    point = moving - normal * (radius/length)
    return point.rotate(roll_rad - pi/(2*spec.teeth))


def _sample(curve: Callable[[float], Vec2], start: float, end: float,
            second_derivative_bound: float, tolerance: float) -> tuple[Vec2, ...]:
    # Linear interpolation error <= max|f''| * delta_parameter**2 / 8.
    estimate = abs(end-start)*sqrt(second_derivative_bound/(8*tolerance))
    if not isfinite(estimate) or estimate > 4096:
        raise ValueError("Requested chord accuracy exceeds the 4096-segment curve limit.")
    count = max(1, ceil(estimate))
    return tuple(curve(start + (end-start)*i/count) for i in range(count+1))


@dataclass(frozen=True)
class SpurProfile:
    lower_root: tuple[Vec2, ...]  # root circle to involute join
    lower_flank: tuple[Vec2, ...]  # join to tip
    tip: tuple[Vec2, ...]  # lower to upper flank
    upper_flank: tuple[Vec2, ...]  # tip to join
    upper_root: tuple[Vec2, ...]  # join to root circle
    root_gap: tuple[Vec2, ...]  # upper root to next tooth's lower root
    chord_tolerance_mm: float

    @property
    def tooth_sector(self) -> tuple[Vec2, ...]:
        """One CCW sector, including both endpoints, with shared joins once."""
        segments = (self.lower_root, self.lower_flank, self.tip,
                    self.upper_flank, self.upper_root, self.root_gap)
        return tuple(p for segment in segments[:-1] for p in segment[:-1]) + segments[-1]


def generate_spur_profile(spec: SpurGearSpec, *, chord_tolerance_mm: float | None = None) -> SpurProfile:
    """Generate a deterministic CCW tooth sector, with exact analytic joins.

    Default chord error is 0.001 module. Output is sampled polylines, not Fusion
    splines; fitting arbitrary splines later does not preserve this error bound.
    """
    tolerance = spec.module_mm*0.001 if chord_tolerance_mm is None else chord_tolerance_mm
    if not isfinite(tolerance) or tolerance <= 0 or tolerance > spec.module_mm*0.01:
        raise ValueError("Chord tolerance must be positive and <= 0.01 module.")
    rack = rack_geometry(spec)
    rb, rp, ra = spec.base_radius_mm, spec.pitch_radius_mm, spec.outside_radius_mm
    u_end = sqrt((ra/rb)**2 - 1)
    lower = _sample(lambda u: flank_point(spec, u), rack.join_involute_parameter,
                    u_end, rb*sqrt(1+u_end*u_end), tolerance)
    # C(t)=R(t)(cx,cy-rp*t), N(t)=R(t)normalize(D,rp*t-cy).
    # |C''| <= |(cx,cy-rp*t)|+2rp;
    # |N''| <= 1+2rp/D+3(rp/D)^2, D=rp-cx > 0.
    d = rp-rack.fillet_center.x
    max_y = max(abs(rack.fillet_center.y-rp*t)
                for t in (rack.join_roll_rad, rack.bottom_roll_rad))
    bound = (hypot(rack.fillet_center.x, max_y) + 2*rp
             + rack.fillet_radius_mm*(1+2*rp/d+3*(rp/d)**2))
    root = _sample(lambda t: root_point(spec, rack, t), rack.bottom_roll_rad,
                   rack.join_roll_rad, bound, tolerance)
    if (root[-1]-lower[0]).length > spec.module_mm*1e-9:
        raise ValueError("Root and involute envelopes did not join.")
    root = root[:-1] + (lower[0],)
    tip_angle = -atan2(lower[-1].y, lower[-1].x)
    root_angle = -atan2(root[0].y, root[0].x)
    if not (0 < tip_angle < root_angle and root_angle <= pi/spec.teeth+1e-12):
        raise ValueError("Profile crosses its tooth sector boundary.")
    tip = _sample(lambda t: Vec2(ra*cos(t), ra*sin(t)), -tip_angle, tip_angle, ra, tolerance)
    tip = (lower[-1],) + tip[1:-1] + (lower[-1].mirror_y(),)
    if abs(root_angle-pi/spec.teeth) <= 1e-12:
        # Width-limited rack fillets meet at the center of the tooth gap.
        gap = (root[0].mirror_y(),)
    else:
        gap = _sample(lambda t: Vec2(spec.root_radius_mm*cos(t), spec.root_radius_mm*sin(t)),
                      root_angle, spec.angular_pitch_rad-root_angle, spec.root_radius_mm, tolerance)
        gap = (root[0].mirror_y(),) + gap[1:-1] + (root[0].rotate(spec.angular_pitch_rad),)
    return SpurProfile(root, lower, tip,
                       tuple(p.mirror_y() for p in reversed(lower)),
                       tuple(p.mirror_y() for p in reversed(root)), gap, tolerance)


def gear_outline(spec: SpurGearSpec, *, chord_tolerance_mm: float | None = None) -> tuple[Vec2, ...]:
    """Closed CCW outline; only the final point repeats the first point."""
    profile = generate_spur_profile(spec, chord_tolerance_mm=chord_tolerance_mm)
    sector = profile.tooth_sector[:-1]
    points = tuple(p.rotate(i*spec.angular_pitch_rad) for i in range(spec.teeth) for p in sector)
    return points + (points[0],)
