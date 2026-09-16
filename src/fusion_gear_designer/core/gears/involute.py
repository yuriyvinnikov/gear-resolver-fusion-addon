"""Analytic base-circle involute for independent profile verification."""

from math import cos, isfinite, sin

from ..geometry.planar import Vec2


def involute_point(base_radius_mm: float, parameter: float) -> Vec2:
    """Unwinding parameter >= 0; at zero the point is (base_radius, 0)."""
    if not isfinite(base_radius_mm) or base_radius_mm <= 0:
        raise ValueError("Base radius must be finite and positive.")
    if not isfinite(parameter) or parameter < 0:
        raise ValueError("Involute parameter must be finite and nonnegative.")
    c, s = cos(parameter), sin(parameter)
    return Vec2(base_radius_mm * (c + parameter*s),
                base_radius_mm * (s - parameter*c))
