"""The exception hierarchy shared across every layer of rocket_physics.

A plain Python exception, not a return code: callers catch `RocketPhysicsError` (or a specific
subclass) rather than checking a status field. Integrator failures carry the state at failure as
part of debuggability (§10).
"""

from __future__ import annotations


class RocketPhysicsError(Exception):
    """Base class for every exception raised by this package."""


class ConfigError(RocketPhysicsError):
    """A configuration object failed validation or is otherwise invalid."""


class ModelError(RocketPhysicsError):
    """A physics model (atmosphere, aero, thrust, ...) received invalid input or cannot produce
    an output for the given state."""


class IntegrationError(RocketPhysicsError):
    """The numerical integrator could not complete a run."""


class StepFailure(IntegrationError):
    """A single integration step failed (e.g. a non-finite derivative)."""


class ConvergenceError(RocketPhysicsError):
    """An iterative algorithm (optimizer, event bisection) failed to converge."""


class Cancelled(RocketPhysicsError):
    """A run was cancelled via a `ProgressSink` callback (see `progress.py`)."""
