from pydantic import BaseModel


class DigestSendOut(BaseModel):
    digest_sent: bool
    digest_status: str
    digest_detail: str | None = None
    watch_emails: int = 0
    smtp_error: str | None = None
