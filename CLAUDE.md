# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**DORA Reporting Platform** — a portfolio/demo project with two sections:
1. **Simulation Engine** (`simulation/`) — Python scripts that populate GitHub and Jira Cloud with 6 months of realistic DevOps activity
2. **Dashboard** (`dashboard/`) — Vanilla HTML/CSS/JS single-page app that reads from GitHub + Jira REST APIs and renders DORA metric trend charts

## Planned Repository Layout

```
dora-platform/          ← this repo
├── simulation/         ← Python scripts (Phases 2–3)
├── dashboard/          ← HTML/CSS/JS frontend (Phases 4–5)
├── proxy/              ← Local Python proxy for Jira CORS (Phase 4)
└── docs/               ← Architecture PDFs + project_plan.md
```

Target repo populated by the simulator: **dora-demo-app** (separate GitHub repo).

## Tech Stack

- **Simulation**: Python 3, PyGithub, requests, python-dateutil
- **Dashboard**: Vanilla HTML/CSS/JS, Chart.js (CDN), no build tools
- **PDF docs**: ReportLab (`docs/generate_docs.py`)
- **APIs**: GitHub REST API, Jira Cloud REST API (direct calls)
- **Jira CORS workaround**: local `proxy/server.py` — dashboard calls `localhost:8080/jira/*`

## Regenerating Architecture Docs

```bash
cd /path/to/dora-platform
python3 docs/generate_docs.py
```

Outputs four PDFs to `docs/`: `0.1_project_architecture.pdf` through `0.4_build_plan.pdf`.

## Key Design Decisions

- **No framework, no build step** on the dashboard — plain `fetch()`, Chart.js via CDN, open `index.html` directly in a browser (or serve with `python3 -m http.server`)
- **Backdated GitHub data**: simulation uses `GIT_AUTHOR_DATE` / `GIT_COMMITTER_DATE` env vars to create commits in the past; Jira timestamps are set via the REST API `created` field workaround
- **Failure release convention**: releases named `vX.Y.Z-hotfix` are treated as failed deployments; corresponding Jira Incident tickets reference them via the `Linked Release` custom field
- **DORA metric sources**:
  - Deployment Frequency → GitHub release tags count
  - Lead Time → Jira `First Commit Date` custom field → story `Done` transition timestamp
  - Change Failure Rate → Incident count / Release count per period
  - MTTR → Jira Incident `Open` → `Resolved` transition delta

## Build Plan Status

Tracked in [`docs/project_plan.md`](docs/project_plan.md). Phase 0 (architecture) is complete; Phases 1–5 are pending. Update statuses there as work progresses.

## Jira Project

- Project key: `DORA`
- Custom fields required: `Deployment Version`, `First Commit Date`, `Incident Severity`, `Linked Release`
- Incident workflow: Open → Investigating → Resolved
- Story/Bug workflow: To Do → In Progress → In Review → Done

## DORA Performance Band Thresholds

Used for chart overlay lines and scorecard classification in Phase 5:

| Metric | Elite | High | Medium | Low |
|---|---|---|---|---|
| Deployment Frequency | Multiple/day | Weekly | Monthly | < Monthly |
| Lead Time for Changes | < 1 hour | 1 day – 1 week | 1 week – 1 month | > 1 month |
| Change Failure Rate | 0–5% | 5–10% | 10–15% | > 15% |
| MTTR | < 1 hour | < 1 day | 1 day – 1 week | > 1 week |

## Required Environment Variables

Stored in `.env` (gitignored). Use `.env.example` as the template.

```
GITHUB_TOKEN=          # PAT with repo scope targeting dora-demo-app
JIRA_BASE_URL=         # https://yoursite.atlassian.net
JIRA_EMAIL=            # Atlassian account email
JIRA_API_TOKEN=        # Jira API token (not password)
JIRA_PROJECT_KEY=DORA
```
