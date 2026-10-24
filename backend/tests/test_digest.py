import pytest

from app.services.digest import build_digest_for_user, send_daily_digest

# build_digest_for_user is async and needs session — test compute path via match tests instead.
# Smoke import only.


def test_digest_module_imports():
    assert build_digest_for_user is not None


@pytest.mark.asyncio
async def test_send_daily_digest_disabled():
    from types import SimpleNamespace

    user = SimpleNamespace(email_digest_enabled=False, email="dev@roleradar.local")
    result = await send_daily_digest(SimpleNamespace(), user)
    assert result.sent is False
    assert result.status == "disabled"
