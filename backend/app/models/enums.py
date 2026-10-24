import enum


class ParserStatus(str, enum.Enum):
    pending_validation = "pending_validation"
    validating = "validating"
    enabled = "enabled"
    failed = "failed"
    disabled = "disabled"


class ExtractionMode(str, enum.Enum):
    static_html = "static_html"
    browser_render = "browser_render"


class LastScanStatus(str, enum.Enum):
    success = "success"
    partial = "partial"
    error = "error"
    skipped = "skipped"


class ListingStatus(str, enum.Enum):
    active = "active"
    closed_confirmed = "closed_confirmed"
    temporarily_unavailable = "temporarily_unavailable"


class TrackerStage(str, enum.Enum):
    new = "new"
    shortlisted = "shortlisted"
    applied = "applied"
    oa = "oa"
    interview = "interview"
    offer = "offer"
    rejected = "rejected"


TRACKER_STAGE_ORDER = [
    TrackerStage.new,
    TrackerStage.shortlisted,
    TrackerStage.applied,
    TrackerStage.oa,
    TrackerStage.interview,
    TrackerStage.offer,
    TrackerStage.rejected,
]
