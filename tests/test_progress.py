"""ProgressSink protocol + NullSink (RP-001). Seam: how the core reports progress without
printing — §4.4 forbids print/logging from the core, this callback is the only escape hatch."""

from rocket_physics.progress import NullSink, ProgressSink


def test_null_sink_satisfies_the_progress_sink_protocol() -> None:
    sink: ProgressSink = NullSink()
    assert isinstance(sink, ProgressSink)


def test_null_sink_on_step_is_a_no_op() -> None:
    sink = NullSink()
    # Must accept the full signature and do nothing observable — no print, no exception,
    # no return value used by the caller.
    assert sink.on_step(0.0, "start") is None
    assert sink.on_step(1.0, "done") is None
