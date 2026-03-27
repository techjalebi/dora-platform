"""
github_sim.py — Populates techjalebi/dora-demo-app with 6 months of
backdated commits, PRs, merges, and releases simulating DORA activity.

Run from repo root:
    python3 -m simulation.github_sim
"""

import os
import random
import subprocess
import tempfile
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from github import Auth, Github, GithubException
from dateutil.relativedelta import relativedelta

from simulation.config import (
    GITHUB_TOKEN, GITHUB_DEMO_REPO,
    SIM_START_DATE, SIM_END_DATE,
    SIM_FAILURE_RATE, DEPLOYS_PER_WEEK,
    COMMITS_PER_BRANCH_MIN, COMMITS_PER_BRANCH_MAX,
)

# ── Fake application content ──────────────────────────────────────────────────

FEATURES = [
    ("user-auth",        "feat: add user authentication module"),
    ("payment-gateway",  "feat: integrate payment gateway"),
    ("email-service",    "feat: add transactional email service"),
    ("search-indexing",  "feat: implement search indexing"),
    ("api-rate-limiting","feat: add API rate limiting"),
    ("cache-layer",      "feat: introduce Redis cache layer"),
    ("audit-logging",    "feat: add audit logging"),
    ("dashboard-api",    "feat: expose dashboard metrics API"),
    ("webhook-support",  "feat: implement outbound webhooks"),
    ("2fa-support",      "feat: add two-factor authentication"),
    ("bulk-import",      "feat: support bulk data import"),
    ("pdf-export",       "feat: add PDF report export"),
    ("notification-hub", "feat: centralise notification delivery"),
    ("tenant-isolation", "feat: enforce tenant data isolation"),
    ("analytics-events", "feat: emit analytics events"),
    ("dark-mode",        "feat: support dark mode preference"),
    ("api-versioning",   "feat: introduce API versioning (v2)"),
    ("perf-profiling",   "perf: add performance profiling hooks"),
    ("i18n-support",     "feat: internationalisation scaffolding"),
    ("graphql-endpoint", "feat: expose GraphQL endpoint"),
    ("session-refresh",  "fix: resolve session token refresh bug"),
    ("db-migration-v2",  "refactor: migrate schema to v2 layout"),
    ("retry-logic",      "fix: add retry logic to external calls"),
    ("config-reload",    "feat: support hot config reload"),
]

COMMIT_MESSAGES = [
    "wip: initial scaffold",
    "add unit tests",
    "fix edge case in handler",
    "refactor: extract helper function",
    "update README for module",
    "add input validation",
    "code review fixes",
    "add integration test",
    "bump dependency versions",
    "fix lint warnings",
]

FAKE_FILES = [
    ("src/app.py",          "# Main application entry point\napp = None\n"),
    ("src/utils.py",        "# Utility functions\ndef noop(): pass\n"),
    ("src/config.py",       "# App configuration\nDEBUG = False\n"),
    ("tests/test_app.py",   "# Tests\ndef test_placeholder(): assert True\n"),
    ("README.md",           "# dora-demo-app\n\nSimulated application for DORA metrics demo.\n"),
    (".gitignore",          "__pycache__/\n*.pyc\n.env\n"),
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def rand_dt(start: datetime, end: datetime) -> datetime:
    delta = int((end - start).total_seconds())
    return start + timedelta(seconds=random.randint(0, delta))


def iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S +0000")


def git(cmd: list[str], cwd: str, env: dict | None = None) -> str:
    full_env = {**os.environ, **(env or {})}
    result = subprocess.run(cmd, cwd=cwd, env=full_env,
                            capture_output=True, text=True, check=True)
    return result.stdout.strip()


def bump_version(version: str, is_hotfix: bool) -> str:
    major, minor, patch = map(int, version.lstrip("v").split("."))
    if is_hotfix:
        patch += 1
    else:
        minor += 1
        patch = 0
    return f"v{major}.{minor}.{patch}"


# ── Main simulation ───────────────────────────────────────────────────────────

def run():
    random.seed(42)

    g = Github(auth=Auth.Token(GITHUB_TOKEN))
    repo = g.get_repo(GITHUB_DEMO_REPO)

    tmpdir = tempfile.mkdtemp(prefix="dora-sim-")
    print(f"Working in {tmpdir}")

    try:
        # Clone
        clone_url = f"https://{GITHUB_TOKEN}@github.com/{GITHUB_DEMO_REPO}.git"
        subprocess.run(["git", "clone", clone_url, tmpdir],
                       capture_output=True, check=True)

        git(["git", "config", "user.email", "sim@dora-platform.dev"], tmpdir)
        git(["git", "config", "user.name",  "DORA Simulator"], tmpdir)

        # Seed initial files on main
        sim_start = datetime(SIM_START_DATE.year, SIM_START_DATE.month,
                             SIM_START_DATE.day, 9, 0, tzinfo=timezone.utc)
        sim_end   = datetime(SIM_END_DATE.year,   SIM_END_DATE.month,
                             SIM_END_DATE.day,   18, 0, tzinfo=timezone.utc)

        for rel_path, content in FAKE_FILES:
            full = Path(tmpdir) / rel_path
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_text(content)

        git(["git", "add", "-A"], tmpdir)
        ts = iso(sim_start - timedelta(days=1))
        git(["git", "commit", "-m", "chore: initial project scaffold"],
            tmpdir, {"GIT_AUTHOR_DATE": ts, "GIT_COMMITTER_DATE": ts})
        git(["git", "push", "origin", "main"], tmpdir)
        print("Seeded initial files on main")

        # Build a timeline: one release every ~3-4 days
        total_days   = (sim_end - sim_start).days
        deploy_interval = 7 // DEPLOYS_PER_WEEK          # days between deploys
        num_releases = total_days // deploy_interval

        features_pool = FEATURES * 3                      # enough for 6 months
        random.shuffle(features_pool)
        feature_iter  = iter(features_pool)

        version  = "v0.0.0"
        prs_created = []

        for i in range(num_releases):
            release_start = sim_start + timedelta(days=i * deploy_interval)
            release_end   = release_start + timedelta(days=deploy_interval - 1)
            if release_end > sim_end:
                break

            is_hotfix = random.random() < SIM_FAILURE_RATE
            version   = bump_version(version, is_hotfix)
            tag_name  = f"{version}-hotfix" if is_hotfix else version

            # 1–3 feature branches per release
            branches_in_release = random.randint(1, 3)
            branch_names = []

            for _ in range(branches_in_release):
                try:
                    branch_slug, pr_title = next(feature_iter)
                except StopIteration:
                    random.shuffle(features_pool)
                    feature_iter = iter(features_pool)
                    branch_slug, pr_title = next(feature_iter)

                branch_name = f"feature/{branch_slug}-{i}"
                branch_names.append((branch_name, pr_title))

                # Create branch from main
                main_sha = repo.get_branch("main").commit.sha
                try:
                    repo.create_git_ref(f"refs/heads/{branch_name}", main_sha)
                except GithubException:
                    pass  # already exists

                git(["git", "fetch", "origin"], tmpdir)
                git(["git", "checkout", "-B", branch_name,
                     f"origin/{branch_name}"], tmpdir)

                # Backdated commits on the branch
                num_commits = random.randint(COMMITS_PER_BRANCH_MIN,
                                             COMMITS_PER_BRANCH_MAX)
                for j in range(num_commits):
                    commit_dt = rand_dt(release_start,
                                        release_end - timedelta(hours=2))
                    ts = iso(commit_dt)

                    # Mutate a file so there's something to commit
                    target = Path(tmpdir) / "src" / "app.py"
                    target.write_text(
                        f"# {branch_slug} — commit {j+1}\n"
                        f"# updated: {commit_dt.isoformat()}\napp = None\n"
                    )
                    git(["git", "add", "-A"], tmpdir)

                    msg = pr_title if j == 0 else random.choice(COMMIT_MESSAGES)
                    git(["git", "commit", "-m", msg],
                        tmpdir, {"GIT_AUTHOR_DATE": ts, "GIT_COMMITTER_DATE": ts})

                git(["git", "push", "-u", "origin", branch_name, "--force"], tmpdir)
                print(f"  Pushed branch {branch_name} ({num_commits} commits)")

            # Merge PRs
            for branch_name, pr_title in branch_names:
                merge_dt  = release_end - timedelta(hours=random.randint(1, 6))
                try:
                    pr = repo.create_pull(
                        title=pr_title,
                        body=f"Automated PR for `{branch_name}`",
                        head=branch_name,
                        base="main",
                    )
                    pr.merge(merge_method="squash",
                             commit_title=f"{pr_title} (#{pr.number})")
                    print(f"  Merged PR #{pr.number}: {pr_title}")
                    prs_created.append(pr.number)
                except GithubException as e:
                    print(f"  PR skipped ({branch_name}): {e.data.get('message', e)}")

            # Pull latest main before tagging
            git(["git", "checkout", "main"], tmpdir)
            git(["git", "pull", "origin", "main"], tmpdir)

            # Create release tag
            tag_dt    = release_end + timedelta(hours=1)
            tag_sha   = repo.get_branch("main").commit.sha
            tag_msg   = (f"Hotfix release {tag_name}" if is_hotfix
                         else f"Release {tag_name}")

            repo.create_git_tag(
                tag=tag_name,
                message=tag_msg,
                object=tag_sha,
                type="commit",
            )
            repo.create_git_ref(f"refs/tags/{tag_name}", tag_sha)
            repo.create_git_release(
                tag=tag_name,
                name=tag_name,
                message=tag_msg,
                prerelease=is_hotfix,
            )
            flag = " ⚠️  FAILURE" if is_hotfix else ""
            print(f"Release {tag_name} @ {tag_dt.date()}{flag}")

        print(f"\nDone. {num_releases} releases, {len(prs_created)} PRs.")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    run()
