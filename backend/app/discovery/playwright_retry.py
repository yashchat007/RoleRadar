"""Bounded retries for Playwright navigation (transient network resets)."""

from __future__ import annotations

import asyncio
import logging
import re

logger = logging.getLogger(__name__)

_TRANSIENT_MARKERS = (
    "ERR_CONNECTION_RESET",
    "ERR_CONNECTION_CLOSED",
    "ERR_NETWORK_CHANGED",
    "ERR_INTERNET_DISCONNECTED",
    "Timeout",
    "timeout",
    "NS_ERROR_NET_RESET",
)


def _is_transient(exc: BaseException) -> bool:
    msg = str(exc)
    return any(m in msg for m in _TRANSIENT_MARKERS)


async def goto_with_retry(
    page,
    url: str,
    *,
    wait_until: str = "domcontentloaded",
    timeout_ms: int = 120_000,
    max_attempts: int = 3,
    base_delay_sec: float = 2.0,
    label: str = "",
) -> None:
    last_exc: BaseException | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            await page.goto(url, wait_until=wait_until, timeout=timeout_ms)
            return
        except Exception as e:
            last_exc = e
            if attempt >= max_attempts or not _is_transient(e):
                raise
            delay = base_delay_sec * (2 ** (attempt - 1))
            logger.warning(
                "Navigation failed for %s (attempt %s/%s): %s; retrying in %.1fs",
                label or url,
                attempt,
                max_attempts,
                _short_err(e),
                delay,
            )
            await asyncio.sleep(delay)
    if last_exc:
        raise last_exc


def _short_err(exc: BaseException) -> str:
    text = str(exc).split("\n")[0]
    return text[:240]
