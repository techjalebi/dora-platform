# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**DORA Reporting Platform** — a portfolio/demo project with two sections:
1. **Simulation Engine** (`simulation/`) — Python scripts that populate GitHub and Jira Cloud with 6 months of realistic DevOps activity
2. **Dashboard** (`dashboard/`) — Vanilla HTML/CSS/JS single-page app that reads from GitHub + Jira REST APIs and renders DORA metric trend charts

## Repository Layout

```
dora-platform/
├── simulation/
│   ├── config.py           ← loads .env, exposes typed constants
│   ├── github_sim.py       ← creates backdated commits/PRs/releases in dora-demo-app
│   ├── jira_sim.py         ← creates stories + incidents in Jira DORA project
│   └── requirements.txt
├── dashboard/
│   ├── index.html          ← single-page app entry point
│   ├── css/style.css
│   └── js/
│       ├── config.js       ← repo name, proxy URL, sim timeline params
│       ├── api.js          ← fetch() wrappers for GitHub + Jira APIs
│       ├── metrics.js      ← pure DORA metric computation functions
│       ├── charts.js       ← Chart.js setup, band annotation overlays
│       └── app.js          ← boot, toggle, date picker, scorecard wiring
├── proxy/
│   └── server.py           ← Python CORS proxy for Jira (localhost:8080)
├── docs/
│   ├── generate_docs.py    ← ReportLab script — regenerates all PDFs
│   ├── project_plan.md     ← phase-by-phase task tracker (source of truth)
│   └── *.pdf               ← generated architecture + status docs
├── start_dashboard.sh      ← opens proxy + dashboard server in two terminals
├── .env                    ← secrets (gitignored)
└── .env.example            ← template
```

Target repo populated by the simulator: **techjalebi/dora-demo-app** (separate GitHub repo).

## Running the Dashboard

```bash
./start_dashboard.sh        # opens both terminals + browser automatically
```

Or manually:
```bash
# Terminal 1
python3 proxy/server.py     # Jira CORS proxy on localhost:8080

# Terminal 2
python3 -m http.server 3000 --directory dashboard
```

## Regenerating Docs

```bash
python3 docs/generate_docs.py
```

Outputs PDFs to `docs/`: architecture docs (`0.1`–`0.4`) + live status doc (`1.0_project_status.pdf`).
Always run this after updating `docs/project_plan.md` or `docs/generate_docs.py`.

## Running the Simulation

```bash
python3 -m simulation.github_sim   # Phase 2 — populate dora-demo-app
python3 -m simulation.jira_sim     # Phase 3 — populate Jira DORA project
```

Both are idempotent — jira_sim.py skips issues whose summaries already exist.

## Key Design Decisions

- **No framework, no build step** on the dashboard — plain `fetch()`, Chart.js + flatpickr via CDN
- **Backdated GitHub data**: simulation uses `GIT_AUTHOR_DATE` / `GIT_COMMITTER_DATE` env vars; GitHub release `published_at` timestamps cannot be backdated via the API — they all reflect when the sim ran
- **Simulated date reconstruction**: `dashboard/js/config.js` stores `SIM_START` and `MONTHLY_DEPLOY_COUNTS` (array of `[year, month, count]`); `api.js:buildReleaseMap()` distributes releases evenly within each month per those targets — Nov=15, Dec=5, others=10. To reshape the DF chart, change `MONTHLY_DEPLOY_COUNTS` (must sum to total releases = 60)
- **Failure release convention**: releases named `vX.Y.Z-hotfix` are failed deployments; Incident tickets reference them via the `Linked Release` custom field
- **Jira MTTR storage**: Jira Cloud cannot backdate transition timestamps — `SimulatedCreated` and `SimulatedResolved` ISO strings are stored in the Incident description; `api.js:parseDescriptionDate()` extracts them
- **Jira search API**: use `POST /rest/api/3/search/jql` with `nextPageToken` pagination — the old `GET /rest/api/3/search` returns HTTP 410 Gone on Jira Cloud
- **DORA metric sources**:
  - Deployment Frequency → GitHub release tag count per period
  - Lead Time → `First Commit Date` custom field → release date (reconstructed)
  - Change Failure Rate → Incident `Linked Release` tags / total releases per period
  - MTTR → `SimulatedCreated` → `SimulatedResolved` in Incident description

## Jira Project

- Project key: `DORA` (id: 10001)
- Custom field IDs (created in Phase 1):
  - `customfield_10039` — Deployment Version
  - `customfield_10040` — First Commit Date
  - `customfield_10041` — Incident Severity (options: P1, P2, P3)
  - `customfield_10042` — Linked Release
- Incident issue type id: `10008`
- Incident workflow: Open → Investigating → Resolved
- Story workflow: To Do → In Progress → In Review → Done

## DORA Performance Band Thresholds

| Metric | Elite | High | Medium | Low |
|---|---|---|---|---|
| Deployment Frequency | ≥ 7/week | ≥ 1/week | ≥ 1/month | < 1/month |
| Lead Time for Changes | < 1 day | < 7 days | < 30 days | ≥ 30 days |
| Change Failure Rate | ≤ 5% | ≤ 10% | ≤ 15% | > 15% |
| MTTR | < 1 hour | < 24 hours | < 168 hours | ≥ 168 hours |

## Required Environment Variables

Stored in `.env` (gitignored). Use `.env.example` as the template.

```
GITHUB_TOKEN=          # PAT with repo scope targeting dora-demo-app
JIRA_BASE_URL=         # https://yoursite.atlassian.net
JIRA_EMAIL=            # Atlassian account email
JIRA_API_TOKEN=        # Jira API token (not password)
JIRA_PROJECT_KEY=DORA
GITHUB_DEMO_REPO=techjalebi/dora-demo-app
SIM_START_DATE=2025-09-01
SIM_END_DATE=2026-03-01
SIM_FAILURE_RATE=0.15
```

## Build Plan Status

Tracked in [`docs/project_plan.md`](docs/project_plan.md). All phases 0–5 complete. Live at **https://dora.techjalebi.com**.
