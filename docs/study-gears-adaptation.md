# Study Gears spur profile adaptation

## Pinned baseline and attribution

- Study Gears: `e8d0efcb3ad40e52c1e07b2f82ef4a24112c5094`.
- Actual helper gitlink: `d313728f8d50e2b792385ff7fb6b735037c6aa36`.
- File blob identities: [source lock](study-gears-source-lock.json).
- Copyright (c) 2025 Osamu Takeuchi; original full MIT text is preserved in
  [licenses/Study-Gears-MIT.txt](../licenses/Study-Gears-MIT.txt).

This implementation supersedes the review-only status in the historical
[audit](study-gears-review.md). No helper package is vendored or imported.

## Exact reuse boundary

Source: [modules/gear_curve.py](https://github.com/osamutake/fusion360-study-gears/blob/e8d0efcb3ad40e52c1e07b2f82ef4a24112c5094/modules/gear_curve.py).

| Upstream function/algorithm | Local implementation and change |
| --- | --- |
| `rack_geometry` | `study_gears_profile.rack_geometry` and `SpurGearSpec.rack_fillet_radius_mm`: specialize to standard external, unshifted spur rack; retain clearance and rack-width fillet limits |
| `gear_curve.shift_rotate` and `d_shift_rotate` | Algebraically reduced rolling-rack transform and its normal; no generic derivative/vector helper dependency |
| `gear_curve.rack_trace` | `flank_point`: same straight-rack envelope, reduced to a closed expression; explicit base-circle unwinding parameter |
| `gear_curve.fillet_trace` | `root_point`: same moving-circle envelope; choose a continuous inward branch analytically instead of comparing coordinates of two candidates |
| `gear_curve` tooth-center rotation | Explicit `-pi/(2*z)` applied to rack coordinates; tooth center is +X, lower flank has negative Y |

Only these geometry methods are adapted. `SpurGearSpec`, analytical involute
oracle, typed XY values, profile assembly, bounded sampling and validation are
project-owned. The scalar root and segment-intersection primitives are corrected
project-owned replacements for the audited helper functionality. The restricted
profile generator does **not** need them at runtime: its joins are analytic.
They are retained with the specifically requested upstream regression cases.

## Deliberately not reused

- `calculate_involute_curve`: its minimization bounds and fixed sample counts.
- `calculate_fillet_curve`: scan loops, adaptive halving and cusp workaround.
- `combine_curves_at_intersection`: approximate nearest-point stitching.
- `gear_curve_curve.Curve`, descending-X traversal and supporting-line distances.
- `lib/function.py`: endpoint fallback, golden-section implementation and implicit
  convergence contracts. No golden-section search is needed here.
- `fusion_helper`: eager Autodesk imports, mutable vectors, exact equality and
  XY rotation that drops Z. This project's Vec2 is explicitly two-dimensional.
- `gear_cylindrical.py`, sketches, splines, solids, UI and all other gear families.
- Internal gearing, profile shift, tip extension/fillet and undercut trimming.

## Fixes relative to the audited helpers

`segment_intersection` returns `p + t*u`, not `p - t*u`. The upstream regression
segments (0,0)-(2,0) and (1,-1)-(1,1) now yield (1,0). It uses explicit None,
length-scaled parallel tolerance, segment bounds and endpoint handling. Degenerate
segments and collinear intervals without a unique point fail explicitly.

`bisect_root` rejects an absent sign bracket with NoRootError, including
`f(x)=x*x+1` on [0,1]. It never returns the nearest endpoint as a substitute.
Endpoint roots are supported; inputs/evaluations must be finite. Iteration limit,
stagnation and an unacceptable residual raise ConvergenceError. Continuity and
a root bracket are caller preconditions; a same-sign interval may contain roots
but is intentionally not accepted as a valid bracket.

The generator replaces uncertain root/minimum searches and intersections with
analytic tangency in a validated no-undercut domain. Thus known upstream helper
defects cannot affect its profile assembly.

## Root geometry and numerical contract

The root is the envelope of a rolling rack-tip circle, not a radial line or
arbitrary decorative arc. It joins the involute tangentially, reaches the root
circle tangentially, then follows that circle into the next tooth. If the rack
width caps the fillet, adjacent root transitions meet at the gap center and the
zero-length root arc is omitted. See [equations](gear-math.md).

The supported domain rejects undercut rather than clipping an overlapping
profile. 20-degree gears support 18..400 teeth; 14.5-degree gears start at 32.
Pressure angle is 14.5..30 degrees. Dynamic minimum count uses the actual
rack-fillet tangent height, with an additional conservative floor of 18.

Samples have a documented linear interpolation error bound, not merely a fixed
count. Output is a deterministic immutable polyline sector and optional full
closed outline. Arbitrary spline fitting in a later Fusion adapter would require
its own error validation.

## Validation and limitations

Complete suite: **56 tests passed** (19 original tests plus 37 new tests).
Coverage includes both helper regressions, analytic involute agreement, pitch
thickness/backlash, root tangency, left/right symmetry, endpoints, determinism,
finite input failures, undercut rejection, sector nonintersection, CCW closure,
scale invariance, chord error against dense samples, sampling limits, and absence
of Autodesk imports in core. A 189-case parameter grid covers angles, modules,
backlash and tooth counts; it is one parameterized unittest method.

This does not certify the full continuous parameter space, mechanical strength,
manufacturing tolerances or pair interference throughout rotation. The next stage
is fixed-center-distance tooth-count and ratio solving, including pair-level
backlash allocation and pair geometry validation. Fusion creation/UI remain
unimplemented and all Fusion manual checks remain outstanding.
