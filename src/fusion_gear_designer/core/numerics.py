"""Project-owned bounded scalar root solver; no endpoint-as-root fallback."""

from collections.abc import Callable
from math import isfinite


class NoRootError(ValueError):
    """The supplied interval does not bracket a root."""


class ConvergenceError(ValueError):
    """The requested numerical accuracy could not be achieved."""


def bisect_root(function: Callable[[float], float], left: float, right: float,
                *, x_tolerance: float = 1e-12, residual_tolerance: float = 1e-12,
                max_iterations: int = 200) -> float:
    """Require a continuous function and a sign bracket, or an endpoint root.

    A small interval alone is insufficient: a returned point must satisfy the
    residual tolerance. No solution, nonfinite evaluation and stagnation fail.
    """
    if not all(isfinite(x) for x in (left, right, x_tolerance, residual_tolerance)):
        raise ValueError("Root inputs must be finite.")
    if x_tolerance <= 0 or residual_tolerance <= 0:
        raise ValueError("Root tolerances must be positive.")
    if type(max_iterations) is not int or max_iterations < 1:
        raise ValueError("Iteration limit must be a positive integer.")
    left, right = sorted((left, right))

    def evaluate(x: float) -> float:
        value = function(x)
        if not isfinite(value):
            raise ValueError("Root function returned a nonfinite value.")
        return value

    fl, fr = evaluate(left), evaluate(right)
    if abs(fl) <= residual_tolerance:
        return left
    if abs(fr) <= residual_tolerance:
        return right
    if (fl > 0) == (fr > 0):
        raise NoRootError("Interval does not bracket a root.")
    for _ in range(max_iterations):
        middle = left / 2 + right / 2
        fm = evaluate(middle)
        if abs(fm) <= residual_tolerance:
            return middle
        if right - left <= x_tolerance or middle <= left or middle >= right:
            raise ConvergenceError("Root interval collapsed without an acceptable residual.")
        if (fl > 0) == (fm > 0):
            left, fl = middle, fm
        else:
            right = middle
    raise ConvergenceError("Root iteration limit exceeded.")
