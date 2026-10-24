import re

from app.resume.schema import (
    EducationEntry,
    ExperienceEntry,
    ParsedProfile,
    Preferences,
    ProjectEntry,
    SkillEntry,
    SourceSpan,
)

SKILL_KEYWORDS = [
    "python",
    "java",
    "javascript",
    "typescript",
    "react",
    "node",
    "sql",
    "postgresql",
    "aws",
    "docker",
    "kubernetes",
    "go",
    "golang",
    "rust",
    "c++",
    "c#",
    "machine learning",
    "tensorflow",
    "pytorch",
    "fastapi",
    "django",
    "flask",
    "git",
    "linux",
    "azure",
    "gcp",
    "html",
    "css",
    "tailwind",
    "graphql",
    "redis",
    "kafka",
    "spark",
    "pandas",
    "numpy",
    "scikit-learn",
    "ci/cd",
    "terraform",
]

SECTION_HEADERS = {
    "skills": re.compile(r"^(skills|technical skills|technologies)\s*$", re.I),
    "education": re.compile(r"^education\s*$", re.I),
    "experience": re.compile(r"^(experience|work experience|employment)\s*$", re.I),
    "projects": re.compile(r"^(projects|personal projects)\s*$", re.I),
}


def find_span(text: str, needle: str, confidence: float) -> tuple[SourceSpan | None, float]:
    if not needle:
        return None, confidence
    idx = text.lower().find(needle.lower())
    if idx < 0:
        return None, max(0.3, confidence - 0.2)
    end = idx + len(needle)
    quote = text[idx:end]
    return SourceSpan(start=idx, end=end, quote=quote), confidence


def split_sections(text: str) -> dict[str, list[str]]:
    lines = [ln.strip() for ln in text.splitlines()]
    sections: dict[str, list[str]] = {"body": []}
    current = "body"
    for line in lines:
        if not line:
            continue
        matched = False
        for name, pattern in SECTION_HEADERS.items():
            if pattern.match(line):
                current = name
                sections.setdefault(current, [])
                matched = True
                break
        if not matched:
            sections.setdefault(current, []).append(line)
    return sections


def parse_resume_text(text: str) -> ParsedProfile:
    normalized = re.sub(r"\r\n", "\n", text).strip()
    sections = split_sections(normalized)

    skills = _parse_skills(normalized, sections.get("skills", []))
    education = _parse_education(normalized, sections.get("education", []))
    experience = _parse_experience(normalized, sections.get("experience", []))
    projects = _parse_projects(normalized, sections.get("projects", []))
    preferences = _parse_preferences(normalized)

    return ParsedProfile(
        skills=skills,
        education=education,
        experience=experience,
        projects=projects,
        preferences=preferences,
    )


_LOCATION_LIKE = frozenset(
    {
        "india",
        "bangalore",
        "bengaluru",
        "mumbai",
        "hyderabad",
        "pune",
        "chennai",
        "delhi",
        "remote",
        "usa",
        "united",
        "states",
    }
)


def _parse_skills(full_text: str, lines: list[str]) -> list[SkillEntry]:
    found: dict[str, SkillEntry] = {}
    haystack = " ".join(lines) if lines else ""
    if not haystack.strip():
        return []
    for kw in SKILL_KEYWORDS:
        if kw.lower() in _LOCATION_LIKE:
            continue
        if re.search(rf"\b{re.escape(kw)}\b", haystack, re.I):
            span, conf = find_span(full_text, kw, 0.85)
            found[kw.lower()] = SkillEntry(
                name=kw.title() if kw != "ci/cd" else "CI/CD",
                level=None,
                confidence=conf,
                source=span,
                needs_confirm=conf < 0.7,
            )
    for line in lines:
        for part in re.split(r"[,|•·]", line):
            token = part.strip()
            key = token.lower()
            if key in _LOCATION_LIKE or len(token) < 2 or len(token) > 40:
                continue
            if not token.lower().startswith("skills"):
                if key not in found:
                    span, conf = find_span(full_text, token, 0.75)
                    found[key] = SkillEntry(
                        name=token,
                        confidence=conf,
                        source=span,
                        needs_confirm=conf < 0.7,
                    )
    return list(found.values())


def _parse_education(full_text: str, lines: list[str]) -> list[EducationEntry]:
    entries: list[EducationEntry] = []
    for line in lines:
        year_match = re.search(r"(20\d{2}|19\d{2})", line)
        span, conf = find_span(full_text, line[: min(40, len(line))], 0.8)
        entries.append(
            EducationEntry(
                institution=line,
                end_year=int(year_match.group(1)) if year_match else None,
                confidence=conf,
                source=span,
                needs_confirm=conf < 0.7,
            )
        )
    return entries[:5]


def _parse_experience(full_text: str, lines: list[str]) -> list[ExperienceEntry]:
    entries: list[ExperienceEntry] = []
    buffer: list[str] = []
    for line in lines:
        if re.match(r"^(20\d{2}|19\d{2})", line) or " at " in line.lower():
            if buffer:
                entries.append(_experience_from_lines(full_text, buffer))
                buffer = []
            buffer.append(line)
        elif buffer:
            buffer.append(line)
    if buffer:
        entries.append(_experience_from_lines(full_text, buffer))
    return entries[:8]


def _experience_from_lines(full_text: str, lines: list[str]) -> ExperienceEntry:
    head = lines[0]
    span, conf = find_span(full_text, head[: min(50, len(head))], 0.78)
    title = head
    company = None
    if " at " in head.lower():
        parts = re.split(r"\s+at\s+", head, maxsplit=1, flags=re.I)
        title = parts[0]
        company = parts[1] if len(parts) > 1 else None
    years = [int(m.group(1)) for ln in lines for m in [re.search(r"(20\d{2}|19\d{2})", ln)] if m]
    return ExperienceEntry(
        title=title.strip(),
        company=company,
        start_year=years[0] if years else None,
        end_year=years[-1] if years else None,
        highlights=[ln for ln in lines[1:] if ln.startswith(("-", "•", "*")) or len(ln) > 20][:5],
        confidence=conf,
        source=span,
        needs_confirm=conf < 0.7,
    )


def _parse_projects(full_text: str, lines: list[str]) -> list[ProjectEntry]:
    entries: list[ProjectEntry] = []
    for line in lines:
        span, conf = find_span(full_text, line[: min(40, len(line))], 0.72)
        entries.append(
            ProjectEntry(
                name=line.split("—")[0].split("-")[0].strip(),
                description=line,
                confidence=conf,
                source=span,
                needs_confirm=conf < 0.7,
            )
        )
    return entries[:6]


def _parse_preferences(full_text: str) -> Preferences:
    grad = None
    m = re.search(r"(graduat(?:e|ion)|class of)\s*(20\d{2})", full_text, re.I)
    if m:
        grad = int(m.group(2))
    visa = bool(re.search(r"visa|sponsorship", full_text, re.I))
    return Preferences(graduation_year=grad, requires_visa_sponsorship=visa)
