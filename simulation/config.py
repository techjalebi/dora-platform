"""
config.py — Central configuration for the DORA simulation engine.
Loads values from ../.env and exposes typed constants used by all sim scripts.
"""

import os
from datetime import date
from pathlib import Path
from dotenv import load_dotenv

# Load .env from repo root
load_dotenv(Path(__file__).parent.parent / ".env")

# ── GitHub ────────────────────────────────────────────────────────────────────
GITHUB_TOKEN      = os.environ["GITHUB_TOKEN"]
GITHUB_DEMO_REPO  = os.getenv("GITHUB_DEMO_REPO", "techjalebi/dora-demo-app")

# ── Jira ─────────────────────────────────────────────────────────────────────
JIRA_BASE_URL     = os.environ["JIRA_BASE_URL"].rstrip("/")
JIRA_EMAIL        = os.environ["JIRA_EMAIL"]
JIRA_API_TOKEN    = os.environ["JIRA_API_TOKEN"]
JIRA_PROJECT_KEY  = os.getenv("JIRA_PROJECT_KEY", "DORA")

# Jira custom field IDs (created in task 1.4)
JIRA_FIELD_DEPLOYMENT_VERSION = "customfield_10039"
JIRA_FIELD_FIRST_COMMIT_DATE  = "customfield_10040"
JIRA_FIELD_INCIDENT_SEVERITY  = "customfield_10041"
JIRA_FIELD_LINKED_RELEASE     = "customfield_10042"

# ── Simulation window ────────────────────────────────────────────────────────
SIM_START_DATE = date.fromisoformat(os.getenv("SIM_START_DATE", "2025-09-01"))
SIM_END_DATE   = date.fromisoformat(os.getenv("SIM_END_DATE",   "2026-03-01"))

# ── Simulation behaviour ─────────────────────────────────────────────────────
# ~15 % of releases are failures (named vX.Y.Z-hotfix)
SIM_FAILURE_RATE = float(os.getenv("SIM_FAILURE_RATE", "0.15"))

# Approximate deployments per week (used to space release tags)
DEPLOYS_PER_WEEK = int(os.getenv("DEPLOYS_PER_WEEK", "2"))

# Commits per feature branch before a PR is opened
COMMITS_PER_BRANCH_MIN = 2
COMMITS_PER_BRANCH_MAX = 6

# Hours from incident open → resolved (used to backdate resolution)
MTTR_HOURS_MIN = 1
MTTR_HOURS_MAX = 72

# Lead time from first commit → Done transition (business days)
LEAD_TIME_DAYS_MIN = 1
LEAD_TIME_DAYS_MAX = 14

# Incident severity weights  P1 / P2 / P3
SEVERITY_WEIGHTS = {"P1": 0.2, "P2": 0.5, "P3": 0.3}
