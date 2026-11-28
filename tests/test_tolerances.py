"""The tolerance registry (RP-001, §10). Seam: the five named families every numeric test must
import instead of writing a tolerance inline.

Expected numbers below are transcribed independently from architecture-stage1.md §10, not derived
from how tolerances.py computes them — if a transcription drifts from the spec, this is the test
that should catch it.
"""

from tolerances import ANALYTIC, CROSSCHECK_V1, PERF, REGRESSION, VALIDATION_FX27


def test_all_five_families_are_defined() -> None:
    # Presence + correct public names is the contract every other test relies on.
    assert ANALYTIC is not None
    assert REGRESSION is not None
    assert CROSSCHECK_V1 is not None
    assert VALIDATION_FX27 is not None
    assert PERF is not None


def test_analytic_is_the_tightest_relative_tolerance() -> None:
    assert ANALYTIC.rtol == 1e-10


def test_regression_is_looser_than_analytic() -> None:
    assert REGRESSION.rtol == 1e-8
    assert REGRESSION.rtol > ANALYTIC.rtol


def test_crosscheck_v1_is_an_absolute_tolerance_on_apogee_metres() -> None:
    assert CROSSCHECK_V1.atol == 1e-6
    assert CROSSCHECK_V1.rtol is None


def test_validation_fx27_is_percent_level_and_the_loosest_numeric_family() -> None:
    assert VALIDATION_FX27.rtol == 1e-2
    assert VALIDATION_FX27.rtol > CROSSCHECK_V1.atol


def test_perf_budgets_match_the_table_in_section_10() -> None:
    # §10 performance budgets table, transcribed in seconds.
    assert PERF["flight_6dof_60s_1khz_seconds"] == 2.0
    assert PERF["monte_carlo_1000_100hz_seconds"] == 60.0
    assert PERF["apogee_targeting_50_flights_seconds"] == 60.0
    assert PERF["import_rocket_physics_seconds"] == 0.150
