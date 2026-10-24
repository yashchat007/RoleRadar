from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://roleradar:roleradar@127.0.0.1:5432/roleradar"
    cors_origins: list[str] = ["http://127.0.0.1:5173", "http://localhost:5173"]
    discovery_user_agent: str = "RoleRadarDiscovery/0.1 (+official-careers-only)"
    discovery_max_jobs_per_scan: int = 80
    discovery_safety_max_jobs_per_scan: int = 300
    discovery_jpm_safety_max_jobs_per_scan: int = 500
    discovery_detail_enrich_max_jobs: int = 120
    discovery_meta_detail_verify_max_jobs: int = 64
    discovery_bofa_detail_verify_max_jobs: int = 24
    discovery_playwright_goto_max_attempts: int = 3
    discovery_validation_max_jobs: int = 12
    discovery_blocklist_hosts: list[str] = [
        "boards-api.greenhouse.io",
        "boards.greenhouse.io",
        "api.lever.co",
        "jobs.lever.co",
        "jobs.ashbyhq.com",
        "api.ashbyhq.com",
    ]
    smtp_host: str = "127.0.0.1"
    smtp_port: int = 1025
    smtp_from: str = "briefing@roleradar.local"
    smtp_use_tls: bool = False
    alert_recipient_email: str | None = None
    discovery_company_timeout_sec: int = 600
    discovery_lock_stale_seconds: int = 7200
    # Documented default for external schedulers (Task Scheduler/cron); not started automatically.
    discovery_refresh_interval_hours: int = 24


settings = Settings()
