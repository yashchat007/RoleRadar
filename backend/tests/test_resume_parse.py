from app.resume.parse import parse_resume_text

SAMPLE = """
Jane Doe
jane@example.com

Skills
Python, React, PostgreSQL, FastAPI, AWS

Education
State University — B.S. Computer Science, 2024

Experience
Software Engineer Intern at Acme Corp
2023 — 2024
- Built an Inventory API in Python serving 10k requests/day

Projects
Inventory API — Python, FastAPI, PostgreSQL
"""


def test_parse_resume_extracts_skills_and_experience():
    parsed = parse_resume_text(SAMPLE)
    skill_names = {s.name.lower() for s in parsed.skills}
    assert "python" in skill_names
    assert "fastapi" in skill_names
    assert len(parsed.experience) >= 1
    assert parsed.experience[0].title
    assert any(s.source for s in parsed.skills if s.name.lower() == "python")
