"""Bounded integer search for fixed spacing; no continuous scaling or shift."""

from dataclasses import dataclass
from math import isfinite, ulp

from ..geometry.line import Line3D
from ..tolerances import DEFAULT_TOLERANCE, GeometryTolerance
from .spur_pair import (
    PairDefinition, SpurPairSolution, CenterDistanceTolerance, DEFAULT_CENTER_TOLERANCE,
    center_distance_matches, shaft_spacing, solve_tooth_counts, validate_distance,
)


class NoPairSolutionError(ValueError):
    """No supported integer pair satisfies both distance and ratio bounds."""


@dataclass(frozen=True)
class RatioCandidate:
    solution: SpurPairSolution
    desired_ratio: float
    ratio_error: float
    relative_ratio_error: float


def search_ratio(center_distance_mm: float, definition: PairDefinition,
                  desired_ratio: float, *, max_relative_ratio_error: float = 0.10,
                  minimum_teeth: int = 18, maximum_teeth: int = 400,
                  tolerance: CenterDistanceTolerance = DEFAULT_CENTER_TOLERANCE) -> tuple[RatioCandidate, ...]:
    """Return every supported candidate in the requested count range.

    Rank by absolute center error, relative ratio error, input count, output
    count. Ten percent is the explicit default ratio-error limit, not a promise
    of exact ratio. Ratios below one are supported; zero tolerance means exact.
    """
    validate_distance(center_distance_mm)
    if not isfinite(desired_ratio) or desired_ratio <= 0:
        raise ValueError("Desired ratio must be finite and positive.")
    if not isfinite(max_relative_ratio_error) or max_relative_ratio_error < 0:
        raise ValueError("Relative ratio-error limit must be finite and nonnegative.")
    if (type(minimum_teeth) is not int or type(maximum_teeth) is not int or
            not 18 <= minimum_teeth <= maximum_teeth <= 400):
        raise ValueError("Search tooth bounds must be integers with 18 <= minimum <= maximum <= 400.")
    # Validate each single gear once. Invalid counts/tip thickness are excluded;
    # unrelated failures are not caught. Common inputs were validated earlier.
    valid = {}
    for teeth in range(minimum_teeth, maximum_teeth+1):
        try:
            valid[teeth] = definition.gear(teeth)
        except ValueError:
            continue
    candidates = []
    for z1, first in valid.items():
        for z2, second in valid.items():
            required = first.pitch_radius_mm + second.pitch_radius_mm
            if not center_distance_matches(center_distance_mm, required, tolerance):
                continue
            ratio = z2/z1
            error = abs(ratio-desired_ratio)
            relative = error/desired_ratio
            # A finite requested limit cannot admit an overflowing relative
            # error. Otherwise both error and ULP allowance may become inf,
            # making the comparison below incorrectly accept the candidate.
            if not isfinite(relative):
                continue
            # Inclusive positive boundary despite subtraction/division roundoff;
            # zero retains the explicitly requested exact floating-point ratio.
            allowance = (4*max(ulp(ratio),ulp(desired_ratio))/desired_ratio
                         if max_relative_ratio_error > 0 else 0.0)
            if relative > max_relative_ratio_error + allowance:
                continue
            solution = solve_tooth_counts(center_distance_mm, definition, z1, z2, tolerance=tolerance)
            candidates.append(RatioCandidate(solution, desired_ratio, error, relative))
    candidates.sort(key=lambda c: (c.solution.center_error_mm, c.relative_ratio_error,
                                    c.solution.input_gear.teeth, c.solution.output_gear.teeth))
    if not candidates:
        raise NoPairSolutionError(
            f"No supported {minimum_teeth}..{maximum_teeth} tooth pair fits "
            f"{center_distance_mm:.9g} mm at module {definition.module_mm:.9g} "
            f"and ratio {desired_ratio:.9g} within relative error {max_relative_ratio_error:.9g}.")
    return tuple(candidates)


def search_axis_ratio(first: Line3D, second: Line3D, definition: PairDefinition,
                       desired_ratio: float, *, max_relative_ratio_error: float = .10,
                       minimum_teeth: int = 18, maximum_teeth: int = 400,
                       geometry_tolerance: GeometryTolerance = DEFAULT_TOLERANCE,
                       center_tolerance: CenterDistanceTolerance = DEFAULT_CENTER_TOLERANCE) -> tuple[RatioCandidate, ...]:
    distance = shaft_spacing(first, second, definition, tolerance=geometry_tolerance)
    return search_ratio(distance, definition, desired_ratio,
                        max_relative_ratio_error=max_relative_ratio_error,
                        minimum_teeth=minimum_teeth, maximum_teeth=maximum_teeth,
                        tolerance=center_tolerance)
