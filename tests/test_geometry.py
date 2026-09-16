"""Analytic fixtures for the first milestone's pure geometry foundation."""

import math
import unittest

from fusion_gear_designer.core.geometry import (
    AxisRelation, Line3D, Vec3, analyze_axes, angle_between_axes,
    angle_between_vectors, shortest_distance,
)
from fusion_gear_designer.core.tolerances import GeometryTolerance


ZERO = Vec3(0, 0, 0)
X = Vec3(1, 0, 0)
Y = Vec3(0, 1, 0)
Z = Vec3(0, 0, 1)


class VectorTests(unittest.TestCase):
    def test_normalization(self):
        result = Vec3(3, 4, 0).normalized()
        self.assertAlmostEqual(result.x, 0.6)
        self.assertAlmostEqual(result.y, 0.8)
        self.assertAlmostEqual(result.length, 1)

    def test_extreme_direction_scales(self):
        for scale in (1e-300, 1e300):
            with self.subTest(scale=scale):
                result = Vec3(scale, scale, scale).normalized()
                self.assertAlmostEqual(result.length, 1)
                self.assertAlmostEqual(result.x, 1 / math.sqrt(3))

    def test_zero_direction_rejected(self):
        with self.assertRaisesRegex(ValueError, "zero vector"):
            Line3D(ZERO, ZERO)

    def test_nonfinite_coordinates_rejected(self):
        for value in (math.nan, math.inf, -math.inf):
            for coordinates in ((value, 0, 0), (0, value, 0), (0, 0, value)):
                with self.subTest(coordinates=coordinates), self.assertRaises(ValueError):
                    Vec3(*coordinates)

    def test_vector_operations(self):
        self.assertEqual(X + Y, Vec3(1, 1, 0))
        self.assertEqual(X - Y, Vec3(1, -1, 0))
        self.assertEqual(X * 3, Vec3(3, 0, 0))
        self.assertEqual(X.dot(Y), 0)
        self.assertEqual(X.cross(Y), Z)

    def test_directed_angles(self):
        self.assertAlmostEqual(angle_between_vectors(X, X * -1), math.pi)
        self.assertAlmostEqual(angle_between_vectors(X * 7, Y * 9), math.pi / 2)


class AxisTests(unittest.TestCase):
    def test_line_normalizes_direction_and_uses_mm_parameter(self):
        line = Line3D(Vec3(1, 2, 3), Z * 50)
        self.assertEqual(line.direction, Z)
        self.assertEqual(line.point_at(4), Vec3(1, 2, 7))

    def test_parallel_and_antiparallel(self):
        for direction in (Z * 7, Z * -3):
            with self.subTest(direction=direction):
                a = Line3D(ZERO, Z)
                b = Line3D(Vec3(3, 4, 19), direction)
                result = analyze_axes(a, b)
                self.assertEqual(result.relationship, AxisRelation.PARALLEL)
                self.assertAlmostEqual(result.shortest_distance_mm, 5)
                self.assertAlmostEqual(result.parallel_spacing_mm, 5)
                self.assertFalse(result.coincident_within_tolerance)
                self.assertAlmostEqual(result.angle_rad, 0)

    def test_coincident_axes(self):
        result = analyze_axes(Line3D(ZERO, Z), Line3D(Z * 42, Z * -1))
        self.assertEqual(result.relationship, AxisRelation.PARALLEL)
        self.assertTrue(result.coincident_within_tolerance)
        self.assertAlmostEqual(result.shortest_distance_mm, 0)

    def test_intersection_away_from_origins(self):
        result = analyze_axes(Line3D(Vec3(-3, 1, 2), X),
                              Line3D(Vec3(2, -5, 2), Y))
        self.assertEqual(result.relationship, AxisRelation.INTERSECTING)
        self.assertAlmostEqual(result.shortest_distance_mm, 0)
        self.assertAlmostEqual(result.angle_rad, math.pi / 2)
        self.assertIsNone(result.parallel_spacing_mm)

    def test_skew_distance(self):
        a = Line3D(ZERO, X)
        b = Line3D(Vec3(7, -4, 6), Y)
        self.assertEqual(analyze_axes(a, b).relationship, AxisRelation.SKEW)
        self.assertAlmostEqual(shortest_distance(a, b), 6)
        self.assertAlmostEqual(shortest_distance(b, a), 6)

    def test_arbitrary_spatial_orientation(self):
        # Common normal is (1, 1, -2)/sqrt(6); separation is exactly 7 mm.
        normal = Vec3(1, 1, -2).normalized()
        a = Line3D(Vec3(10, 20, 30), Vec3(1, 1, 1))
        b = Line3D(a.point_at(12) + normal * 7, Vec3(1, -1, 0))
        self.assertAlmostEqual(shortest_distance(a, b), 7)
        self.assertEqual(analyze_axes(a, b).relationship, AxisRelation.SKEW)

    def test_unoriented_angle(self):
        a = Line3D(ZERO, X)
        self.assertAlmostEqual(angle_between_axes(a, Line3D(ZERO, X * -1)), 0)
        self.assertAlmostEqual(angle_between_axes(a, Line3D(ZERO, Vec3(-1, 1, 0))), math.pi / 4)

    def test_near_parallel_inside_and_outside_tolerance(self):
        tolerance = GeometryTolerance(angle_rad=1e-6)
        a = Line3D(ZERO, X)
        for factor, expected in ((0.999, AxisRelation.PARALLEL),
                                 (1.001, AxisRelation.INTERSECTING)):
            angle = tolerance.angle_rad * factor
            b = Line3D(Vec3(0, 5, 0), Vec3(math.cos(angle), math.sin(angle), 0))
            with self.subTest(factor=factor):
                self.assertEqual(analyze_axes(a, b, tolerance).relationship, expected)

    def test_exact_angular_boundary_is_inclusive(self):
        a = Line3D(ZERO, X)
        b = Line3D(ZERO, Vec3(1, 1e-6, 0))
        tolerance = GeometryTolerance(angle_rad=angle_between_axes(a, b))
        self.assertEqual(analyze_axes(a, b, tolerance).relationship, AxisRelation.PARALLEL)

    def test_nearly_parallel_distance_is_not_local_spacing(self):
        a = Line3D(ZERO, X)
        b = Line3D(Vec3(0, 5, 0), Vec3(1, 1e-10, 0))
        result = analyze_axes(a, b)
        self.assertEqual(result.relationship, AxisRelation.PARALLEL)
        self.assertAlmostEqual(result.shortest_distance_mm, 0)
        self.assertAlmostEqual(result.parallel_spacing_mm, 5)

    def test_distance_tolerance_boundaries(self):
        tolerance = GeometryTolerance(distance_mm=1e-5)
        for factor in (0.999, 1, 1.001):
            with self.subTest(factor=factor):
                a = Line3D(ZERO, X)
                offset = Vec3(0, 0, tolerance.distance_mm * factor)
                result = analyze_axes(a, Line3D(offset, Y), tolerance)
                expected = AxisRelation.INTERSECTING if factor <= 1 else AxisRelation.SKEW
                self.assertEqual(result.relationship, expected)
                parallel = analyze_axes(a, Line3D(offset, X), tolerance)
                self.assertEqual(parallel.coincident_within_tolerance, factor <= 1)

    def test_distance_invariant_under_origin_shift_and_reversal(self):
        a = Line3D(Vec3(1, 2, 3), Vec3(2, 3, 4))
        b = Line3D(Vec3(5, -2, 8), Vec3(-1, 4, 2))
        expected = shortest_distance(a, b)
        shifted_a = Line3D(a.point_at(30), a.direction * -1)
        shifted_b = Line3D(b.point_at(-20), b.direction)
        self.assertAlmostEqual(shortest_distance(shifted_a, shifted_b), expected)


class ToleranceTests(unittest.TestCase):
    def test_invalid_tolerances(self):
        for value in (0, -1, math.nan, math.inf):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    GeometryTolerance(distance_mm=value)
                with self.assertRaises(ValueError):
                    GeometryTolerance(angle_rad=value)
        with self.assertRaises(ValueError):
            GeometryTolerance(angle_rad=math.pi / 2)


if __name__ == "__main__":
    unittest.main()
