"""Process-level lock for discover_jobs (manual + scheduled). Stale locks are recovered."""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path

from app.config import settings
from app.scripts.runtime import logs_dir

LOCK_FILE = "discover_jobs.lock"


def lock_path() -> Path:
    return logs_dir() / LOCK_FILE


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _stale_seconds() -> int:
    return max(
        settings.discovery_lock_stale_seconds,
        settings.discovery_company_timeout_sec * 8 + 300,
    )


def acquire_discovery_lock(logger: logging.Logger | None = None) -> bool:
    """
    Return True if this process holds the lock.
    Removes stale locks when the owning PID is gone or the lock exceeded stale age.
    """
    log = logger or logging.getLogger(__name__)
    path = lock_path()
    stale_sec = _stale_seconds()

    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            pid = int(data.get("pid") or 0)
            started_raw = data.get("started_at") or ""
            started = datetime.fromisoformat(started_raw.replace("Z", "+00:00"))
            if started.tzinfo is None:
                started = started.replace(tzinfo=UTC)
            age = (datetime.now(UTC) - started).total_seconds()
        except (json.JSONDecodeError, TypeError, ValueError):
            log.warning("Removing unreadable discover_jobs lock at %s", path)
            path.unlink(missing_ok=True)
        else:
            alive = _pid_alive(pid)
            if alive and age < stale_sec:
                log.error(
                    "Another discover_jobs run is active (pid=%s, started=%s). Exiting without scanning.",
                    pid,
                    started_raw,
                )
                return False
            log.warning(
                "Removing stale discover_jobs lock (pid=%s, process_alive=%s, age_sec=%.0f, stale_limit=%s)",
                pid,
                alive,
                age,
                stale_sec,
            )
            path.unlink(missing_ok=True)

    payload = {"pid": os.getpid(), "started_at": datetime.now(UTC).isoformat()}
    path.write_text(json.dumps(payload), encoding="utf-8")
    return True


def release_discovery_lock() -> None:
    path = lock_path()
    if not path.is_file():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if int(data.get("pid") or 0) == os.getpid():
            path.unlink()
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        pass
