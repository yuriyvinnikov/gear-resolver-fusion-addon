# Architecture

The first task in MILESTONE_01 is implemented: package skeleton and pure axis
geometry. Gear mathematics, solving, Fusion adapters and commands remain pending.

- `core/geometry/vector.py`: immutable finite vectors and stable normalization.
- `core/geometry/line.py`: normalized infinite axes, shaft angles and true distance.
- `core/geometry/axis_relation.py`: tolerance-aware relationship and local spacing.
- `core/tolerances.py`: explicit millimeter/radian tolerances.
- `core/gears` and `core/solver`: reserved packages, no implementations yet.
- `fusion`: future Autodesk API boundary, including all unit conversions.
- `commands/gear_pair`: future orchestration; no gear equations in UI handlers.
- `addin.py`: documentation placeholder, not a working Fusion entry point.

Core imports only Python's standard library. Pure tests require no Fusion install.
Value objects reject nonfinite coordinates and invalid tolerances immediately.
Zero directions cannot construct a line. Tiny nonzero directions are valid and
normalized using scaling to avoid numerical underflow/overflow.

Coincident axes retain the `parallel` classification and have an explicit flag.
The future external-pair solver must reject coincident shafts and unsupported
relationships. Classification alone is not permission to generate gears.
