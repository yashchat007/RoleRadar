from pydantic import BaseModel, Field


class SettingsOut(BaseModel):
    email: str
    theme: str
    email_digest_enabled: bool


class SettingsPatch(BaseModel):
    theme: str | None = None
    email_digest_enabled: bool | None = None
