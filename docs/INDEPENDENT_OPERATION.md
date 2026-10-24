# RoleRadar — Independent discovery and email (Windows)

RoleRadar runs scheduled discovery and internship alerts **without Cursor or the IDE**.

## Prerequisites

1. **PostgreSQL** — `docker compose up -d` from the repo root (or your own Postgres matching `DATABASE_URL`).
2. **Python venv** — `backend\.venv` with dependencies installed (`pip install -r requirements.txt`).
3. **Playwright Chromium** (for browser adapters): `playwright install chromium` from `backend/`.
4. **Mailpit** (local SMTP): listen on `127.0.0.1:1025` (default in `app/config.py`).

## Environment

Create **`backend/.env`** from **`backend/.env.example`** (never commit secrets). Settings load via **absolute path** in `app/config.py` (`BACKEND_DIR / ".env"`), so manual runs and Task Scheduler both pick up the same file when `Run-RoleRadarTask.ps1` sets `cwd` to `backend/`. Logs show only the database **host** (`Database target: …`), never credentials.

```env
DATABASE_URL=postgresql+asyncpg://roleradar:roleradar@127.0.0.1:5432/roleradar
ALERT_RECIPIENT_EMAIL=you@example.com
SMTP_HOST=127.0.0.1
SMTP_PORT=1025
SMTP_FROM=briefing@roleradar.local
```

- **Recipient:** set `ALERT_RECIPIENT_EMAIL` or alerts go to the dev user (`dev@roleradar.local`).
- **Digest toggle:** Settings → “Daily briefing email” maps to `users.email_digest_enabled`. Scheduled alerts respect this flag (exit **0** without sending when disabled).

Do **not** rely on machine-wide environment variables for secrets; use `backend/.env`.

## Commands

From `backend/` with `PYTHONPATH=.`:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.discover_jobs
.\.venv\Scripts\python.exe -m app.scripts.discover_jobs --company "Google"
.\.venv\Scripts\python.exe -m app.scripts.send_job_alerts
.\.venv\Scripts\python.exe -m app.scripts.send_job_alerts --dry-run
.\.venv\Scripts\python.exe -m app.scripts.data_repair_dry_run
```

**Refresh cadence:** recurring discovery is **not** started by the FastAPI app. Use Task Scheduler/cron to run `discover_jobs` on a schedule. Default documented interval: `DISCOVERY_REFRESH_INTERVAL_HOURS=24` in settings (conservative for official sources). One company failing does not block others — `discover_jobs` continues the loop and exits non-zero if any scan errors.

**Data repair:** `data_repair_dry_run` previews polluted titles and stale match scores; pass `--apply` for idempotent title/requisition fixes and clearing scores when `resume_match_available` is false.

Each invocation writes:

| Log | Purpose |
|-----|---------|
| `backend/logs/runs/<script>-YYYYMMDD-HHMMSS.log` | One file per run (timestamped); oldest runs pruned (40 per script) |
| `backend/logs/<script>.log` | Rotating aggregate (5 × ~2 MB) |
| stderr | Same lines as the run log (for interactive use) |

Every run ends with `Finished with exit code N` in the logs.

Exit codes:

| Code | Meaning |
|------|---------|
| 0 | Success (or alerts skipped because digest disabled) |
| 1 | One or more company scans failed / fatal script error |
| 2 | No enabled companies in the active registry |
| 3 | SMTP delivery failed after retries |
| 4 | Configuration or database connection invalid |
| 5 | Another `discover_jobs` run is already active (`backend/logs/discover_jobs.lock`) |
| 130 | Interrupted (Ctrl+C) |

**Overlap:** Task Scheduler uses `IgnoreNew` for scheduled instances only. Manual runs and overlapping shells are also guarded by `discover_jobs.lock` (PID + timestamp). Stale locks are removed when the owning process is gone or the lock is older than `discovery_lock_stale_seconds` (default 2h).

**Discovery runtime:** Each company line in the run log includes `duration_ms=…`. Per-company wall time is dominated by (1) Playwright facet harvest and scroll/load-more, and (2) optional per-listing detail-page location enrichment (`discovery_detail_enrich_max_jobs`, default 120). Large inventories (Amazon, JPMorgan Oracle CX) spend most of their time in enrichment, not HTTP API work. Tune caps in `backend/.env` only after reading a full run log — do not raise caps to mask pagination gaps.

Logs never include database passwords or SMTP credentials.

## Windows Task Scheduler

After editing paths in `scripts\windows\Register-RoleRadarTasks.ps1`, register **as yourself**:

```powershell
cd <repo-root>\scripts\windows
.\Register-RoleRadarTasks.ps1
```

Tasks call `Run-RoleRadarTask.ps1`, which sets `backend/` as the working directory, sets `PYTHONPATH=.`, and runs the venv Python module. **Environment variables for DB/SMTP come from `backend/.env`**, not from the task definition.

**Inspect:** Task Scheduler → Task Scheduler Library → `RoleRadar-Discover`, `RoleRadar-JobAlerts`.

**Remove:**

```powershell
.\Unregister-RoleRadarTasks.ps1
```

**Overlap behavior:** `-MultipleInstances IgnoreNew` means if a scheduled run is **still executing** when the next daily trigger fires, Windows **skips** the new instance. It is **not** a mutex across manual runs, other machines, or overlapping `discover_jobs` started outside the scheduler.

## Active companies (registry)

Google, Microsoft, Amazon, Bank of America, JPMorgan Chase, Morgan Stanley, Goldman Sachs, Meta.

All other companies remain in the database but are **disabled** for scheduled discovery and hidden from the Discover company strip.

## Logs and recovery

- Per-run: `backend/logs/runs/discover_jobs-*.log`, `backend/logs/runs/send_job_alerts-*.log`
- Aggregate: `backend/logs/discover_jobs.log`, `backend/logs/send_job_alerts.log`

If a run fails, fix the reported company, `.env`, or SMTP issue and re-run the command. Failed scans do **not** mass-close jobs for other companies.
