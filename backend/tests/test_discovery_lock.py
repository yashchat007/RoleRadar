import json
import os
from unittest.mock import patch

from app.scripts.discovery_lock import acquire_discovery_lock, lock_path, release_discovery_lock


def test_second_acquire_fails_while_lock_held(tmp_path, monkeypatch):
    monkeypatch.setattr("app.scripts.discovery_lock.logs_dir", lambda: tmp_path)
    assert acquire_discovery_lock() is True
    assert acquire_discovery_lock() is False
    release_discovery_lock()
    assert not lock_path().exists()


def test_competing_live_process_blocks_acquire(tmp_path, monkeypatch):
    monkeypatch.setattr("app.scripts.discovery_lock.logs_dir", lambda: tmp_path)
    path = lock_path()
    path.write_text(
        json.dumps({"pid": 4242, "started_at": "2099-01-01T00:00:00+00:00"}),
        encoding="utf-8",
    )
    with patch("app.scripts.discovery_lock._pid_alive", return_value=True):
        assert acquire_discovery_lock() is False
    assert path.exists()


def test_stale_lock_removed_when_pid_dead(tmp_path, monkeypatch):
    monkeypatch.setattr("app.scripts.discovery_lock.logs_dir", lambda: tmp_path)
    path = lock_path()
    path.write_text(
        json.dumps({"pid": 999999, "started_at": "2020-01-01T00:00:00+00:00"}),
        encoding="utf-8",
    )
    with patch("app.scripts.discovery_lock._pid_alive", return_value=False):
        assert acquire_discovery_lock() is True
    release_discovery_lock()
