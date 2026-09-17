"""Fixed-center external spur solving; all lengths in mm, angles in radians."""

from dataclasses import dataclass
from math import isfinite, radians, sin, ulp

from ..gears.spur import SpurGearSpec
from ..geometry.axis_relation import AxisRelation, analyze_axes
from ..geometry.line import Line3D
from ..tolerances import DEFAULT_TOLERANCE, GeometryTolerance


@dataclass(frozen=True)
class PairDefinition:
    module_mm: float
    pressure_angle_rad: float = radians(20)
    backlash_mm: float = 0.15  # Total pair thickness reduction, split equally.
    thickness_mm: float = 8.0

    def __post_init__(self) -> None:
        if not isfinite(self.backlash_mm) or self.backlash_mm < 0:
            raise ValueError("Pair backlash must be finite and nonnegative.")
        # 400 is the supported upper count, also validating common parameters.
        self.gear(400)

    def gear(self, teeth: int) -> SpurGearSpec:
        return SpurGearSpec(self.module_mm, teeth, self.pressure_angle_rad,
                            self.backlash_mm/2, self.thickness_mm)


@dataclass(frozen=True)
class CenterDistanceTolerance:
    absolute_mm: float = 1e-6
    relative: float = 1e-9

    def __post_init__(self) -> None:
        if not all(isfinite(x) and x >= 0 for x in (self.absolute_mm, self.relative)):
            raise ValueError("Center tolerances must be finite and nonnegative.")

    def limit(self, actual_mm: float, required_mm: float) -> float:
        return max(self.absolute_mm, self.relative*max(actual_mm, required_mm))


DEFAULT_CENTER_TOLERANCE = CenterDistanceTolerance()


@dataclass(frozen=True)
class SpurPairSolution:
    input_gear: SpurGearSpec
    output_gear: SpurGearSpec
    center_distance_mm: float  # Actual geometry-derived spacing, never scaled.
    required_center_distance_mm: float
    center_error_mm: float  # Absolute error.
    relative_center_error: float  # Absolute error divided by required distance.
    ratio: float  # z_output / z_input, magnitude; external rotation is opposite.


def validate_distance(distance_mm: float) -> None:
    if not isfinite(distance_mm) or distance_mm <= 0:
        raise ValueError("Shaft center distance must be finite and positive.")


def center_distance_matches(actual: float, required: float,
                            tolerance: CenterDistanceTolerance) -> bool:
    """Inclusive boundary with a four-ULP roundoff allowance on operands."""
    limit = tolerance.limit(actual, required)
    return abs(actual-required) <= limit + 4*max(ulp(actual), ulp(required))


def solve_tooth_counts(center_distance_mm: float, definition: PairDefinition,
                       input_teeth: int, output_teeth: int, *,
                       tolerance: CenterDistanceTolerance = DEFAULT_CENTER_TOLERANCE) -> SpurPairSolution:
    validate_distance(center_distance_mm)
    first, second = definition.gear(input_teeth), definition.gear(output_teeth)
    required = first.pitch_radius_mm + second.pitch_radius_mm
    error = abs(center_distance_mm-required)
    if not center_distance_matches(center_distance_mm, required, tolerance):
        raise ValueError(
            f"Selected axes are {center_distance_mm:.9g} mm apart, but a "
            f"{input_teeth}T/{output_teeth}T pair at module {definition.module_mm:.9g} "
            f"requires {required:.9g} mm (error {error:.9g} mm).")
    return SpurPairSolution(first, second, center_distance_mm, required, error,
                            error/required, output_teeth/input_teeth)


def shaft_spacing(first: Line3D, second: Line3D, definition: PairDefinition, *,
                  tolerance: GeometryTolerance = DEFAULT_TOLERANCE) -> float:
    """Spacing at the first axis origin; also limit tilt over the gear width.

    This defines the reference for future placement, not a component transform.
    Almost-parallel lines may intersect elsewhere, so global shortest distance
    is deliberately not used as shaft spacing here.
    """
    analysis = analyze_axes(first, second, tolerance)
    if analysis.relationship is not AxisRelation.PARALLEL:
        raise ValueError(f"Selected axes are {analysis.relationship.value}, not parallel. "
                         "Only external spur gears on parallel shafts are supported.")
    if analysis.coincident_within_tolerance:
        raise ValueError("Selected axes coincide within tolerance; use two distinct shafts.")
    if definition.thickness_mm*sin(analysis.angle_rad) > tolerance.distance_mm:
        raise ValueError("Axis tilt over the gear thickness exceeds the distance tolerance.")
    assert analysis.parallel_spacing_mm is not None
    return analysis.parallel_spacing_mm


def solve_axis_pair(first: Line3D, second: Line3D, definition: PairDefinition,
                    input_teeth: int, output_teeth: int, *,
                    geometry_tolerance: GeometryTolerance = DEFAULT_TOLERANCE,
                    center_tolerance: CenterDistanceTolerance = DEFAULT_CENTER_TOLERANCE) -> SpurPairSolution:
    distance = shaft_spacing(first, second, definition, tolerance=geometry_tolerance)
    return solve_tooth_counts(distance, definition, input_teeth, output_teeth,
                             tolerance=center_tolerance)
