"""Pure fixed-axis external spur pair solving."""

from .spur_pair import PairDefinition, SpurPairSolution, CenterDistanceTolerance, solve_tooth_counts, solve_axis_pair
from .ratio_search import RatioCandidate, NoPairSolutionError, search_ratio, search_axis_ratio

__all__ = ["PairDefinition", "SpurPairSolution", "CenterDistanceTolerance",
           "solve_tooth_counts", "solve_axis_pair", "RatioCandidate",
           "NoPairSolutionError", "search_ratio", "search_axis_ratio"]
