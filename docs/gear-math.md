# Mathematical conventions

## Implemented axis geometry

Origins and distances are millimeters; angles are radians. Directions are
dimensionless unit vectors. A line is `p(t) = origin + t * direction` with `t`
in millimeters. Lines are infinite, not finite shaft segments.

For unit directions u, v and origin displacement d:

- Unoriented shaft angle: `atan2(|u cross v|, |u dot v|)`, in [0, pi/2].
- Directed vector angle: `atan2(|u cross v|, u dot v)`, in [0, pi].
- Nonparallel infinite-line distance: `|d dot normalize(u cross v)|`.
- Parallel infinite-line distance: `|d cross u|`.

Classification uses inclusive tolerances: angle <= 1e-8 rad means parallel;
otherwise distance <= 1e-6 mm means intersecting; otherwise skew. These defaults
are centralized in `GeometryTolerance`, and callers may supply alternatives.
No geometric comparison of floating-point coordinates uses exact equality.
The zero-length cross-product branch is an arithmetic degeneracy check, not
a tolerance-based relationship decision.

For almost parallel axes, their global shortest distance can be zero even with
substantial local separation. `shortest_distance_mm` preserves that true distance.
`parallel_spacing_mm` separately measures distance from the **first axis origin**
to the second line. It is populated only for axes classified as parallel and is
an explicitly local approximation. With nonzero angular deviation it can depend
on origin choice/order. Future placement must use that same axial reference and
consider deviation over the gear thickness. No placement is implemented yet.

`coincident_within_tolerance` means classified parallel and local spacing within
distance tolerance; it does not assert exact identity of infinite lines.

## Planned spur model (not implemented)

Standard, external, unshifted involute gears: `d = m*z`, `a = m*(z1+z2)/2`.
Backlash distribution, supported tooth range, root treatment and discretization
must be documented during implementation, after reviewing Study Gears. No gear
geometry, load rating or manufacturing suitability is claimed at this stage.
