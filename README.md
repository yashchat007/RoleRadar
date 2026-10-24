# RoleRadar

Personal job intelligence platform — official career pages only, explainable match scores, Research Desk UI.

## Stack

- Frontend: React, TypeScript, Tailwind CSS (`frontend/`)
- Backend: FastAPI, SQLAlchemy, PostgreSQL (`backend/`)
- Discovery worker: `backend/app/workers/main.py`

## Security (public repo)

- **Never commit** `backend/.env` or real API keys — use `backend/.env.example` as a template only.
- **Uploaded resumes** are stored under `backend/data/resumes/` at runtime; that directory is gitignored.
- Default `DATABASE_URL` / Docker Postgres password (`roleradar`) is for **local dev only**, not production.

## Prerequisites

- Node.js 20+
- Python 3.11+
- Docker (for PostgreSQL and Mailpit)
- Playwright Chromium (for official-site discovery adapters)

## Development

```bash
docker compose up -d
cd backend
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\playwright install chromium
set PYTHONPATH=.
.venv\Scripts\python scripts\validate_pilots.py
.venv\Scripts\uvicorn app.main:app --reload --app-dir .
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
set PYTHONPATH=.
.venv\Scripts\pytest
```

Live adapter checks (network + Playwright):

```bash
.venv\Scripts\pytest -m live
```

## Phase 2 — discovery

Official career pages only. HTTP client blocks ATS/aggregator hosts (see `app/config.py`).

Pilot adapters:

| Company | Adapter | Status |
|---------|---------|--------|
| Stripe | `stripe_official` | Playwright on `stripe.com/jobs/search` |
| Atlassian | `atlassian_official` | Playwright on `atlassian.com/company/careers/details/*` |
| Cloudflare | `cloudflare_official` | Fails validation — listings link only to `boards.greenhouse.io` |

After Postgres is up:

```bash
docker compose up -d
cd backend
set PYTHONPATH=.
.venv\Scripts\python scripts\validate_pilots.py
```

API:

- `POST /api/v1/discovery/companies/{id}/validate` — inspect, sample extract, enable on success, run initial scan
- `POST /api/v1/discovery/scan` — scan all `is_enabled` companies
- `GET /api/v1/jobs` — ingested listings
- `GET /api/v1/jobs/meta` — totals + degraded sources

Worker: `PYTHONPATH=. .venv\Scripts\python -m app.workers.main`

## Phase 3 — resume and matching

Single dev user (`dev@roleradar.local`) is created on API startup.

- `GET/PATCH /api/v1/profile` — structured profile (skills, education, experience, projects, preferences)
- `POST /api/v1/resume` — upload PDF/DOCX/TXT (multipart), rule-based parse with source spans
- `GET /api/v1/resume/source?field_path=skills.0` — quote from resume for a field
- `GET /api/v1/jobs` — includes `score`, `eligible`, `top_reason`; `hide_ineligible=true` (default) with `meta.hidden_ineligible_count`
- `GET /api/v1/jobs/{id}/match` — full breakdown (factors, requirements, gaps)

Matches recompute after resume upload, profile patch, and successful discovery scans.

## Phase 4 — product UI

With API + frontend dev servers running (`npm run dev` proxies `/api` to port 8000):

| Route | Screen |
|-------|--------|
| `/` | Today briefing, attention list, tracker counts, changelog |
| `/discover` | Job table + detail pane, search `/`, arrows, bookmark `S` |
| `/tracker` | Stage board (rejected collapsible) + list view |
| `/saved` | Bookmarked jobs |
| `/profile` | Resume upload + parsed sections |
| `/design-system` | Research Desk reference |

Backend also exposes `GET /api/v1/today`, `/tracker`, `/saved`, bookmark POST/DELETE.

## Phase 5 — alerts, theme, a11y, E2E

- **Mailpit**: `docker compose up -d` → SMTP `1025`, UI http://127.0.0.1:8025
- **Digest**: `POST /api/v1/digest/send` or `python -m app.workers.digest`
- **Watches**: `GET/POST/DELETE /api/v1/watches` (+ Save watch on Discover)
- **Settings**: theme (light/dark/system) + digest toggle → `PATCH /api/v1/settings`
- **UI**: `Ctrl+K` command palette, `?` shortcuts overlay, skip link
- **E2E**: `cd frontend && npm install && npx playwright install chromium && npm run test:e2e`

If you added Phase 5 DB columns on an existing Postgres volume, recreate the DB or run:
`ALTER TABLE users ADD COLUMN IF NOT EXISTS email_digest_enabled BOOLEAN DEFAULT true;`
