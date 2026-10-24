from unittest.mock import patch

import pytest

from app.services.job_alerts import send_job_alerts


@pytest.mark.asyncio
async def test_alerts_disabled_without_dry_run():
    from types import SimpleNamespace

    user = SimpleNamespace(email_digest_enabled=False, email="dev@roleradar.local", id="00000000-0000-0000-0000-000000000001")
    session = SimpleNamespace()
    sent, failed, errors = await send_job_alerts(session, user, dry_run=False)
    assert sent == 0
    assert "disabled" in errors[0].lower()


@pytest.mark.asyncio
async def test_smtp_failure_not_recorded_as_sent():
    from types import SimpleNamespace
    from uuid import uuid4

    user = SimpleNamespace(email_digest_enabled=True, email="dev@roleradar.local", id=uuid4())
    job = SimpleNamespace(
        id=uuid4(),
        title="SWE Intern",
        location="Bengaluru",
        apply_url="https://example.com",
        deadline_at=None,
        company_id=uuid4(),
    )

    class FakeSession:
        async def get(self, model, pk):
            return SimpleNamespace(name="TestCo")

        async def scalars(self, stmt):
            class R:
                def all(self):
                    return [job]

            return R()

        def add(self, _):
            pass

        async def commit(self):
            pass

    with patch("app.services.job_alerts.select_jobs_pending_notification", return_value=[job]):
        with patch("app.services.job_alerts.send_email", side_effect=OSError("refused")):
            sent, failed, errors = await send_job_alerts(FakeSession(), user, dry_run=False, max_retries=0)
    assert sent == 0
    assert failed == 1
    assert "refused" in errors[0]
