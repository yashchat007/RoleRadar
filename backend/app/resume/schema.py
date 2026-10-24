from typing import Literal

from pydantic import BaseModel, Field


class SourceSpan(BaseModel):
    start: int
    end: int
    quote: str


class SkillEntry(BaseModel):
    name: str
    level: Literal["beginner", "intermediate", "advanced"] | None = None
    confidence: float = Field(ge=0, le=1)
    source: SourceSpan | None = None
    needs_confirm: bool = False


class EducationEntry(BaseModel):
    institution: str
    degree: str | None = None
    field: str | None = None
    end_year: int | None = None
    confidence: float = 1.0
    source: SourceSpan | None = None
    needs_confirm: bool = False


class ExperienceEntry(BaseModel):
    title: str
    company: str | None = None
    start_year: int | None = None
    end_year: int | None = None
    highlights: list[str] = Field(default_factory=list)
    confidence: float = 1.0
    source: SourceSpan | None = None
    needs_confirm: bool = False


class ProjectEntry(BaseModel):
    name: str
    description: str | None = None
    skills: list[str] = Field(default_factory=list)
    confidence: float = 1.0
    source: SourceSpan | None = None
    needs_confirm: bool = False


class Preferences(BaseModel):
    graduation_year: int | None = None
    requires_visa_sponsorship: bool = False
    preferred_locations: list[str] = Field(default_factory=list)
    open_to_remote: bool = True
    min_match_score: int = 0


class ParsedProfile(BaseModel):
    skills: list[SkillEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    projects: list[ProjectEntry] = Field(default_factory=list)
    preferences: Preferences = Field(default_factory=Preferences)
