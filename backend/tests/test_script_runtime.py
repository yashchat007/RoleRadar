import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from app.scripts.runtime import (
    EXIT_CONFIG,
    _safe_database_label,
    setup_script_logging,
    validate_database_url,
    validate_smtp_for_alerts,
)


def test_safe_database_label_never_includes_password():
    url = "postgresql+asyncpg://roleradar:secret@127.0.0.1:5432/roleradar"
    label = _safe_database_label(url)
    assert "secret" not in label
    assert "127.0.0.1" in label


def test_validate_database_url_rejects_empty():
    with patch("app.scripts.runtime.settings") as s:
        s.database_url = ""
        assert validate_database_url() is not None


def test_validate_smtp_skipped_on_dry_run():
    with patch("app.scripts.runtime.settings") as s:
        s.smtp_host = ""
        assert validate_smtp_for_alerts(dry_run=True) is None
        assert validate_smtp_for_alerts(dry_run=False) is not None


def test_setup_script_logging_creates_run_file(tmp_path, monkeypatch):
    monkeypatch.setattr("app.scripts.runtime.logs_dir", lambda: tmp_path)
    (tmp_path / "runs").mkdir(parents=True)
    run_log = setup_script_logging("test_script")
    assert run_log.exists()
    logging.getLogger("test").info("hello")
    assert "hello" in run_log.read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_dry_run_never_calls_send_email():
    from types import SimpleNamespace
    from uuid import uuid4
    from unittest.mock import AsyncMock, patch

    user = SimpleNamespace(email_digest_enabled=True, email="dev@roleradar.local", id=uuid4())
    job = SimpleNamespace(
        id=uuid4(),
        title="Intern",
        location="India",
        apply_url="https://example.com",
        deadline_at=None,
        company_id=uuid4(),
    )

    class FakeSession:
        async def get(self, model, pk):
            return SimpleNamespace(name="Co")

        async def scalars(self, stmt):
            class R:
                def all(self):
                    return [job]

            return R()

        def add(self, _):
            pass

        async def commit(self):
            pass

    with patch("app.services.job_alerts.send_email") as send:
        from app.services.job_alerts import send_job_alerts

        await send_job_alerts(FakeSession(), user, dry_run=True)
        send.assert_not_called()


def test_exit_config_constant():
    assert EXIT_CONFIG == 4
