from dataclasses import dataclass


@dataclass
class DigestSendResult:
    sent: bool
    status: str
    detail: str | None = None
    smtp_error: str | None = None
