import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def w(rel, content):
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

w("backend/tests/test_compliance.py", """from app.discovery.compliance import assert_official_url, is_host_blocklisted


def test_blocklist_greenhouse_api():
    assert is_host_blocklisted("https://boards-api.greenhouse.io/v1/boards/acme/jobs")


def test_allow_official_stripe():
    assert not is_host_blocklisted("https://stripe.com/jobs/search")
    assert_official_url("https://stripe.com/jobs/123", frozenset({"stripe.com"}))
""")

w("README.md", """# RoleRadar

Personal job intelligence platform — official career pages only, explainable match scores, Research Desk UI.

## Stack

- Frontend: React, TypeScript, Tailwind CSS (`frontend/`)
- Backend: FastAPI, SQLAlchemy, PostgreSQL (`backend/`)
- Discovery worker: `backend/app/workers/main.py`

## Prerequisites

- Node.js 20+
- Python 3.11+
- Docker (for PostgreSQL)

## Development

```bash
docker compose up -d
cd backend
python -m venv .venv
.venv\\Scripts\\pip install -r requirements.txt
.venv\\Scripts\\uvicorn app.main:app --reload --app-dir .
```

```bash
cd frontend
npm install
npm run dev
```

- App: http://127.0.0.1:5173
- Design system: http://127.0.0.1:5173/design-system
- API docs: http://127.0.0.1:8000/docs

## Job sources

All listings must be extracted from each company's **official** career website. Third-party job APIs and ATS discovery APIs are blocked in `app/discovery/compliance.py`.

## Tests

```bash
cd backend
.venv\\Scripts\\pip install pytest
.venv\\Scripts\\pytest
```
""")

w(".gitignore", """node_modules/
frontend/dist/
backend/.venv/
__pycache__/
*.pyc
.env
.pytest_cache/
""")

print("readme ok")
