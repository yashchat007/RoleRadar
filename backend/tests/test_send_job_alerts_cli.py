"""CLI wiring for send_job_alerts (no SMTP, no DB)."""

from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_cli_dry_run_returns_zero_without_smtp_check_failure():
    with patch("app.scripts.send_job_alerts.check_database_connection", AsyncMock(return_value=None)):
        with patch("app.scripts.send_job_alerts.validate_smtp_for_alerts", return_value=None):
            with patch("app.scripts.send_job_alerts.ensure_dev_user", AsyncMock()):
                with patch(
                    "app.scripts.send_job_alerts.send_job_alerts",
                    AsyncMock(return_value=(0, 0, ["Dry run: 0 job(s) would be emailed"])),
                ):
                    from app.scripts.send_job_alerts import run

                    code = await run(dry_run=True)
                    assert code == 0


@pytest.mark.asyncio
async def test_cli_config_error_exit_code():
    with patch("app.scripts.send_job_alerts.check_database_connection", AsyncMock(return_value="bad db")):
        from app.scripts.send_job_alerts import run
        from app.scripts.runtime import EXIT_CONFIG

        code = await run(dry_run=False)
        assert code == EXIT_CONFIG
