import math
import unittest

from fusion_gear_designer.core.geometry.planar import Vec2, segment_intersection
from fusion_gear_designer.core.numerics import bisect_root, NoRootError, ConvergenceError


class IntersectionTests(unittest.TestCase):
    def test_upstream_sign_regression(self):
        # Pinned upstream cross_point returns (-1, 0), outside both segments.
        p = segment_intersection(Vec2(0, 0), Vec2(2, 0), Vec2(1, -1), Vec2(1, 1))
        self.assertEqual(p, Vec2(1, 0))

    def test_origin_intersection_is_not_absence(self):
        self.assertEqual(segment_intersection(Vec2(-1, 0), Vec2(1, 0),
                                             Vec2(0, -1), Vec2(0, 1)), Vec2(0, 0))

    def test_disjoint_and_parallel(self):
        for q, end in ((Vec2(2, -1), Vec2(2, 1)), (Vec2(0, 1), Vec2(1, 1)),
                       (Vec2(2, 0), Vec2(3, 0))):
            self.assertIsNone(segment_intersection(Vec2(0, 0), Vec2(1, 0), q, end))

    def test_endpoints_and_reversal(self):
        for a, b in ((Vec2(0, 0), Vec2(1, 0)), (Vec2(1, 0), Vec2(0, 0))):
            self.assertEqual(segment_intersection(a, b, Vec2(1, 0), Vec2(2, 0)), Vec2(1, 0))

    def test_overlap_and_degenerate_fail(self):
        with self.assertRaisesRegex(ValueError, "overlap"):
            segment_intersection(Vec2(0, 0), Vec2(2, 0), Vec2(1, 0), Vec2(3, 0))
        with self.assertRaisesRegex(ValueError, "Degenerate"):
            segment_intersection(Vec2(0, 0), Vec2(0, 0), Vec2(1, 0), Vec2(2, 0))

    def test_nearly_parallel_crossing(self):
        p = segment_intersection(Vec2(0, 0), Vec2(1, 1e-6),
                                 Vec2(0, 1e-6), Vec2(1, 0))
        self.assertAlmostEqual(p.x, 0.5)

    def test_invalid_tolerance(self):
        for tol in (0, -1, math.nan):
            with self.assertRaises(ValueError):
                segment_intersection(Vec2(0, 0), Vec2(1, 0), Vec2(0, 1), Vec2(1, 1),
                                     tolerance_mm=tol)


class RootTests(unittest.TestCase):
    def test_upstream_nonroot_regression(self):
        # Upstream returns 0 even though f(0)=1 and no real root exists.
        with self.assertRaises(NoRootError):
            bisect_root(lambda x: x*x + 1, 0, 1)

    def test_valid_root_and_reversed_interval(self):
        for left, right in ((0, 2), (2, 0)):
            result = bisect_root(lambda x: x*x - 2, left, right)
            self.assertLessEqual(abs(result*result - 2), 1e-12)

    def test_endpoint_roots(self):
        self.assertEqual(bisect_root(lambda x: x, 0, 1), 0)
        self.assertEqual(bisect_root(lambda x: x - 1, 0, 1), 1)

    def test_discontinuous_sign_jump_is_not_root(self):
        with self.assertRaises(ConvergenceError):
            bisect_root(lambda x: -1 if x < 0.3 else 1, 0, 1)

    def test_nonfinite_function_and_inputs(self):
        with self.assertRaises(ValueError):
            bisect_root(lambda x: math.nan, 0, 1)
        with self.assertRaises(ValueError):
            bisect_root(lambda x: x, 0, math.inf)
        with self.assertRaises(ValueError):
            bisect_root(lambda x: x, 0, 1, x_tolerance=0)

    def test_iteration_limit(self):
        with self.assertRaises(ConvergenceError):
            bisect_root(lambda x: x*x - 2, 0, 2, max_iterations=1)

    def test_large_sign_values_do_not_require_product(self):
        self.assertEqual(bisect_root(lambda x: x*1e300, -1, 1), 0)
