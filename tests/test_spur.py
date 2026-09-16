import ast
import math
from pathlib import Path
import unittest

from fusion_gear_designer.core.gears.spur import SpurGearSpec
from fusion_gear_designer.core.gears.involute import involute_point
from fusion_gear_designer.core.gears.study_gears_profile import (
    flank_point, rack_geometry, root_point, generate_spur_profile, gear_outline,
)
from fusion_gear_designer.core.geometry.planar import Vec2, segment_intersection


class SpurDimensionsTests(unittest.TestCase):
    def test_standard_dimensions(self):
        s = SpurGearSpec(1.5, 20, backlash_mm=0.075)
        self.assertEqual(s.pitch_diameter_mm, 30)
        self.assertEqual(s.pitch_radius_mm, 15)
        self.assertAlmostEqual(s.base_radius_mm, 15*math.cos(math.radians(20)))
        self.assertEqual(s.outside_radius_mm, 16.5)
        self.assertEqual(s.root_radius_mm, 13.125)
        self.assertAlmostEqual(s.circular_pitch_mm, 1.5*math.pi)
        self.assertAlmostEqual(s.angular_pitch_rad, math.pi/10)
        self.assertAlmostEqual(s.tooth_thickness_mm, .75*math.pi-.075)

    def test_small_module(self):
        self.assertAlmostEqual(SpurGearSpec(.001, 20).pitch_radius_mm, .01)
        self.assertTrue(generate_spur_profile(SpurGearSpec(.001, 20)).tooth_sector)

    def test_invalid_inputs(self):
        cases = [dict(module_mm=0), dict(module_mm=-1), dict(module_mm=math.nan),
                 dict(module_mm=1e-300), dict(module_mm=1e300),
                 dict(teeth=True), dict(teeth=20.0), dict(teeth=0), dict(teeth=401),
                 dict(backlash_mm=-1), dict(backlash_mm=math.inf), dict(backlash_mm=10),
                 dict(thickness_mm=0), dict(pressure_angle_rad=math.radians(10)),
                 dict(pressure_angle_rad=math.radians(31))]
        for changes in cases:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                SpurGearSpec(**(dict(module_mm=1.5, teeth=20) | changes))

    def test_low_tooth_domain_is_explicit(self):
        for angle, minimum in ((14.5, 32), (20, 18), (30, 18)):
            with self.subTest(angle=angle):
                s = SpurGearSpec(1, minimum, math.radians(angle))
                self.assertEqual(s.minimum_teeth, minimum)
                self.assertTrue(generate_spur_profile(s).lower_root)
                with self.assertRaisesRegex(ValueError, "undercut"):
                    SpurGearSpec(1, minimum-1, math.radians(angle))

    def test_pointed_tip_rejected_before_generation(self):
        with self.assertRaisesRegex(ValueError, "tip"):
            SpurGearSpec(1, 18, backlash_mm=1)


class InvoluteTests(unittest.TestCase):
    def test_base_circle_point(self):
        self.assertEqual(involute_point(10, 0), Vec2(10, 0))

    def test_radial_progression(self):
        radii = [involute_point(10, i/100).length for i in range(101)]
        self.assertTrue(all(b > a for a, b in zip(radii, radii[1:])))
        for i, radius in enumerate(radii):
            self.assertAlmostEqual(radius, 10*math.sqrt(1+(i/100)**2))

    def test_invalid_domain(self):
        for radius, parameter in ((0, 0), (-1, 1), (1, -1), (math.inf, 0), (1, math.nan)):
            with self.assertRaises(ValueError):
                involute_point(radius, parameter)

    def test_adapted_rack_envelope_matches_analytic_involute(self):
        for teeth, angle in ((18, 20), (32, 14.5), (40, 30), (400, 20)):
            s = SpurGearSpec(1.5, teeth, math.radians(angle), .075)
            rotation = (-s.tooth_thickness_mm/(2*s.pitch_radius_mm)
                        -(math.tan(s.pressure_angle_rad)-s.pressure_angle_rad))
            for u in (0, .001, .1, .3, .6):
                with self.subTest(teeth=teeth, u=u):
                    expected = involute_point(s.base_radius_mm, u).rotate(rotation)
                    self.assertLess((flank_point(s, u)-expected).length, 1e-10)

    def test_pitch_thickness_and_backlash(self):
        for backlash in (0, .075, .15):
            s = SpurGearSpec(1.5, 20, backlash_mm=backlash)
            point = flank_point(s, math.tan(s.pressure_angle_rad))
            self.assertAlmostEqual(point.length, s.pitch_radius_mm)
            thickness = -2*math.atan2(point.y, point.x)*s.pitch_radius_mm
            self.assertAlmostEqual(thickness, s.tooth_thickness_mm)


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.spec = SpurGearSpec(1.5, 20, backlash_mm=.075)
        self.profile = generate_spur_profile(self.spec)

    def test_symmetry(self):
        p = self.profile
        self.assertEqual(p.upper_flank, tuple(q.mirror_y() for q in reversed(p.lower_flank)))
        self.assertEqual(p.upper_root, tuple(q.mirror_y() for q in reversed(p.lower_root)))

    def test_root_circle_and_tip_radii(self):
        p, s = self.profile, self.spec
        self.assertAlmostEqual(p.lower_root[0].length, s.root_radius_mm)
        self.assertAlmostEqual(p.lower_flank[-1].length, s.outside_radius_mm)
        for point in p.root_gap:
            self.assertAlmostEqual(point.length, s.root_radius_mm)
        for point in p.tip:
            self.assertAlmostEqual(point.length, s.outside_radius_mm)

    def test_analytic_root_join_and_tangent(self):
        for teeth in (18, 20, 40, 400):
            s = SpurGearSpec(1.5, teeth)
            rack = rack_geometry(s)
            join = flank_point(s, rack.join_involute_parameter)
            self.assertLess((root_point(s, rack, rack.join_roll_rad)-join).length, 1e-10)
            delta = 1e-7
            # Root traversal goes from bottom toward smaller roll values.
            root_tangent = join-root_point(s, rack, rack.join_roll_rad+delta)
            flank_tangent = flank_point(s, rack.join_involute_parameter+delta)-join
            cosine = root_tangent.dot(flank_tangent)/(root_tangent.length*flank_tangent.length)
            self.assertGreater(cosine, .99999)

    def test_continuous_joins(self):
        p = self.profile
        segments = (p.lower_root, p.lower_flank, p.tip, p.upper_flank, p.upper_root, p.root_gap)
        for first, second in zip(segments, segments[1:]):
            self.assertEqual(first[-1], second[0])
        self.assertEqual(p.root_gap[-1], p.lower_root[0].rotate(self.spec.angular_pitch_rad))

    def test_deterministic_output(self):
        self.assertEqual(self.profile, generate_spur_profile(self.spec))
        self.assertEqual(gear_outline(self.spec), gear_outline(self.spec))

    def test_sector_has_no_nonadjacent_intersections(self):
        for teeth, angle in ((18, 20), (32, 14.5), (18, 30), (400, 20)):
            p = generate_spur_profile(SpurGearSpec(1, teeth, math.radians(angle))).tooth_sector
            for i in range(len(p)-1):
                for j in range(i+2, len(p)-1):
                    self.assertIsNone(segment_intersection(p[i], p[i+1], p[j], p[j+1]))

    def test_outline_closed_ccw_and_confined_to_sectors(self):
        points = gear_outline(self.spec)
        self.assertEqual(points[0], points[-1])
        self.assertTrue(all((b-a).length > 1e-10 for a, b in zip(points, points[1:])))
        self.assertGreater(sum(a.cross(b) for a, b in zip(points, points[1:])), 0)
        start = math.atan2(self.profile.lower_root[0].y, self.profile.lower_root[0].x)
        for p in self.profile.tooth_sector:
            angle = math.atan2(p.y, p.x)
            self.assertGreaterEqual(angle+1e-12, start)
            self.assertLessEqual(angle-1e-12, start+self.spec.angular_pitch_rad)

    def test_scale_invariance(self):
        for scale in (.001, 1000):
            other = generate_spur_profile(SpurGearSpec(1.5*scale, 20, backlash_mm=.075*scale))
            self.assertEqual(len(self.profile.tooth_sector), len(other.tooth_sector))
            for a, b in zip(self.profile.tooth_sector, other.tooth_sector):
                self.assertLess((a-b*(1/scale)).length, 1e-10)

    def test_chord_error_against_dense_analytic_samples(self):
        s = self.spec
        rack = rack_geometry(s)
        end = math.sqrt((s.outside_radius_mm/s.base_radius_mm)**2-1)
        curves = ((self.profile.lower_flank, lambda u: flank_point(s,u), rack.join_involute_parameter, end),
                  (self.profile.lower_root, lambda t: root_point(s,rack,t), rack.bottom_roll_rad, rack.join_roll_rad))
        for points, curve, start, finish in curves:
            count = len(points)-1
            for i in range(count):
                for fraction in (.1,.25,.5,.75,.9):
                    t = start+(finish-start)*(i+fraction)/count
                    chord = points[i]*(1-fraction)+points[i+1]*fraction
                    self.assertLessEqual((curve(t)-chord).length, self.profile.chord_tolerance_mm*1.000001)

    def test_sampling_tolerance_and_resource_limit(self):
        for tolerance in (0, -1, math.nan, 1):
            with self.assertRaises(ValueError):
                generate_spur_profile(self.spec, chord_tolerance_mm=tolerance)
        with self.assertRaisesRegex(ValueError, "limit"):
            generate_spur_profile(self.spec, chord_tolerance_mm=1e-16)
        with self.assertRaisesRegex(ValueError, "limit"):
            generate_spur_profile(self.spec, chord_tolerance_mm=1e-320)
        finer = generate_spur_profile(self.spec, chord_tolerance_mm=.00015)
        self.assertGreater(len(finer.tooth_sector), len(self.profile.tooth_sector))

    def test_width_limited_root_has_no_zero_length_gap(self):
        s = SpurGearSpec(1, 18, math.radians(30))
        p = generate_spur_profile(s)
        self.assertEqual(len(p.root_gap), 1)
        outline = gear_outline(s)
        self.assertTrue(all((b-a).length > 1e-10 for a,b in zip(outline, outline[1:])))

    def test_supported_parameter_grid(self):
        for angle in (14.5, 17.5, 20, 22.5, 25, 27.5, 30):
            for module in (.001, 1.5, 1000):
                for backlash_fraction in (0, .05, .2):
                    reference = SpurGearSpec(module, 400, math.radians(angle), module*backlash_fraction)
                    for teeth in (reference.minimum_teeth, 40, 400):
                        with self.subTest(angle=angle,module=module,teeth=teeth,backlash=backlash_fraction):
                            s = SpurGearSpec(module, teeth, math.radians(angle), module*backlash_fraction)
                            p = generate_spur_profile(s)
                            points = p.tooth_sector
                            angles = [math.atan2(q.y,q.x) for q in points]
                            self.assertTrue(all(b >= a-1e-12 for a,b in zip(angles, angles[1:])))
                            for q in points:
                                self.assertGreaterEqual(q.length/module, s.root_radius_mm/module-1e-10)
                                self.assertLessEqual(q.length/module, s.outside_radius_mm/module+1e-10)

    def test_core_has_no_autodesk_import(self):
        core = Path(__file__).resolve().parents[1]/'src/fusion_gear_designer/core'
        for file in core.rglob('*.py'):
            for node in ast.walk(ast.parse(file.read_text(encoding='utf-8'))):
                if isinstance(node, ast.Import):
                    self.assertFalse(any(a.name.split('.')[0] == 'adsk' for a in node.names), str(file))
                elif isinstance(node, ast.ImportFrom):
                    self.assertNotEqual((node.module or '').split('.')[0], 'adsk', str(file))
