"""Standard unshifted external spur dimensions (millimeters and radians).

Rack fillet limit adapted from Study Gears rack_geometry, copyright (c) 2025
Osamu Takeuchi <osamu@big.jp>, MIT. See licenses/Study-Gears-MIT.txt.
"""

from dataclasses import dataclass
from math import atan, ceil, cos, isfinite, pi, radians, sin, sqrt, tan


@dataclass(frozen=True)
class SpurGearSpec:
    module_mm: float
    teeth: int
    pressure_angle_rad: float = radians(20)
    backlash_mm: float = 0.0
    thickness_mm: float = 8.0

    def __post_init__(self) -> None:
        values = (self.module_mm, self.pressure_angle_rad, self.backlash_mm, self.thickness_mm)
        if not all(isfinite(x) for x in values):
            raise ValueError("Gear parameters must be finite.")
        if self.module_mm <= 0 or self.thickness_mm <= 0 or self.backlash_mm < 0:
            raise ValueError("Module/thickness must be positive; backlash cannot be negative.")
        if not 1e-6 <= self.module_mm <= 1e6:
            raise ValueError("Supported numerical module range is 1e-6 through 1e6 mm.")
        if not radians(14.5) <= self.pressure_angle_rad <= radians(30):
            raise ValueError("Supported pressure angles are 14.5 through 30 degrees.")
        if type(self.teeth) is not int or not self.minimum_teeth <= self.teeth <= 400:
            raise ValueError(f"Supported tooth count is {self.minimum_teeth} through 400; undercut is excluded.")
        if not isfinite(self.outside_radius_mm):
            raise ValueError("Derived gear dimensions overflow.")
        if self.tooth_thickness_mm <= 0:
            raise ValueError("Backlash removes the entire pitch tooth thickness.")
        u = sqrt((self.outside_radius_mm / self.base_radius_mm)**2 - 1)
        tip_half_angle = (self.tooth_thickness_mm / (2*self.pitch_radius_mm)
                          + tan(self.pressure_angle_rad) - self.pressure_angle_rad
                          - (u - atan(u)))
        if tip_half_angle <= 1e-12:
            raise ValueError("Backlash produces a pointed or crossed tooth tip.")

    @property
    def minimum_teeth(self) -> int:
        # Conservative floor plus rack addendum undercut limit, no profile shift.
        a = self.pressure_angle_rad
        effective_height = 1.25 - self.rack_fillet_radius_mm/self.module_mm*(1-sin(a))
        return max(18, ceil(2 * effective_height / sin(a)**2))

    @property
    def rack_fillet_radius_mm(self) -> float:
        """Largest rack-tip fillet tangent to flank/root without crossing gap center."""
        a, m = self.pressure_angle_rad, self.module_mm
        clearance_limit = .25*m/(1-sin(a))
        width_limit = (pi*m/4 + self.backlash_mm/2 - 1.25*m*tan(a))*tan(pi/4+a/2)
        return min(clearance_limit, width_limit)

    @property
    def pitch_diameter_mm(self) -> float:
        return self.module_mm * self.teeth

    @property
    def pitch_radius_mm(self) -> float:
        return self.pitch_diameter_mm / 2

    @property
    def base_radius_mm(self) -> float:
        return self.pitch_radius_mm * cos(self.pressure_angle_rad)

    @property
    def outside_radius_mm(self) -> float:
        return self.pitch_radius_mm + self.module_mm

    @property
    def root_radius_mm(self) -> float:
        return self.pitch_radius_mm - 1.25 * self.module_mm

    @property
    def circular_pitch_mm(self) -> float:
        return pi * self.module_mm

    @property
    def angular_pitch_rad(self) -> float:
        return 2 * pi / self.teeth

    @property
    def tooth_thickness_mm(self) -> float:
        """Backlash here is this gear's total pitch thickness reduction.

        A future pair solver must distribute total pair backlash across gears.
        Equal allocation means each spec receives half the pair input.
        """
        return self.circular_pitch_mm / 2 - self.backlash_mm
