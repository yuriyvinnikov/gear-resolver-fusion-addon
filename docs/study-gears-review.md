# Study Gears review — 2026-09-16

Historical audit: implementation has since proceeded. Current reuse, fixes and
tests are recorded in [study-gears-adaptation.md](study-gears-adaptation.md).

## Result

Recommend a narrow adaptation of external spur profile mathematics behind our
pure-core interface. No upstream source was incorporated into the project;
isolated helper behavior was executed in memory as described below.

Reviewed [Study Gears](https://github.com/osamutake/fusion360-study-gears/commit/e8d0efcb3ad40e52c1e07b2f82ef4a24112c5094)
at `e8d0efcb3ad40e52c1e07b2f82ef4a24112c5094` (2025-09-24).
The GitHub connector resolved the earlier network limitation. Source files were
refetched at this immutable revision. See `study-gears-source-lock.json` for
commit and blob identities, including the actual helper gitlink revision.

## License

[LICENSE.txt](https://github.com/osamutake/fusion360-study-gears/blob/main/LICENSE.txt)
specifies MIT, copyright (c) 2025 Osamu Takeuchi. The terms are in Japanese and
permit modification and redistribution, including commercial use, with copyright
and permission notices preserved. Preserve the complete original license when
adapting, including its warranty disclaimer. This does not select our project's
license. Record revision, files and modifications in THIRD_PARTY_NOTICES.md;
separately check any reused submodule's license.

## Source map

[gear_curve.py](https://raw.githubusercontent.com/osamutake/fusion360-study-gears/main/modules/gear_curve.py):
`GearParams`, `rack_geometry`, `gear_curve`, `calculate_involute_curve`,
`calculate_fillet_curve`, `combine_curves_at_intersection` form the adaptation
candidate. Dependencies include `Vector`/`vec` from `fusion_helper`, curve
intersection helpers from `gear_curve_curve.py`, and numerical routines from
`lib/function.py`. Both helper bodies have now been inspected at the pinned
revision. The helper import boundary and vector implementation were also reviewed.

[gear_cylindrical.py](https://raw.githubusercontent.com/osamutake/fusion360-study-gears/main/modules/gear_cylindrical.py):
Fusion-specific component/sketch creation, profile mirroring, blank extrusion,
groove cutting and circular patterning. `draw_part` constructs fitted splines.
Use as an adapter reference only; independently validate profile selection and
placement in Fusion. Do not import it into core.

## Integration proposal

Adapt the rack-envelope method in an isolated `core/gears/study_gears_profile.py`.
Use project-owned pure vectors and bounded numerical routines. Input should be a
validated SpurGearSpec in millimeters/radians; output should be typed local XY
profile segments with radii and an explicit tooth-center phase. No adsk objects.
Support external spur only, zero profile shift and helix angle. Keep shaft
analysis, pair solving, relative phase, placement and UI project-owned.

## Risks and required checks

The reviewed profile uses a rolling rack envelope for involute flanks and a
rack-tip fillet envelope for roots. Its `90 - alpha` search bound needs scrutiny
against radian conventions; unbounded root-search loops need caps. Fixed sample
counts do not establish a geometric error bound. Backlash is applied as a half
offset in rack geometry; confirm resulting pitch thickness before mapping our
pair-level input. These are review concerns, not experimentally confirmed bugs.

Before integration: preserve pinned licenses; compare
against analytic involute identities; test flank symmetry, joined endpoints,
nonintersection, scaling, pitch thickness, backlash distribution and root
clearance. Establish supported tooth/angle ranges and measurable approximation
tolerance. Test pair interference over a meshing cycle, including range limits.
Run the documented manual Fusion matrix once adapters exist.

## Helper audit and reproduced behavior

The actual `modules/lib/fusion_helper` gitlink points to
[`d313728f8d50e2b792385ff7fb6b735037c6aa36`](https://github.com/osamutake/fusion360-helper/tree/d313728f8d50e2b792385ff7fb6b735037c6aa36).
Its LICENSE.txt has the same MIT copyright and blob as Study Gears. Its
`__init__.py` imports command, component, sketch and other Fusion modules; even
`vector.py` imports `adsk.core`. Importing this package violates our pure-core
boundary. Review scope covers profile dependencies, not every Fusion utility.

Confirmed by isolated execution of the pinned function bodies:

1. `cross_point((0,0),(2,0),(1,-1),(1,1))` returns `(-1,0)` although the
   segments intersect at `(1,0)`. The returned point uses subtraction instead of
   addition along the first segment. Do not copy this defect into root trimming.
2. `find_root(0,1,lambda x: x*x+1)` returns 0 with residual 1. This is an explicit
   nearest-endpoint fallback, not a root. Our wrapper must distinguish no bracket
   from success and check residuals.
3. Helper `Vector(1,0,7).rotate(0)` drops z to 0. Treat its rotation as XY-only;
   do not reuse it for shaft placement.
4. Control case `find_root(0,1,lambda x: x*(x-0.5))` returns approximately 0.5,
   a valid root. An initial probe incorrectly expected failure; that assertion
   was corrected and is not reported as an upstream defect.

Further static findings: intersection uses exact determinant equality and treats
collinear cases as absent; `cross_point_x_desc` requires descending-X curves;
`closest_point_x_desc` measures distance to supporting lines, not clamped segments,
and lacks empty/degenerate input guards. Vector truthiness makes the zero point
false, so `if p` cannot reliably distinguish an origin intersection from None.
`minimize` uses golden-section search and needs an appropriate unimodal interval.
Neither numerical helper validates finite inputs, positive tolerance or maximum
iterations. These contracts require explicit handling and regression tests.

Decision: preserve the rack-envelope approach but replace/fix numerical and
intersection helpers behind project-owned APIs; do not vendor the helper package.
Add regression tests for the crossing-sign defect when implementing intersection
logic. No new core math was added during this audit.

Validation: 19 existing core tests passed. Four isolated upstream behavior probes
passed after correcting the control assertion. Imports were removed via AST and
the upstream Vector supplied directly; function bodies were unchanged. Source was
executed in memory only, with no Fusion simulation or generated gear. License
files were rechecked at both pinned revisions. No source was vendored; full
generator correctness and Fusion runtime behavior remain unverified.
