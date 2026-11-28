"""Error hierarchy (RP-001). Seam: the public exception classes importers catch."""

from rocket_physics.errors import (
    Cancelled,
    ConfigError,
    ConvergenceError,
    IntegrationError,
    ModelError,
    RocketPhysicsError,
    StepFailure,
)


def test_all_errors_derive_from_the_common_base() -> None:
    for exc_type in (
        ConfigError,
        ModelError,
        IntegrationError,
        StepFailure,
        ConvergenceError,
        Cancelled,
    ):
        assert issubclass(exc_type, RocketPhysicsError)


def test_step_failure_is_an_integration_error() -> None:
    assert issubclass(StepFailure, IntegrationError)


def test_errors_carry_a_message_like_a_normal_exception() -> None:
    exc = IntegrationError("step 42 produced a non-finite derivative")
    assert str(exc) == "step 42 produced a non-finite derivative"
