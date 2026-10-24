"""Shared CLI runtime: logging, config checks, exit codes for scheduled scripts."""

from __future__ import annotations

import logging
import re
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from sqlalchemy import text

from app.config import BACKEND_DIR, settings

EXIT_CONFIG = 4
EXIT_BUSY = 5
RUN_LOG_RETENTION = 40
AGG_LOG_MAX_BYTES = 2_000_000
AGG_LOG_BACKUP_COUNT = 5


def logs_dir() -> Path:
    path = BACKEND_DIR / "logs"
    path.mkdir(parents=True, exist_ok=True)
    (path / "runs").mkdir(parents=True, exist_ok=True)
    return path


def setup_script_logging(script_name: str) -> Path:
    """stderr + per-run timestamped file + rotating aggregate log under backend/logs/."""
    log_dir = logs_dir()
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_log = log_dir / "runs" / f"{script_name}-{ts}.log"

    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    for handler in list(root.handlers):
        root.removeHandler(handler)

    stream = logging.StreamHandler(sys.stderr)
    stream.setFormatter(fmt)
    root.addHandler(stream)

    run_handler = logging.FileHandler(run_log, encoding="utf-8")
    run_handler.setFormatter(fmt)
    root.addHandler(run_handler)

    aggregate = RotatingFileHandler(
        log_dir / f"{script_name}.log",
        maxBytes=AGG_LOG_MAX_BYTES,
        backupCount=AGG_LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    aggregate.setFormatter(fmt)
    root.addHandler(aggregate)

    _prune_old_run_logs(log_dir / "runs", script_name)
    return run_log


def _prune_old_run_logs(runs_dir: Path, script_name: str) -> None:
    pattern = f"{script_name}-*.log"
    files = sorted(runs_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in files[RUN_LOG_RETENTION:]:
        try:
            path.unlink()
        except OSError:
            pass


def log_configuration_status(logger: logging.Logger) -> None:
    env_file = BACKEND_DIR / ".env"
    if env_file.is_file():
        logger.info("Configuration: backend/.env present; settings loaded from %s", env_file)
    else:
        logger.warning(
            "Configuration: no backend/.env at %s - using defaults and process environment",
            env_file,
        )
    logger.info(
        "Database target: %s",
        _safe_database_label(settings.database_url),
    )
    if settings.alert_recipient_email:
        logger.info("Alert recipient: configured via ALERT_RECIPIENT_EMAIL")
    else:
        logger.info("Alert recipient: dev user email (ALERT_RECIPIENT_EMAIL not set)")


def _safe_database_label(database_url: str) -> str:
    """Host/db hint only — never log credentials."""
    url = (database_url or "").strip()
    if not url:
        return "(empty)"
    # postgresql+asyncpg://user:pass@host:port/dbname
    m = re.match(r"^[a-z+]+://([^@]+@)?([^/?:]+)", url, re.I)
    if m:
        return m.group(2) or "(invalid)"
    return "(unrecognized URL scheme)"


def validate_database_url() -> str | None:
    url = (settings.database_url or "").strip()
    if not url:
        return "DATABASE_URL is empty. Create backend/.env with DATABASE_URL=postgresql+asyncpg://..."
    if "postgresql" not in url:
        return "DATABASE_URL must use PostgreSQL (postgresql+asyncpg://user:pass@host:port/dbname)"
    return None


async def check_database_connection() -> str | None:
    static = validate_database_url()
    if static:
        return static
    from app.database import SessionLocal

    try:
        async with SessionLocal() as session:
            await session.execute(text("select 1"))
    except Exception as e:
        return (
            f"Database connection failed ({type(e).__name__}). "
            "Check DATABASE_URL in backend/.env and that PostgreSQL is running."
        )
    return None


def validate_smtp_for_alerts(dry_run: bool) -> str | None:
    if dry_run:
        return None
    if not (settings.smtp_host or "").strip():
        return "SMTP_HOST is empty. Set SMTP_HOST in backend/.env (e.g. 127.0.0.1 for Mailpit)."
    if settings.smtp_port < 1 or settings.smtp_port > 65535:
        return f"SMTP_PORT is invalid ({settings.smtp_port}). Use 1–65535."
    if not (settings.smtp_from or "").strip():
        return "SMTP_FROM is empty. Set SMTP_FROM in backend/.env."
    return None


def finish_script(logger: logging.Logger, exit_code: int) -> None:
    level = logging.ERROR if exit_code else logging.INFO
    logger.log(level, "Finished with exit code %s", exit_code)
    sys.exit(exit_code)
