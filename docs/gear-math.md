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

## Implemented standard external spur model

Lengths are millimeters, angles radians. No profile shift or helix angle.
Module m, integer teeth z, pressure angle alpha, per-gear thickness reduction b:

- Pitch diameter `d=m*z`, pitch radius `rp=d/2`, base radius `rb=rp*cos(alpha)`.
- Outside radius `ra=rp+m`; root radius `rf=rp-1.25*m`.
- Circular pitch `pi*m`, angular pitch `2*pi/z`.
- Pitch tooth thickness `s=pi*m/2-b`. Here `backlash_mm` is the **per-gear**
  reduction. Future pair input B should use b=B/2 on each gear for equal sharing.
- Thickness is positive and explicit; the 2D outline is independent of it.

Numerical domain: `1e-6 <= m <= 1e6` mm, `14.5 <= alpha <= 30` degrees,
up to 400 teeth. Reject nonfinite values, noninteger counts, negative backlash,
zero/negative thickness and nonpositive tip width.

## Adapted rack envelope

Let `rho=min(.25*m/(1-sin(alpha)),
(pi*m/4+b/2-1.25*m*tan(alpha))*tan(pi/4+alpha/2))`.
The second bound prevents the rack-tip fillet center crossing the tooth-gap
center. Its center is
`C=(rp-1.25*m+rho, b/2-1.25*m*tan(alpha)-rho/tan(pi/4+alpha/2))`.
Tangent height `h=-1.25*m+rho*(1-sin(alpha))`.
The supported tooth minimum is `max(18, ceil(2*(-h/m)/sin(alpha)^2))`.
This excludes the returning/undercut involute branch for this rack geometry.

For the lower flank, unwinding parameter `u>=0`, rack roll
`t=u-tan(alpha)+b/(2*rp)`, and `k=rp*(u-tan(alpha))`:

`P(u)=R(t-pi/(2*z)) * (rp+k*sin(alpha)*cos(alpha), -k*cos(alpha)^2)`.

This is the algebraic reduction of Study Gears' straight rack envelope. It agrees
with the canonical involute `rb*(cos(u)+u*sin(u), sin(u)-u*cos(u))` rotated by
`-s/(2*rp) - (tan(alpha)-alpha)`. Its radius is `rb*sqrt(1+u^2)`.
The profile uses `u_join=tan(alpha)+h/(rp*sin(alpha)*cos(alpha))` through
`u_tip=sqrt((ra/rb)^2-1)`, not necessarily the whole base-to-tip involute.

For the root circle envelope, `D=rp-C.x`, `V=(D,rp*t-C.y)`:

`Q(t)=R(t-pi/(2*z))*((C.x,C.y-rp*t)-rho*V/|V|)`.

Traverse from `t_bottom=C.y/rp` to
`t_join=(b/2+h/(sin(alpha)*cos(alpha)))/rp`.
This branch joins the involute tangentially and terminates on rf. Mirror across X
for the upper flank/root. Tip and root-gap arcs are circular. A width-limited
root has a zero-length gap arc, represented by one endpoint rather than a line.
The tooth center is +X; a CCW sector extends between consecutive gap bottoms.

## Approximation and limits

Each analytic curve is uniformly sampled with enough segments that
`M*delta_t^2/8 <= tolerance`, where M bounds the second derivative norm.
For the involute `M=rb*sqrt(1+u_tip^2)`; for circular arcs M is the radius.
The root bound is `max|(C.x,C.y-rp*t)|+2*rp +
rho*(1+2*rp/D+3*(rp/D)^2)`. Endpoint replacement only removes floating-point
roundoff at analytic joins. The default chord tolerance is `.001*m`, maximum
`.01*m`; requests needing over 4096 segments per curve fail explicitly.
This bounds polyline interpolation, not any future fitted spline.

No undercut trimming, arbitrary rack fillets, profile shift, tip fillet, load
rating, pair interference validation or manufacturing guarantee is implemented.
For a future unshifted pair, `a=m*(z1+z2)/2`; the pair solver is the next stage.
