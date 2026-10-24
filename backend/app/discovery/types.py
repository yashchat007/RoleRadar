from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class NormalizedJob:
    source_job_key: str
    title: str
    location: str | None
    remote_flag: bool | None
    description_sections: dict
    posted_at: datetime | None
    deadline_at: datetime | None
    apply_url: str
    listing_url: str
    content_hash: str
    location_meta: dict | None = None


@dataclass
class AdapterResult:
    jobs: list[NormalizedJob] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    fatal_error: str | None = None


@dataclass
class InspectionReport:
    extraction_mode: str
    allowed_hosts: list[str]
    notes: str = ""
    inventory_complete: bool = False
