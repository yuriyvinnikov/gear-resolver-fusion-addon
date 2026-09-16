# Corrected mathematical helper contracts

These project-owned primitives replace the audited Study Gears helper behaviors;
no helper source is imported. Regression fixtures refer to the revisions recorded
in study-gears-source-lock.json.

`core/geometry/planar.py` provides finite immutable Vec2 values (XY only) and
`segment_intersection`. Unique intersections, including endpoints and the origin,
are returned as Vec2; disjoint segments return None. Zero-length segments and
nonunique collinear overlaps raise ValueError. The positive displacement from the
first segment origin fixes the audited sign error. Length tolerance is explicit
and scales the parallel test; callers must distinguish `is None` from a point.

`core/numerics.py` provides `bisect_root`: finite interval and evaluations,
positive parameter/residual tolerances, sign bracket or endpoint root, bounded
iterations. Same-sign nonroot endpoints raise NoRootError, not a fake root at the
nearest endpoint. Collapse without acceptable residual and iteration exhaustion
raise ConvergenceError. Continuity is a caller precondition. Even-multiplicity
roots without a sign bracket require a different method and are not guessed.

Run `python -m unittest discover -s tests -v` with PYTHONPATH=src. The helper
suite contains 14 tests including the two confirmed upstream defect fixtures.
The restricted spur envelope uses analytical joins, so it needs Vec2 but does
not need a root solver or segment-intersection search during profile generation.
