# Third-party notices

## Study Gears

Copyright (c) 2025 Osamu Takeuchi <osamu@big.jp>

MIT; the complete original license is preserved in
[licenses/Study-Gears-MIT.txt](licenses/Study-Gears-MIT.txt) and must accompany
distribution of the adapted code or substantial portions.

Repository: https://github.com/osamutake/fusion360-study-gears

Pinned revision: `e8d0efcb3ad40e52c1e07b2f82ef4a24112c5094`.
Adapted upstream file: `modules/gear_curve.py`, specifically standard rack
geometry, rolling-rack straight-line/circle envelopes and tooth-center rotation.
Local files: `core/gears/study_gears_profile.py` and the rack fillet radius
convention in `core/gears/spur.py` under `src/fusion_gear_designer`.

Substantial changes: restricted external unshifted spur domain; immutable Vec2;
analytic tangent joins and continuous root-envelope branch; no undercut trimming;
bounded error-controlled polyline sampling; explicit validation/failures.
See [adaptation record](docs/study-gears-adaptation.md) for function-level mapping.

The reviewed helper revision is `d313728f8d50e2b792385ff7fb6b735037c6aa36` from
https://github.com/osamutake/fusion360-helper, with the same MIT license blob.
No helper source is incorporated. Numerical and intersection primitives are
project-owned and deliberately correct the audited failure behaviors.

All runtime dependencies remain in the Python standard library. The upstream
MIT grant applies to its adapted material; it does not select a license for the
remaining project-owned code (see LICENSE).
