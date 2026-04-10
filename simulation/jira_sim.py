"""
jira_sim.py — Populates the Jira DORA project with 6 months of simulated
stories and incidents that mirror the GitHub activity created by github_sim.py.

Data strategy
─────────────
Jira Cloud does not allow backdating issue creation or transition timestamps
via the REST API. Instead we store simulated dates in structured fields:

  Stories
    • First Commit Date  (customfield_10040) = PR branch creation date
    • Deployment Version (customfield_10039) = GitHub release tag that shipped it
    • Lead time on the dashboard = First Commit Date → release date (from GitHub)

  Incidents
    • Linked Release     (customfield_10042) = hotfix tag that caused it
    • Incident Severity  (customfield_10041) = P1 / P2 / P3
    • Description stores  "SimulatedCreated: <ISO>" and "SimulatedResolved: <ISO>"
      so the dashboard can compute MTTR without relying on Jira internal timestamps.

Run from repo root:
    python3 -m simulation.jira_sim
"""

import json
import random
import time
import base64
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Optional

from github import Auth, Github

from simulation.config import (
    GITHUB_TOKEN, GITHUB_DEMO_REPO,
    JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT_KEY,
    JIRA_FIELD_DEPLOYMENT_VERSION, JIRA_FIELD_FIRST_COMMIT_DATE,
    JIRA_FIELD_INCIDENT_SEVERITY, JIRA_FIELD_LINKED_RELEASE,
    SIM_START_DATE, SIM_END_DATE,
    MTTR_HOURS_MIN, MTTR_HOURS_MAX,
    LEAD_TIME_DAYS_MIN, LEAD_TIME_DAYS_MAX,
    SEVERITY_WEIGHTS,
)

random.seed(42)

# ── Jira HTTP helpers ─────────────────────────────────────────────────────────

_AUTH = base64.b64encode(f"{JIRA_EMAIL}:{JIRA_API_TOKEN}".encode()).decode()
_HEADERS = {
    "Authorization": f"Basic {_AUTH}",
    "Accept": "application/json",
    "Content-Type": "application/json",
}


def jira(method: str, path: str, data: dict | None = None,
         base: str = "/rest/api/3") -> dict:
    url = JIRA_BASE_URL + base + path
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=_HEADERS, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            body = r.read()
            return json.loads(body) if body.strip() else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return {"_error": e.code, "_msg": json.loads(raw)}
        except Exception:
            return {"_error": e.code, "_msg": raw}


def ok(r: dict) -> bool:
    return "_error" not in r


# ── Jira setup helpers ────────────────────────────────────────────────────────

def add_fields_to_screens():
    """Add custom fields to the DORA project's default create/edit screens."""
    custom_fields = [
        JIRA_FIELD_DEPLOYMENT_VERSION,
        JIRA_FIELD_FIRST_COMMIT_DATE,
        JIRA_FIELD_INCIDENT_SEVERITY,
        JIRA_FIELD_LINKED_RELEASE,
    ]
    screens = jira("GET", "/screens?maxResults=100")
    added = 0
    for screen in screens.get("values", []):
        screen_id = screen["id"]
        # Get tabs for this screen
        tabs = jira("GET", f"/screens/{screen_id}/tabs")
        for tab in tabs if isinstance(tabs, list) else tabs.get("values", []):
            tab_id = tab["id"]
            # Get existing fields on this tab
            existing = jira("GET", f"/screens/{screen_id}/tabs/{tab_id}/fields")
            existing_ids = {f["id"] for f in (existing if isinstance(existing, list) else [])}
            for fid in custom_fields:
                if fid not in existing_ids:
                    r = jira("POST", f"/screens/{screen_id}/tabs/{tab_id}/fields",
                             {"fieldId": fid})
                    if ok(r):
                        added += 1
    print(f"  Added {added} field-screen assignments")


def ensure_incident_severity_options() -> Optional[str]:
    """Add P1/P2/P3 options to the Incident Severity select field."""
    fields = jira("GET", "/field")
    field_id = None
    for f in fields:
        if f.get("id") == JIRA_FIELD_INCIDENT_SEVERITY:
            field_id = f["id"]
            break
    if not field_id:
        print("  ⚠  Could not find Incident Severity field")
        return None

    # Fetch existing context + options
    contexts = jira("GET", f"/field/{field_id}/context")
    if not ok(contexts) or not contexts.get("values"):
        print("  ⚠  No context found for Incident Severity field")
        return None

    ctx_id = contexts["values"][0]["id"]

    # Add options if missing
    options_resp = jira("GET", f"/field/{field_id}/context/{ctx_id}/option")
    existing = {o["value"] for o in options_resp.get("values", [])}
    to_add = [v for v in ["P1", "P2", "P3"] if v not in existing]
    if to_add:
        jira("POST", f"/field/{field_id}/context/{ctx_id}/option",
             {"options": [{"value": v} for v in to_add]})
        print(f"  Added severity options: {to_add}")

    # Return option IDs keyed by value
    options_resp = jira("GET", f"/field/{field_id}/context/{ctx_id}/option")
    return {o["value"]: o["id"] for o in options_resp.get("values", [])}


def get_transition_ids(issue_key: str) -> dict[str, str]:
    """Return {transition_name: id} for a given issue."""
    r = jira("GET", f"/issue/{issue_key}/transitions")
    return {t["name"]: t["id"] for t in r.get("transitions", [])}


def transition(issue_key: str, name: str, trans_map: dict[str, str]) -> bool:
    tid = trans_map.get(name)
    if not tid:
        return False
    r = jira("POST", f"/issue/{issue_key}/transitions",
             {"transition": {"id": tid}})
    return ok(r)


def existing_summaries() -> set[str]:
    """Fetch all issue summaries already in the project (to avoid duplicates)."""
    summaries = set()
    next_page_token = None
    while True:
        body = {
            "jql": f"project={JIRA_PROJECT_KEY}",
            "fields": ["summary"],
            "maxResults": 100,
        }
        if next_page_token:
            body["nextPageToken"] = next_page_token
        r = jira("POST", "/search/jql", body)
        issues = r.get("issues", [])
        if not issues:
            break
        for i in issues:
            summaries.add(i["fields"]["summary"])
        next_page_token = r.get("nextPageToken")
        if not next_page_token or len(issues) < 100:
            break
    return summaries


# ── GitHub data fetch ─────────────────────────────────────────────────────────

def fetch_github_data() -> tuple[list[dict], list[dict]]:
    """
    Returns:
        releases — list of dicts with keys: tag, date (simulated), is_hotfix
        stories  — list of dicts with keys: title, branch, release_tag,
                   first_commit_date, done_date (all simulated dates)

    NOTE: GitHub release published_at timestamps reflect when the simulation
    script ran, not the simulated period.  We reconstruct the simulated
    timeline from the release order using the same spacing formula as
    github_sim.py (deploy_interval = 7 // DEPLOYS_PER_WEEK days).
    """
    from simulation.config import DEPLOYS_PER_WEEK

    g = Github(auth=Auth.Token(GITHUB_TOKEN))
    repo = g.get_repo(GITHUB_DEMO_REPO)

    sim_start = datetime(SIM_START_DATE.year, SIM_START_DATE.month,
                         SIM_START_DATE.day, 9, 0, tzinfo=timezone.utc)

    deploy_interval = 7 // DEPLOYS_PER_WEEK   # days between releases

    print("Fetching GitHub releases…")
    raw_releases = sorted(repo.get_releases(), key=lambda r: r.id)
    releases = []
    for i, rel in enumerate(raw_releases):
        # Reconstruct the simulated date from release index
        sim_date = sim_start + timedelta(days=(i + 1) * deploy_interval)
        releases.append({
            "tag":        rel.tag_name,
            "date":       sim_date,
            "is_hotfix":  rel.tag_name.endswith("-hotfix"),
        })
    print(f"  Found {len(releases)} releases "
          f"({sum(1 for r in releases if r['is_hotfix'])} hotfixes)")

    print("Fetching merged PRs…")
    all_prs = [pr for pr in repo.get_pulls(
                   state="closed", base="main", sort="created", direction="asc")
               if pr.merged_at]
    print(f"  Found {len(all_prs)} merged PRs")

    # Assign each PR to its nearest release (first release after PR creation order)
    # PRs and releases are both in creation order; zip them loosely.
    stories = []
    rel_iter = iter(releases)
    current_rel = next(rel_iter, None)

    for idx, pr in enumerate(all_prs):
        if current_rel is None:
            break

        # Assign to current release; advance release every ~2 PRs on average
        release_tag = current_rel["tag"]
        release_date = current_rel["date"]

        # Simulate first commit = N days before release
        lead_days = random.randint(LEAD_TIME_DAYS_MIN, LEAD_TIME_DAYS_MAX)
        first_commit_dt = release_date - timedelta(days=lead_days)
        if first_commit_dt < sim_start:
            first_commit_dt = sim_start

        stories.append({
            "title":             pr.title,
            "branch":            pr.head.ref,
            "pr_number":         pr.number,
            "release_tag":       release_tag,
            "first_commit_date": first_commit_dt,
            "done_date":         release_date,
        })

        # Advance to next release every PR so all releases get coverage
        current_rel = next(rel_iter, current_rel)

    print(f"  Mapped {len(stories)} PRs to releases")
    return releases, stories


# ── Story creation ────────────────────────────────────────────────────────────

def create_stories(stories: list[dict], skip_summaries: set[str]) -> int:
    created = 0
    for s in stories:
        summary = f"[{s['release_tag']}] {s['title']}"
        if summary in skip_summaries:
            continue

        first_commit_str = s["first_commit_date"].strftime("%Y-%m-%d")
        desc_text = (
            f"Simulated story for PR #{s['pr_number']} on branch `{s['branch']}`.\n\n"
            f"Release: {s['release_tag']}\n"
            f"First Commit Date: {first_commit_str}\n"
            f"Merged: {s['done_date'].strftime('%Y-%m-%d %H:%M UTC')}"
        )

        payload = {
            "fields": {
                "project":     {"key": JIRA_PROJECT_KEY},
                "issuetype":   {"name": "Story"},
                "summary":     summary,
                "description": {
                    "type":    "doc",
                    "version": 1,
                    "content": [{
                        "type":    "paragraph",
                        "content": [{"type": "text", "text": desc_text}]
                    }]
                },
            }
        }

        r = jira("POST", "/issue", payload)
        if not ok(r):
            print(f"  ✗ Story failed ({summary[:50]}): {r.get('_msg', r)}")
            continue

        key = r["key"]
        created += 1

        # Update custom fields post-create (avoids screen restriction errors)
        jira("PUT", f"/issue/{key}", {"fields": {
            JIRA_FIELD_DEPLOYMENT_VERSION: s["release_tag"],
            JIRA_FIELD_FIRST_COMMIT_DATE:  first_commit_str,
        }})

        # Transition: To Do → In Progress → In Review → Done
        trans = get_transition_ids(key)
        for step in ["In Progress", "In Review", "Done"]:
            if not transition(key, step, trans):
                # Re-fetch transitions after each step
                trans = get_transition_ids(key)
                transition(key, step, trans)

        print(f"  ✓ {key}  {summary[:60]}")
        skip_summaries.add(summary)
        time.sleep(0.3)   # stay within Jira rate limits

    return created


# ── Incident creation ─────────────────────────────────────────────────────────

def create_incidents(releases: list[dict], severity_options: dict,
                     skip_summaries: set[str]) -> int:
    hotfixes = [r for r in releases if r["is_hotfix"]]
    created = 0

    for rel in hotfixes:
        summary = f"Incident: production failure in {rel['tag']}"
        if summary in skip_summaries:
            continue

        # Simulate: incident opened shortly after the release
        open_offset_h = random.randint(1, 6)
        open_dt = rel["date"] + timedelta(hours=open_offset_h)

        # MTTR: incident resolved N hours later
        mttr_h = random.randint(MTTR_HOURS_MIN, MTTR_HOURS_MAX)
        resolved_dt = open_dt + timedelta(hours=mttr_h)

        # Severity weighted choice
        severity = random.choices(
            list(SEVERITY_WEIGHTS.keys()),
            weights=list(SEVERITY_WEIGHTS.values())
        )[0]

        desc_text = (
            f"Production incident triggered by release {rel['tag']}.\n\n"
            f"SimulatedCreated: {open_dt.strftime('%Y-%m-%dT%H:%M:%SZ')}\n"
            f"SimulatedResolved: {resolved_dt.strftime('%Y-%m-%dT%H:%M:%SZ')}\n"
            f"MTTR_Hours: {mttr_h}\n"
            f"Severity: {severity}"
        )

        severity_id = severity_options.get(severity)
        issue_fields = {
            "project":    {"key": JIRA_PROJECT_KEY},
            "issuetype":  {"name": "Incident"},
            "summary":    summary,
            "description": {
                "type":    "doc",
                "version": 1,
                "content": [{
                    "type":    "paragraph",
                    "content": [{"type": "text", "text": desc_text}]
                }]
            },
        }
        if severity_id:
            issue_fields[JIRA_FIELD_INCIDENT_SEVERITY] = {"id": severity_id}

        r = jira("POST", "/issue", {"fields": issue_fields})
        if not ok(r):
            print(f"  ✗ Incident failed ({summary[:50]}): {r.get('_msg', r)}")
            continue

        key = r["key"]
        created += 1

        # Update custom fields that may not be on create screen
        jira("PUT", f"/issue/{key}", {"fields": {
            JIRA_FIELD_LINKED_RELEASE: rel["tag"],
        }})

        # Transition: Open → Investigating → Resolved
        trans = get_transition_ids(key)
        for step in ["Investigating", "Resolved"]:
            if not transition(key, step, trans):
                trans = get_transition_ids(key)
                transition(key, step, trans)

        print(f"  ✓ {key}  {summary}  [{severity}]  MTTR={mttr_h}h")
        skip_summaries.add(summary)
        time.sleep(0.3)

    return created


# ── Entry point ───────────────────────────────────────────────────────────────

def run():
    print("=" * 60)
    print("DORA Jira Simulation")
    print("=" * 60)

    # 1. Add custom fields to screens
    print("\n[Setup] Adding custom fields to Jira screens…")
    add_fields_to_screens()

    # 2. Ensure severity options exist
    print("\n[Setup] Configuring Incident Severity field options…")
    severity_options = ensure_incident_severity_options()
    if not severity_options:
        severity_options = {}

    # 2. Fetch GitHub data
    print("\n[GitHub] Loading releases and merged PRs…")
    releases, stories = fetch_github_data()

    # 3. Load existing Jira summaries to skip duplicates
    print("\n[Jira] Checking for existing issues…")
    skip = existing_summaries()
    print(f"  {len(skip)} issues already exist — will skip duplicates")

    # 4. Create stories
    print(f"\n[Stories] Creating {len(stories)} stories…")
    s_count = create_stories(stories, skip)
    print(f"  Created {s_count} new stories")

    # 5. Create incidents
    hotfix_count = sum(1 for r in releases if r["is_hotfix"])
    print(f"\n[Incidents] Creating incidents for {hotfix_count} hotfix releases…")
    i_count = create_incidents(releases, severity_options, skip)
    print(f"  Created {i_count} new incidents")

    print("\n" + "=" * 60)
    print(f"Done.  Stories: {s_count}   Incidents: {i_count}")
    print("=" * 60)


if __name__ == "__main__":
    run()
