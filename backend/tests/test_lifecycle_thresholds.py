from app.discovery.lifecycle_status import (
    MISSED_FOR_CLOSED,
    MISSED_FOR_POSSIBLY_CLOSED,
)


def test_possibly_closed_before_closed():
    assert MISSED_FOR_POSSIBLY_CLOSED < MISSED_FOR_CLOSED
    assert MISSED_FOR_POSSIBLY_CLOSED == 1
    assert MISSED_FOR_CLOSED == 3
