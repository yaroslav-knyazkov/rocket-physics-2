"""The single home of every numerical tolerance used by this test suite (§10).

No test may define a tolerance locally — import the family constant you need from here instead.
Loosening a tolerance is then a one-line, reviewable diff in this file, not a quiet edit buried
inside a test.

Five families, tightest to loosest:
  ANALYTIC         closed-form oracles (vacuum ballistic, const-thrust, ...).
  REGRESSION       committed golden trajectories.
  CROSSCHECK_V1    differential tests against rocket-physics v1 (opt-in, marker `crosscheck`).
  VALIDATION_FX27  real fx27 reference numbers (opt-in, marker `validation`); percent-level and
                   oracle-dependent — individual validation tests may loosen further, but never
                   tighten past this ceiling without updating it here.
  PERF             wall-clock budgets (opt-in, marker `perf`), in seconds.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToleranceSpec:
    """A named numerical tolerance. Exactly one of `rtol`/`atol` is expected to be set for most
    families, but both may be provided where `numpy.testing.assert_allclose`-style combination is
    useful."""

    rtol: float | None
    atol: float | None
    description: str


ANALYTIC = ToleranceSpec(
    rtol=1e-10,
    atol=None,
    description="relative tolerance vs closed-form analytic solutions (§10)",
)

REGRESSION = ToleranceSpec(
    rtol=1e-8,
    atol=None,
    description="relative tolerance vs committed golden trajectories (§10)",
)

CROSSCHECK_V1 = ToleranceSpec(
    rtol=None,
    atol=1e-6,
    description="absolute tolerance on apogee (metres) vs rocket-physics v1 (§10)",
)

VALIDATION_FX27 = ToleranceSpec(
    rtol=1e-2,
    atol=None,
    description=(
        "percent-level relative ceiling vs fx27 reference data; oracle-dependent, far looser "
        "against real flight data (§10)"
    ),
)

# Wall-clock performance budgets (§10), in seconds. Not an accuracy tolerance, but kept in the
# same single-home file so a budget change is equally visible.
PERF: dict[str, float] = {
    "flight_6dof_60s_1khz_seconds": 2.0,
    "monte_carlo_1000_100hz_seconds": 60.0,
    "apogee_targeting_50_flights_seconds": 60.0,
    "import_rocket_physics_seconds": 0.150,
}
