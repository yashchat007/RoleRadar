import pytest

from app.discovery.playwright_retry import _is_transient, goto_with_retry


def test_is_transient_detects_connection_reset():
    assert _is_transient(Exception("net::ERR_CONNECTION_RESET"))


def test_is_transient_ignores_unknown():
    assert not _is_transient(Exception("selector not found"))


@pytest.mark.asyncio
async def test_goto_with_retry_succeeds_after_transient():
    calls = 0

    class Page:
        async def goto(self, url, wait_until=None, timeout=None):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise Exception("net::ERR_CONNECTION_RESET")
            return None

    await goto_with_retry(Page(), "https://example.com", max_attempts=3, base_delay_sec=0.01)
    assert calls == 2


@pytest.mark.asyncio
async def test_goto_with_retry_raises_after_max_attempts():
    class Page:
        async def goto(self, url, wait_until=None, timeout=None):
            raise Exception("net::ERR_CONNECTION_RESET")

    with pytest.raises(Exception, match="ERR_CONNECTION_RESET"):
        await goto_with_retry(Page(), "https://example.com", max_attempts=2, base_delay_sec=0.01)
