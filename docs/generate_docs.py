"""Generate Phase 0 architecture documents as PDFs using ReportLab."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Preformatted
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

W, H = A4
MARGIN = 2 * cm

BRAND = colors.HexColor("#1a56db")
LIGHT_BLUE = colors.HexColor("#e8f0fe")
DARK = colors.HexColor("#1a1a2e")
GREY = colors.HexColor("#6b7280")
LIGHT_GREY = colors.HexColor("#f3f4f6")
GREEN = colors.HexColor("#065f46")
GREEN_BG = colors.HexColor("#d1fae5")
AMBER = colors.HexColor("#92400e")
AMBER_BG = colors.HexColor("#fef3c7")
RED = colors.HexColor("#991b1b")
RED_BG = colors.HexColor("#fee2e2")

styles = getSampleStyleSheet()

def make_styles():
    return {
        "title": ParagraphStyle("title", fontSize=22, leading=28, textColor=BRAND,
                                 fontName="Helvetica-Bold", spaceAfter=4),
        "subtitle": ParagraphStyle("subtitle", fontSize=12, leading=16, textColor=GREY,
                                    fontName="Helvetica", spaceAfter=2),
        "h2": ParagraphStyle("h2", fontSize=14, leading=18, textColor=DARK,
                              fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=6),
        "h3": ParagraphStyle("h3", fontSize=11, leading=15, textColor=BRAND,
                              fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=4),
        "body": ParagraphStyle("body", fontSize=10, leading=14, textColor=DARK,
                                fontName="Helvetica", spaceAfter=4),
        "mono": ParagraphStyle("mono", fontSize=8.5, leading=13, textColor=DARK,
                                fontName="Courier", spaceAfter=2, backColor=LIGHT_GREY,
                                leftIndent=10, rightIndent=10),
        "bullet": ParagraphStyle("bullet", fontSize=10, leading=14, textColor=DARK,
                                  fontName="Helvetica", leftIndent=16, spaceAfter=3,
                                  bulletIndent=6),
        "caption": ParagraphStyle("caption", fontSize=8, leading=11, textColor=GREY,
                                   fontName="Helvetica-Oblique", alignment=TA_CENTER),
    }

S = make_styles()

def header_block(doc_id, title, subtitle, date="2026-03-13"):
    items = [
        Paragraph(f"DORA Reporting Platform", S["subtitle"]),
        Spacer(1, 4),
        Paragraph(title, S["title"]),
        Paragraph(subtitle, S["subtitle"]),
        Spacer(1, 6),
        HRFlowable(width="100%", thickness=2, color=BRAND),
        Spacer(1, 4),
        Paragraph(f"Document ID: {doc_id} &nbsp;&nbsp;|&nbsp;&nbsp; Date: {date} &nbsp;&nbsp;|&nbsp;&nbsp; Status: <font color='#065f46'>Complete</font>", S["caption"]),
        Spacer(1, 12),
    ]
    return items

def section(title, body_paragraphs):
    items = [Paragraph(title, S["h2"])]
    for p in body_paragraphs:
        items.append(p)
    return items

def bullet(text):
    return Paragraph(f"• &nbsp; {text}", S["bullet"])

def body(text):
    return Paragraph(text, S["body"])

def code_block(text):
    return Preformatted(text, S["mono"])

def colored_table(data, col_widths, header_bg=BRAND, header_fg=colors.white):
    t = Table(data, colWidths=col_widths)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), header_bg),
        ("TEXTCOLOR", (0, 0), (-1, 0), header_fg),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]
    t.setStyle(TableStyle(style))
    return t


# ─────────────────────────────────────────────────────────
# DOC 0.1 — Project Architecture & Component Diagram
# ─────────────────────────────────────────────────────────
def doc_01():
    path = "docs/0.1_project_architecture.pdf"
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=MARGIN, bottomMargin=MARGIN)
    story = []
    story += header_block("DORA-ARCH-0.1", "Project Architecture &amp; Component Diagram",
                          "System overview, data flows, and component responsibilities")

    story += section("Overview", [
        body("The DORA Reporting Platform consists of two independently operable sections that share "
             "GitHub and Jira Cloud as the central data store."),
    ])

    story += section("High-Level Components", [
        colored_table(
            [
                ["Component", "Type", "Responsibility"],
                ["Data Simulation Engine", "Python scripts", "Generates realistic DevOps activity in GitHub and Jira"],
                ["GitHub (dora-demo-app)", "External SaaS", "Stores commits, PRs, releases — source of deployment data"],
                ["Jira Cloud (DORA project)", "External SaaS", "Stores stories and incidents — source of lead time & MTTR"],
                ["CORS Proxy Server", "Python (Flask/http.server)", "Forwards Jira API calls from the browser with auth headers"],
                ["DORA Dashboard", "Vanilla HTML/CSS/JS", "Reads APIs, computes metrics, renders charts"],
            ],
            [5*cm, 4*cm, 7.5*cm]
        ),
        Spacer(1, 10),
    ])

    story += section("Component Diagram (Text)", [
        code_block(
"""┌──────────────────────────────────────────────────────────────┐
│                   DORA Reporting Platform                     │
└──────────────────────────────────────────────────────────────┘

┌─────────────────────────┐     ┌────────────────────────────┐
│  Simulation Engine      │     │  Dashboard (Browser)       │
│  (Python, local)        │     │  index.html                │
│                         │     │  js/api.js                 │
│  github_sim.py ─────────┼──▶  │  js/metrics.js             │
│  jira_sim.py   ─────────┼──▶  │  js/charts.js              │
│  run_simulation.py      │     │  js/app.js                 │
│  config.py              │     └──────────┬─────────────────┘
└─────────────────────────┘                │ fetch()
                                           │
              ┌────────────────────────────┼───────────┐
              │                            │           │
              ▼                            ▼           ▼
  ┌───────────────────┐     ┌──────────────────┐  ┌───────────┐
  │  GitHub Cloud     │     │  CORS Proxy      │  │  Jira     │
  │  dora-demo-app    │     │  server.py       │  │  Cloud    │
  │  - commits        │     │  localhost:8080  │  │  DORA     │
  │  - pull requests  │     └────────┬─────────┘  │  project  │
  │  - releases/tags  │              │             └─────┬─────┘
  └───────────────────┘              └─────────────────▶┘
         ▲                                Jira REST API
         │
  GitHub REST API
"""
        ),
        Paragraph("Figure 1 — Component and data flow diagram", S["caption"]),
        Spacer(1, 10),
    ])

    story += section("Data Flow", [
        colored_table(
            [
                ["Flow", "Source", "Destination", "Protocol"],
                ["Simulation writes", "github_sim.py / jira_sim.py", "GitHub + Jira Cloud", "REST API (PyGithub / requests)"],
                ["Deployment data read", "Dashboard js/api.js", "GitHub REST API", "fetch() — no CORS issue"],
                ["Jira data read", "Dashboard js/api.js", "localhost proxy → Jira", "fetch() → HTTP forward"],
                ["Chart render", "js/metrics.js output", "Chart.js canvas", "In-browser JS"],
            ],
            [3.5*cm, 4*cm, 4*cm, 5*cm]
        ),
        Spacer(1, 10),
    ])

    story += section("DORA Metrics Mapping", [
        colored_table(
            [
                ["DORA Metric", "Data Source", "Signal"],
                ["Deployment Frequency", "GitHub releases/tags", "Count of releases per week/month"],
                ["Lead Time for Changes", "GitHub PR open→merge + Jira story", "Time from first commit to release"],
                ["Change Failure Rate", "GitHub releases + Jira incidents", "% releases that triggered an incident"],
                ["MTTR", "Jira Incident tickets", "Time from Incident Open → Resolved"],
            ],
            [4.5*cm, 4.5*cm, 7.5*cm]
        ),
    ])

    doc.build(story)
    print(f"  ✓ {path}")


# ─────────────────────────────────────────────────────────
# DOC 0.2 — GitHub Repo Structure
# ─────────────────────────────────────────────────────────
def doc_02():
    path = "docs/0.2_github_repo_structure.pdf"
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=MARGIN, bottomMargin=MARGIN)
    story = []
    story += header_block("DORA-ARCH-0.2", "GitHub Repository Structure",
                          "Repo layout for dora-platform and dora-demo-app")

    story += section("Two-Repo Design", [
        body("The project uses two GitHub repositories with distinct responsibilities:"),
        colored_table(
            [
                ["Repo", "Purpose", "Visibility"],
                ["dora-platform", "Dashboard source + simulation scripts (this repo)", "Public"],
                ["dora-demo-app", "Fake application repo populated by the simulator", "Public"],
            ],
            [4.5*cm, 9*cm, 3*cm]
        ),
        Spacer(1, 10),
    ])

    story += section("dora-platform — Directory Layout", [
        code_block(
"""dora-platform/
│
├── simulation/
│   ├── config.py              # API tokens, date ranges, volume params
│   ├── github_sim.py          # Creates commits/PRs/releases in dora-demo-app
│   ├── jira_sim.py            # Creates/transitions Jira tickets
│   ├── run_simulation.py      # Orchestrator — runs both scripts in order
│   └── requirements.txt       # PyGithub, requests, python-dateutil
│
├── dashboard/
│   ├── index.html             # Single-page application entry point
│   ├── css/
│   │   └── style.css          # All dashboard styles
│   └── js/
│       ├── config.js          # API base URLs (gitignored tokens)
│       ├── api.js             # fetch() wrappers for GitHub + Jira APIs
│       ├── metrics.js         # DORA metric computation logic
│       ├── charts.js          # Chart.js setup and rendering
│       └── app.js             # Entry point — wires everything together
│
├── proxy/
│   ├── server.py              # Minimal proxy: handles Jira CORS + Basic Auth
│   └── requirements.txt       # flask or just stdlib http.server
│
├── docs/                      # Architecture documents (this folder)
│   ├── 0.1_project_architecture.pdf
│   ├── 0.2_github_repo_structure.pdf
│   ├── 0.3_jira_project_setup.pdf
│   ├── 0.4_build_plan.pdf
│   └── project_plan.md
│
├── .env.example               # Template: GITHUB_TOKEN, JIRA_TOKEN, etc.
├── .gitignore                 # Ignores .env, __pycache__, *.pyc
└── README.md                  # Setup and run instructions"""
        ),
        Spacer(1, 10),
    ])

    story += section("dora-demo-app — Directory Layout", [
        body("This repo is populated entirely by github_sim.py. It simulates a real application codebase."),
        code_block(
"""dora-demo-app/
│
├── src/
│   ├── main.py                # Fake application code (touched by commits)
│   ├── utils.py
│   └── config.py
│
├── tests/
│   └── test_main.py
│
├── CHANGELOG.md               # Updated on each simulated release
└── README.md"""
        ),
        Spacer(1, 10),
    ])

    story += section("Key File Responsibilities", [
        colored_table(
            [
                ["File", "What it does"],
                ["simulation/config.py", "Central config: start/end dates, failure rate %, PR volume, Jira project key, repo names"],
                ["simulation/github_sim.py", "Uses PyGithub + local git to create backdated commits, open/merge PRs, create release tags"],
                ["simulation/jira_sim.py", "Uses Jira REST API to create stories/incidents, perform transitions with timestamps"],
                ["simulation/run_simulation.py", "Runs github_sim then jira_sim, links Jira tickets to GitHub PRs via branch name"],
                ["dashboard/js/api.js", "All fetch() calls — encapsulates GitHub + Jira endpoints, pagination, error handling"],
                ["dashboard/js/metrics.js", "Pure functions: takes raw API responses, returns aggregated DORA metric arrays by week/month"],
                ["dashboard/js/charts.js", "Chart.js configuration, DORA band overlay lines, weekly/monthly dataset swap"],
                ["proxy/server.py", "Listens on localhost:8080, forwards /jira/* to Jira Cloud with Basic Auth header injected"],
            ],
            [5*cm, 11.5*cm]
        ),
    ])

    story += section("Branching Convention in dora-demo-app", [
        body("The simulator creates branches following a naming pattern so Jira tickets can be linked:"),
        colored_table(
            [
                ["Branch pattern", "Example", "Linked Jira ticket"],
                ["feature/DORA-{n}-{slug}", "feature/DORA-42-add-login", "DORA-42 (Story)"],
                ["hotfix/DORA-{n}-{slug}", "hotfix/DORA-87-fix-crash", "DORA-87 (Incident)"],
                ["release/v{x.y.z}", "release/v1.4.0", "Tagged as GitHub release"],
            ],
            [5*cm, 5.5*cm, 6*cm]
        ),
    ])

    doc.build(story)
    print(f"  ✓ {path}")


# ─────────────────────────────────────────────────────────
# DOC 0.3 — Jira Project Setup
# ─────────────────────────────────────────────────────────
def doc_03():
    path = "docs/0.3_jira_project_setup.pdf"
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=MARGIN, bottomMargin=MARGIN)
    story = []
    story += header_block("DORA-ARCH-0.3", "Jira Project Setup",
                          "Issue types, custom fields, workflow, and JQL queries")

    story += section("Project Configuration", [
        colored_table(
            [
                ["Setting", "Value"],
                ["Project name", "DORA Demo App"],
                ["Project key", "DORA"],
                ["Project type", "Scrum"],
                ["Board type", "Scrum board with sprints"],
            ],
            [5*cm, 11.5*cm]
        ),
        Spacer(1, 10),
    ])

    story += section("Issue Types", [
        colored_table(
            [
                ["Issue Type", "Purpose", "DORA Metric"],
                ["Story", "Feature work — represents a change being developed", "Lead Time for Changes"],
                ["Bug", "Defect work — also represents a change", "Lead Time for Changes"],
                ["Incident", "Production failure triggered by a bad release", "Change Failure Rate + MTTR"],
                ["Task", "Optional: manual deployment log entries", "Deployment Frequency (fallback)"],
            ],
            [3*cm, 7*cm, 6.5*cm]
        ),
        Spacer(1, 10),
    ])

    story += section("Custom Fields", [
        colored_table(
            [
                ["Field Name", "Type", "Used On", "Purpose"],
                ["Deployment Version", "Text (single line)", "Story, Bug", "Links ticket to the GitHub release tag that shipped it"],
                ["First Commit Date", "Date", "Story, Bug", "Timestamp of first commit — lead time start point"],
                ["Incident Severity", "Select list", "Incident", "P1 / P2 / P3 — filter high-severity for CFR calculation"],
                ["Linked Release", "Text (single line)", "Incident", "GitHub release tag that caused this incident"],
            ],
            [3.5*cm, 3.5*cm, 3*cm, 6.5*cm]
        ),
        Spacer(1, 6),
        body("Incident Severity select options: P1 (Critical), P2 (Major), P3 (Minor)"),
        Spacer(1, 10),
    ])

    story += section("Workflow", [
        body("Stories and Bugs follow the standard delivery workflow:"),
        code_block("  [To Do] → [In Progress] → [In Review] → [Done]\n                                        ↘ [Cancelled]"),
        Spacer(1, 6),
        body("Incidents follow an incident response workflow:"),
        code_block("  [Open] → [Investigating] → [Resolved]"),
        Spacer(1, 10),
    ])

    story += section("DORA Metric Mapping to Jira Fields", [
        colored_table(
            [
                ["DORA Metric", "Calculation", "Jira Fields Used"],
                ["Lead Time for Changes",
                 "Avg time: First Commit Date → Story status = Done",
                 "First Commit Date (custom), status change log"],
                ["Change Failure Rate",
                 "Count(Incidents) / Count(Releases) in period",
                 "Incident issue type, Linked Release field, created date"],
                ["MTTR",
                 "Avg time: Incident created → Incident status = Resolved",
                 "created field, status change log (Resolved timestamp)"],
            ],
            [3.5*cm, 5.5*cm, 7.5*cm]
        ),
        Spacer(1, 10),
    ])

    story += section("Key JQL Queries", [
        body("Stories reaching Done (proxy for deployments shipped) in a date range:"),
        code_block('project = DORA AND issuetype in (Story, Bug)\n  AND status changed to Done after "2025-09-01"'),
        Spacer(1, 6),
        body("All incidents (change failures):"),
        code_block('project = DORA AND issuetype = Incident\n  AND created >= "2025-09-01"'),
        Spacer(1, 6),
        body("Resolved incidents for MTTR calculation:"),
        code_block('project = DORA AND issuetype = Incident\n  AND status = Resolved\n  AND created >= "2025-09-01"'),
        Spacer(1, 6),
        body("Incidents linked to a specific release (for CFR):"),
        code_block('project = DORA AND issuetype = Incident\n  AND "Linked Release" = "v1.4.0"'),
    ])

    doc.build(story)
    print(f"  ✓ {path}")


# ─────────────────────────────────────────────────────────
# DOC 0.4 — Build Plan
# ─────────────────────────────────────────────────────────
def doc_04():
    path = "docs/0.4_build_plan.pdf"
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=MARGIN, bottomMargin=MARGIN)
    story = []
    story += header_block("DORA-ARCH-0.4", "Step-by-Step Build Plan",
                          "Phase ordering, task breakdown, and rationale")

    story += section("Build Strategy", [
        body("The simulation engine is built before the dashboard because the dashboard requires "
             "populated data to develop and test against. Each phase produces a working artifact "
             "before the next phase begins."),
        colored_table(
            [
                ["Phase", "Name", "Output"],
                ["Phase 0", "Architecture & Planning", "Design docs (this set)"],
                ["Phase 1", "Setup & Config", "Two repos, Jira project, config files"],
                ["Phase 2", "GitHub Simulation", "6 months of commits, PRs, releases in dora-demo-app"],
                ["Phase 3", "Jira Simulation", "6 months of stories and incidents in DORA project"],
                ["Phase 4", "Dashboard Core", "Working dashboard reading real API data"],
                ["Phase 5", "Classification & Polish", "DORA bands, scorecard, date picker, GitHub Pages deploy"],
            ],
            [1.8*cm, 4.5*cm, 10.2*cm]
        ),
        Spacer(1, 10),
    ])

    phases = [
        ("Phase 1 — Setup & Config", [
            ("1.1", "Create dora-demo-app GitHub repo (simulation target repo)"),
            ("1.2", "Create dora-platform GitHub repo (dashboard + sim scripts)"),
            ("1.3", "Set up Jira Cloud project (DORA) with issue types and workflow"),
            ("1.4", "Add four custom Jira fields: Deployment Version, First Commit Date, Incident Severity, Linked Release"),
            ("1.5", "Write config.py with API tokens, date ranges (Sep 2025 – Mar 2026), simulation params"),
            ("1.6", "Create .env.example and .gitignore"),
        ]),
        ("Phase 2 — GitHub Simulation", [
            ("2.1", "Write github_sim.py: backdated commits using GIT_AUTHOR_DATE / GIT_COMMITTER_DATE env vars"),
            ("2.2", "Script PR creation and merge events spread across 6 months (~3–5 PRs/week)"),
            ("2.3", "Script release tag creation after each batch of merged PRs (releases = deployments)"),
            ("2.4", "Inject ~15% failure releases with naming convention vX.Y.Z-hotfix"),
        ]),
        ("Phase 3 — Jira Simulation", [
            ("3.1", "Write jira_sim.py: create stories linked to feature branches (one story per PR)"),
            ("3.2", "Simulate ticket transitions with backdated timestamps matching GitHub PR timeline"),
            ("3.3", "Create incident tickets for each failure release (within 48h of release date)"),
            ("3.4", "Transition incidents to Resolved after simulated MTTR duration (2–72 hours)"),
            ("3.5", "Run run_simulation.py orchestrator and validate data looks realistic"),
        ]),
        ("Phase 4 — Dashboard Core", [
            ("4.1", "Build index.html skeleton: header, 4 metric panels, weekly/monthly toggle"),
            ("4.2", "Write js/api.js: fetch wrappers for GitHub /releases, /pulls, /commits; Jira /search"),
            ("4.3", "Write proxy/server.py: local proxy for Jira CORS and Basic Auth injection"),
            ("4.4", "Write js/metrics.js: pure functions computing 4 DORA metrics by week and month"),
            ("4.5", "Write js/charts.js: Chart.js line/bar charts, dataset switching on toggle"),
            ("4.6", "Implement weekly / monthly toggle wired to chart dataset swap"),
        ]),
        ("Phase 5 — Classification & Polish", [
            ("5.1", "Add DORA performance band overlay lines to each chart (Elite/High/Medium/Low thresholds)"),
            ("5.2", "Add summary scorecard: one badge per metric showing current classification"),
            ("5.3", "Add date range picker to filter chart data"),
            ("5.4", "Style and polish (css/style.css) — clean, professional dashboard look"),
            ("5.5", "Deploy dashboard to GitHub Pages"),
            ("5.6", "Write README.md with setup and run instructions"),
        ]),
    ]

    for phase_title, tasks in phases:
        story += [Paragraph(phase_title, S["h2"])]
        rows = [["#", "Task"]]
        for num, desc in tasks:
            rows.append([num, desc])
        story.append(colored_table(rows, [1.5*cm, 15*cm]))
        story.append(Spacer(1, 10))

    story += section("DORA Performance Band Thresholds", [
        body("These are the standard DORA Research thresholds used for classification in Phase 5:"),
        colored_table(
            [
                ["Metric", "Elite", "High", "Medium", "Low"],
                ["Deployment Frequency", "On-demand (multiple/day)", "Weekly", "Monthly", "< Monthly"],
                ["Lead Time for Changes", "< 1 hour", "1 day – 1 week", "1 week – 1 month", "> 1 month"],
                ["Change Failure Rate", "0–5%", "5–10%", "10–15%", "> 15%"],
                ["MTTR", "< 1 hour", "< 1 day", "1 day – 1 week", "> 1 week"],
            ],
            [4.5*cm, 3.5*cm, 3.5*cm, 3.5*cm, 2*cm]
        ),
    ])

    doc.build(story)
    print(f"  ✓ {path}")


if __name__ == "__main__":
    print("Generating Phase 0 architecture documents...")
    doc_01()
    doc_02()
    doc_03()
    doc_04()
    print("Done. All PDFs written to docs/")
