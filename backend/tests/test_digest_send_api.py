from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_digest_send_returns_503_when_smtp_fails():
    transport = ASGITransport(app=app)
    with patch("app.services.digest.send_email", side_effect=OSError("Connection refused")):
        with patch("app.services.digest.build_digest_for_user", return_value=("line1", "<p>x</p>")):
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                res = await client.post("/api/v1/digest/send")
    assert res.status_code == 503
    assert "Connection refused" in res.json()["detail"]


@pytest.mark.asyncio
async def test_send_daily_digest_no_content_is_not_sent():
    from types import SimpleNamespace

    from app.services.digest import send_daily_digest

    user = SimpleNamespace(email_digest_enabled=True, email="dev@roleradar.local")
    with patch("app.services.digest.build_digest_for_user", return_value=None):
        result = await send_daily_digest(SimpleNamespace(), user, force=True)
    assert result.sent is False
    assert result.status == "no_content"
