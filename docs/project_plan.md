# DORA Reporting Platform — Project Plan

Last updated: 2026-03-27

## Legend
- ✅ Complete
- 🔄 In Progress
- ⬜ Pending

---

## Phase 0 — Architecture & Planning
| # | Task | Status |
|---|------|--------|
| 0.1 | Define project architecture and component diagram | ✅ |
| 0.2 | Define GitHub repo structure | ✅ |
| 0.3 | Define Jira project setup (issue types, fields, workflow) | ✅ |
| 0.4 | Define build plan and phase ordering | ✅ |

---

## Phase 1 — Setup & Config
| # | Task | Status |
|---|------|--------|
| 1.1 | Create `dora-demo-app` GitHub repo (simulation target) | ✅ |
| 1.2 | Create `dora-platform` GitHub repo (dashboard + scripts) | ✅ |
| 1.3 | Set up Jira Cloud project (`DORA`) with issue types and workflow | ✅ |
| 1.4 | Add custom Jira fields (`Deployment Version`, `First Commit Date`, `Incident Severity`, `Linked Release`) | ✅ |
| 1.5 | Write `config.py` with API tokens, date ranges, simulation parameters | ✅ |
| 1.6 | Create `.env.example` and `.gitignore` | ✅ |

---

## Phase 2 — GitHub Simulation
| # | Task | Status |
|---|------|--------|
| 2.1 | Write `github_sim.py` — backdated commits using `GIT_AUTHOR_DATE` / `GIT_COMMITTER_DATE` | ✅ |
| 2.2 | Script PR creation and merge events spread across 6 months | ✅ |
| 2.3 | Script release tag creation (releases = deployments) | ✅ |
| 2.4 | Inject ~15% failure releases (naming: `vX.Y.Z-hotfix`) | ✅ |

---

## Phase 3 — Jira Simulation
| # | Task | Status |
|---|------|--------|
| 3.1 | Write `jira_sim.py` — create stories linked to feature branches | ✅ |
| 3.2 | Simulate ticket transitions with backdated timestamps | ✅ |
| 3.3 | Create incident tickets triggered by failure releases | ✅ |
| 3.4 | Transition incidents to Resolved (simulates MTTR) | ✅ |
| 3.5 | Run `run_simulation.py` orchestrator and validate data | ✅ |

---

## Phase 4 — Dashboard Core
| # | Task | Status |
|---|------|--------|
| 4.1 | Build `index.html` skeleton with 4 metric panels | ✅ |
| 4.2 | Write `js/api.js` — GitHub + Jira API fetch functions | ✅ |
| 4.3 | Write `proxy/server.py` — local proxy to handle Jira CORS + auth | ✅ |
| 4.4 | Write `js/metrics.js` — compute all 4 DORA metrics from raw API data | ✅ |
| 4.5 | Write `js/charts.js` — Chart.js line/bar charts | ✅ |
| 4.6 | Implement weekly / monthly toggle | ✅ |

---

## Phase 5 — DORA Classification & Polish
| # | Task | Status |
|---|------|--------|
| 5.1 | Add DORA performance band overlays (Elite / High / Medium / Low) per metric | ✅ |
| 5.2 | Add summary scorecard showing current classification per metric | ✅ |
| 5.3 | Add date range picker | ✅ |
| 5.4 | Style and polish (`css/style.css`) | ✅ |
| 5.5 | Deploy dashboard + proxy to Oracle VM (nginx + systemd) | ✅ |
| 5.6 | Write `README.md` with setup and run instructions | ✅ |
