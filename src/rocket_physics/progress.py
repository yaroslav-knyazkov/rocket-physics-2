"""The progress-reporting seam (§4.4).

The core never prints and never configures logging. Anything observable from outside is either a
returned value or a call to a `ProgressSink` callback supplied by the caller. `NullSink` is the
default adapter: it discards every callback silently.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ProgressSink(Protocol):
    """Receives progress callbacks from a long-running simulation or optimization."""

    def on_step(self, frac: float, message: str) -> None:
        """Report that a run is `frac` (0.0-1.0) of the way through, with a human-readable
        `message`. Implementations must not raise for a well-formed call."""


class NullSink:
    """A `ProgressSink` that discards every callback. The default when the caller supplies none."""

    def on_step(self, frac: float, message: str) -> None:
        return None
