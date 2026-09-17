import math
import unittest

from fusion_gear_designer.core.geometry import Line3D, Vec3
from fusion_gear_designer.core.solver import (
    PairDefinition, CenterDistanceTolerance, NoPairSolutionError,
    solve_tooth_counts, solve_axis_pair, search_ratio, search_axis_ratio,
)
from fusion_gear_designer.core.tolerances import GeometryTolerance


class ToothCountTests(unittest.TestCase):
    def setUp(self):
        self.definition = PairDefinition(1.5)

    def test_exact_pair(self):
        s = solve_tooth_counts(45, self.definition, 20, 40)
        self.assertEqual(s.ratio, 2)
        self.assertEqual(s.required_center_distance_mm, 45)
        self.assertEqual(s.center_error_mm, 0)
        self.assertEqual(s.relative_center_error, 0)

    def test_pair_backlash_is_shared_once(self):
        s = solve_tooth_counts(45, self.definition, 20, 40)
        self.assertEqual(s.input_gear.backlash_mm, .075)
        self.assertEqual(s.output_gear.backlash_mm, .075)
        reductions = sum(g.circular_pitch_mm/2-g.tooth_thickness_mm
                         for g in (s.input_gear, s.output_gear))
        self.assertAlmostEqual(reductions, .15)

    def test_mismatch_contains_actual_and_required_values(self):
        with self.assertRaisesRegex(ValueError, r"42 mm.*20T/40T.*45 mm"):
            solve_tooth_counts(42, self.definition, 20, 40)

    def test_absolute_tolerance_boundary(self):
        tol = CenterDistanceTolerance(.001, 0)
        for sign in (-1, 1):
            for offset in (.000999, .001):
                s = solve_tooth_counts(45+sign*offset, self.definition, 20, 40, tolerance=tol)
                self.assertAlmostEqual(s.center_error_mm, offset)
                self.assertAlmostEqual(s.relative_center_error, offset/45)
                self.assertEqual(s.center_distance_mm, 45+sign*offset)
            with self.assertRaises(ValueError):
                solve_tooth_counts(45+sign*.001001, self.definition, 20, 40, tolerance=tol)

    def test_relative_tolerance(self):
        tol = CenterDistanceTolerance(0, 1e-5)
        solve_tooth_counts(45.0004, self.definition, 20, 40, tolerance=tol)
        with self.assertRaises(ValueError):
            solve_tooth_counts(45.0005, self.definition, 20, 40, tolerance=tol)

    def test_invalid_distance(self):
        for value in (0, -1, math.nan, math.inf):
            with self.assertRaises(ValueError):
                solve_tooth_counts(value, self.definition, 20, 40)

    def test_invalid_common_parameters(self):
        for changes in (dict(module_mm=0), dict(backlash_mm=-1), dict(backlash_mm=math.inf),
                        dict(backlash_mm=100), dict(thickness_mm=0), dict(pressure_angle_rad=0)):
            with self.assertRaises(ValueError):
                PairDefinition(**(dict(module_mm=1.5) | changes))

    def test_unsupported_counts(self):
        for count in (17, 401, 20.5, True):
            with self.assertRaises(ValueError):
                solve_tooth_counts(45, self.definition, count, 40)

    def test_small_module_and_zero_backlash(self):
        s = solve_tooth_counts(.03, PairDefinition(.001, backlash_mm=0), 20, 40)
        self.assertAlmostEqual(s.required_center_distance_mm, .03)

    def test_invalid_tolerances(self):
        for value in (-1, math.nan, math.inf):
            with self.assertRaises(ValueError):
                CenterDistanceTolerance(value, 0)
            with self.assertRaises(ValueError):
                CenterDistanceTolerance(0, value)


class AxisSolverTests(unittest.TestCase):
    def setUp(self):
        self.first = Line3D(Vec3(1, 2, 3), Vec3(0, 0, 1))
        self.second = Line3D(Vec3(46, 2, 100), Vec3(0, 0, -1))
        self.definition = PairDefinition(1.5)

    def test_antiparallel_and_offset_origins(self):
        self.assertEqual(solve_axis_pair(self.first,self.second,self.definition,20,40).center_distance_mm,45)

    def test_rotated_parallel_axes(self):
        first = Line3D(Vec3(5, 6, 7), Vec3(1, 1, 1))
        offset = Vec3(1, -1, 0).normalized()*45
        second = Line3D(first.point_at(50)+offset, first.direction)
        self.assertAlmostEqual(solve_axis_pair(first,second,self.definition,20,40).center_distance_mm,45)

    def test_nonparallel_rejected(self):
        for origin in (Vec3(1,2,3), Vec3(1,5,3)):
            with self.assertRaisesRegex(ValueError, "not parallel"):
                solve_axis_pair(self.first,Line3D(origin,Vec3(1,0,0)),self.definition,20,40)

    def test_coincident_rejected(self):
        with self.assertRaisesRegex(ValueError, "coincide"):
            solve_axis_pair(self.first,self.first,self.definition,20,40)

    def test_near_parallel_uses_local_spacing(self):
        a = Line3D(Vec3(0,0,0),Vec3(0,0,1))
        b = Line3D(Vec3(45,0,0),Vec3(1e-10,0,1))
        self.assertAlmostEqual(solve_axis_pair(a,b,self.definition,20,40).center_distance_mm,45)

    def test_tilt_across_thickness_rejected(self):
        b = Line3D(Vec3(46,2,3),Vec3(1e-5,0,1))
        with self.assertRaisesRegex(ValueError, "tilt"):
            solve_axis_pair(self.first,b,self.definition,20,40,
                            geometry_tolerance=GeometryTolerance(1e-6,1e-4))


class RatioSearchTests(unittest.TestCase):
    def setUp(self):
        self.definition = PairDefinition(1.5)

    def test_ranked_multiple_candidates(self):
        results = search_ratio(45,self.definition,2)
        self.assertEqual([(c.solution.input_gear.teeth,c.solution.output_gear.teeth)
                          for c in results],[(20,40),(21,39),(19,41)])
        self.assertEqual(results[0].ratio_error,0)
        self.assertAlmostEqual(results[1].relative_ratio_error,1/14)

    def test_exact_ratio_filter(self):
        self.assertEqual(len(search_ratio(45,self.definition,2,max_relative_ratio_error=0)),1)

    def test_ratio_error_boundary_is_inclusive(self):
        candidates = search_ratio(21,PairDefinition(1,backlash_mm=0),1,
                                  minimum_teeth=20,maximum_teeth=22,max_relative_ratio_error=.1)
        self.assertIn((20,22),[(c.solution.input_gear.teeth,c.solution.output_gear.teeth) for c in candidates])
        candidates = search_ratio(21,PairDefinition(1,backlash_mm=0),1,
                                  minimum_teeth=20,maximum_teeth=22,max_relative_ratio_error=.09999)
        self.assertNotIn((20,22),[(c.solution.input_gear.teeth,c.solution.output_gear.teeth) for c in candidates])

    def test_ratio_less_than_one(self):
        c = search_ratio(45,self.definition,.5)[0]
        self.assertEqual((c.solution.input_gear.teeth,c.solution.output_gear.teeth),(40,20))

    def test_deterministic_order(self):
        self.assertEqual(search_ratio(45,self.definition,2), search_ratio(45,self.definition,2))

    def test_no_integer_sum_fits(self):
        with self.assertRaisesRegex(NoPairSolutionError,"45.1"):
            search_ratio(45.1,self.definition,2)

    def test_no_ratio_solution(self):
        with self.assertRaises(NoPairSolutionError):
            search_ratio(45,self.definition,10)

    def test_subnormal_ratio_does_not_admit_infinite_error(self):
        # Previously inf > inf was false, admitting 13 impossible candidates.
        for desired in (5e-324, 1e-320):
            with self.subTest(desired=desired), self.assertRaises(NoPairSolutionError):
                search_ratio(45,self.definition,desired)

    def test_undercut_counts_excluded(self):
        with self.assertRaises(NoPairSolutionError):
            search_ratio(45,PairDefinition(1.5,math.radians(14.5)),1)

    def test_search_bounds(self):
        result = search_ratio(45,self.definition,2,minimum_teeth=20,maximum_teeth=40)
        self.assertEqual(len(result),2)
        for kwargs in (dict(minimum_teeth=17),dict(maximum_teeth=401),dict(minimum_teeth=50,maximum_teeth=40),
                       dict(minimum_teeth=True),dict(maximum_teeth=40.0)):
            with self.assertRaises(ValueError):
                search_ratio(45,self.definition,2,**kwargs)

    def test_invalid_ratios(self):
        for value in (0,-1,math.inf,math.nan):
            with self.assertRaises(ValueError):
                search_ratio(45,self.definition,value)
        for value in (-1,math.inf,math.nan):
            with self.assertRaises(ValueError):
                search_ratio(45,self.definition,2,max_relative_ratio_error=value)

    def test_center_error_has_ranking_priority(self):
        results = search_ratio(45,self.definition,2,tolerance=CenterDistanceTolerance(.8,0))
        keys = [(c.solution.center_error_mm,c.relative_ratio_error,
                 c.solution.input_gear.teeth,c.solution.output_gear.teeth) for c in results]
        self.assertEqual(keys,sorted(keys))
        self.assertTrue(any(c.solution.center_error_mm > 0 for c in results))

    def test_axis_wrapper(self):
        a = Line3D(Vec3(0,0,0),Vec3(0,0,1))
        b = Line3D(Vec3(45,0,5),Vec3(0,0,-1))
        self.assertEqual(search_axis_ratio(a,b,self.definition,2),search_ratio(45,self.definition,2))

    def test_matches_exhaustive_tooth_count_oracle(self):
        expected = set()
        for z1 in range(18,46):
            for z2 in range(18,46):
                if abs(z2/z1-1.7)/1.7 > .2:
                    continue
                try:
                    solve_tooth_counts(45,self.definition,z1,z2)
                except ValueError:
                    continue
                expected.add((z1,z2))
        actual = search_ratio(45,self.definition,1.7,maximum_teeth=45,max_relative_ratio_error=.2)
        self.assertEqual({(c.solution.input_gear.teeth,c.solution.output_gear.teeth) for c in actual},expected)
