# Architecture

Implemented: pure axis geometry, corrected mathematical helpers, standard spur
dimensions and an adapted rack-envelope profile. Pair solving, Fusion adapters
and commands remain pending.

- `core/geometry/vector.py`: immutable finite vectors and stable normalization.
- `core/geometry/line.py`: normalized infinite axes, shaft angles and true distance.
- `core/geometry/axis_relation.py`: tolerance-aware relationship and local spacing.
- `core/tolerances.py`: explicit millimeter/radian tolerances.
- `core/geometry/planar.py`: immutable XY vectors and unique segment intersection.
- `core/numerics.py`: bounded root solving with explicit failures.
- `core/gears/spur.py`: validated unshifted spur dimensions and rack limits.
- `core/gears/involute.py`: canonical analytic involute.
- `core/gears/study_gears_profile.py`: isolated MIT-attributed rack-envelope
  adaptation, analytic root joins and error-controlled immutable polyline output.
- `core/solver`: reserved for fixed-axis pair solving.
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
