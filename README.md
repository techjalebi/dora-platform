# DORA Metrics Dashboard

A full-stack DevOps portfolio project — simulates 6 months of engineering activity and visualises the four DORA metrics in a live dashboard.

**Live demo:** https://dora.techjalebi.com

Built with Claude Code · DNS via AWS Route 53 · Hosted on Oracle Cloud

---

## What are DORA Metrics?

[DORA (DevOps Research and Assessment)](https://dora.dev) defines four key metrics that predict software delivery performance:

| Metric | What it measures |
|---|---|
| **Deployment Frequency** | How often code is deployed to production |
| **Lead Time for Changes** | Time from first commit to production |
| **Change Failure Rate** | % of deployments that cause an incident |
| **MTTR** | Time to recover from a production failure |

Each metric is classified into Elite / High / Medium / Low bands based on DORA Research 2023 thresholds.

---

## Project Structure

```
dora-platform/
├── simulation/
│   ├── config.py           ← loads .env, exposes typed constants
│   ├── github_sim.py       ← creates backdated commits/PRs/releases
│   ├── jira_sim.py         ← creates stories + incidents in Jira
│   └── requirements.txt
├── dashboard/
│   ├── index.html          ← single-page app entry point
│   ├── favicon.svg
│   ├── css/style.css       ← dark theme
│   └── js/
│       ├── config.js       ← repo name, proxy URL, timeline params
│       ├── api.js          ← fetch() wrappers for GitHub + Jira APIs
│       ├── metrics.js      ← pure DORA metric computation functions
│       ├── charts.js       ← Chart.js setup + band annotation overlays
│       └── app.js          ← boot, toggle, date picker, scorecard
├── proxy/
│   └── server.py           ← Python CORS proxy for Jira (port 8080 local)
├── deploy/
│   ├── deploy.sh           ← one-shot Oracle VM deployment script
│   ├── dora-proxy.service  ← systemd unit for the Jira proxy
│   └── nginx-dora          ← nginx site config (HTTP, certbot adds SSL)
├── docs/
│   ├── project_plan.md     ← phase-by-phase task tracker
│   └── *.pdf               ← generated architecture docs
├── start_dashboard.sh      ← opens proxy + dashboard in two terminals
├── .env.example            ← secrets template
└── CLAUDE.md               ← Claude Code project instructions
```

---

## Running Locally

### Prerequisites

- Python 3.10+
- GitHub PAT (repo scope) targeting `techjalebi/dora-demo-app`
- Jira Cloud account with API token

### 1. Clone and configure

```bash
git clone https://github.com/techjalebi/dora-platform.git
cd dora-platform
cp .env.example .env
# Fill in your values in .env
```

### 2. Start the dashboard

```bash
./start_dashboard.sh
```

This opens two terminals (Jira proxy on port 8080, dashboard on port 3000) and launches the browser automatically.

Or manually:

```bash
# Terminal 1 — Jira CORS proxy
python3 proxy/server.py

# Terminal 2 — Static file server
python3 -m http.server 3000 --directory dashboard
```

Open **http://localhost:3000** in your browser.

---

## Running the Simulation

Populates `techjalebi/dora-demo-app` (GitHub) and the `DORA` Jira project with 6 months of realistic data.

```bash
pip install -r simulation/requirements.txt

python3 -m simulation.github_sim   # 60 releases, 63 PRs, ~15% hotfix
python3 -m simulation.jira_sim     # 61 stories, 9 incidents
```

Both scripts are idempotent — safe to re-run.

---

## Deploying to Your Own Server

```bash
./deploy/deploy.sh
```

Requires:
- Oracle Cloud (or any Ubuntu VM) with nginx + certbot installed
- SSH key path configured in `deploy/deploy.sh`
- DNS A record pointing your domain to the VM IP

After deploy, get SSL:

```bash
ssh ubuntu@<your-vm-ip> 'sudo certbot --nginx -d your.domain.com'
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Dashboard | Vanilla HTML / CSS / JS — no framework, no build step |
| Charts | Chart.js v4 + chartjs-plugin-annotation |
| Date picker | Flatpickr |
| Data sources | GitHub REST API + Jira Cloud REST API v3 |
| Jira proxy | Python `http.server` (handles CORS + Basic Auth) |
| Simulation | Python + PyGithub + Jira REST API |
| Hosting | Oracle Cloud VM — nginx + systemd |
| DNS | AWS Route 53 |
| SSL | Let's Encrypt (certbot, auto-renews) |

---

## DORA Band Thresholds

| Metric | Elite | High | Medium | Low |
|---|---|---|---|---|
| Deployment Frequency | ≥ 7/week | ≥ 1/week | ≥ 1/month | < 1/month |
| Lead Time for Changes | < 1 day | < 7 days | < 30 days | ≥ 30 days |
| Change Failure Rate | ≤ 5% | ≤ 10% | ≤ 15% | > 15% |
| MTTR | < 1 hour | < 24 hours | < 168 hours | ≥ 168 hours |
