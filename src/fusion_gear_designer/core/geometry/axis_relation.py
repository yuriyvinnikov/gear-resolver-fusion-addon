"""Tolerance-aware classification, separate from exact line distance."""

from dataclasses import dataclass
from enum import Enum

from ..tolerances import DEFAULT_TOLERANCE, GeometryTolerance
from .line import Line3D, angle_between_axes, shortest_distance


class AxisRelation(str, Enum):
    PARALLEL = "parallel"
    INTERSECTING = "intersecting"
    SKEW = "skew"


@dataclass(frozen=True)
class AxisAnalysis:
    relationship: AxisRelation
    angle_rad: float
    shortest_distance_mm: float
    parallel_spacing_mm: float | None
    coincident_within_tolerance: bool


def analyze_axes(first: Line3D, second: Line3D,
                 tolerance: GeometryTolerance = DEFAULT_TOLERANCE) -> AxisAnalysis:
    """Classify shafts; inclusive tolerance boundaries.

    For almost parallel axes, spacing is measured at the first axis origin
    against the second axis. This is a local approximation, not the global
    shortest distance (the infinite lines may meet very far away).
    """
    angle = angle_between_axes(first, second)
    distance = shortest_distance(first, second)
    if angle <= tolerance.angle_rad:
        spacing = (first.origin - second.origin).cross(second.direction).length
        return AxisAnalysis(AxisRelation.PARALLEL, angle, distance, spacing,
                            spacing <= tolerance.distance_mm)
    relationship = (AxisRelation.INTERSECTING if distance <= tolerance.distance_mm
                    else AxisRelation.SKEW)
    return AxisAnalysis(relationship, angle, distance, None, False)
