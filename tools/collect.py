#!/usr/bin/env python3
"""Collects every number the profile shows. Writes data/build.json."""
import json, subprocess, shutil, tempfile, os
from datetime import datetime
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data"
OUT.mkdir(exist_ok=True)
WORK = Path(tempfile.mkdtemp(prefix="gh-"))

def gh(*a):
    return subprocess.run(["gh", *a], capture_output=True, text=True, check=True).stdout

user = json.loads(gh("api", "user"))
repos = json.loads(gh("api", "user/repos?per_page=100&affiliation=owner"))
owned = [r for r in repos if not r["fork"]]

CODE_EXT = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".html", ".css",
            ".scss", ".sass", ".go", ".rs", ".java", ".kt", ".c", ".h", ".cpp",
            ".hpp", ".cs", ".rb", ".php", ".swift", ".sh", ".sql", ".lua",
            ".ex", ".exs", ".zig", ".vue", ".svelte"}
SKIP_DIR = {".git", "node_modules", "dist", "build", ".next", "venv", ".venv",
            "__pycache__", "vendor", "target", ".idea", ".vscode", "corpus",
            "data", "datasets", "models", "checkpoints", "cache", "coverage",
            "public", "static", "assets", "out", ".turbo", ".cache"}

env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_SSH_COMMAND": "ssh -o BatchMode=yes -o StrictHostKeyChecking=no"}

loc = files = 0
per_repo, failed = {}, {}
hours = [0] * 24
weekdays = [0] * 7
commit_total = 0

for r in owned:
    d = WORK / r["name"]
    # full history, blobs on demand: cheap clone that still has every commit date
    try:
        subprocess.run(["git", "clone", "--filter=blob:none", "-q", r["ssh_url"], str(d)],
                       check=True, timeout=300, capture_output=True, env=env)
    except Exception as e:
        failed[r["name"]] = str(e)[:80]
        continue

    log = subprocess.run(["git", "-C", str(d), "log", "--format=%ad", "--date=format:%H %w"],
                         capture_output=True, text=True).stdout.split("\n")
    for line in log:
        if not line.strip():
            continue
        try:
            h, w = line.split()
            hours[int(h) % 24] += 1
            weekdays[int(w) % 7] += 1
            commit_total += 1
        except Exception:
            pass

    n = 0
    for root, dirs, names in os.walk(d):
        dirs[:] = [x for x in dirs if x not in SKIP_DIR]
        for fn in names:
            p = Path(root) / fn
            if p.suffix.lower() not in CODE_EXT or p.stat().st_size > 1_000_000:
                continue
            try:
                txt = p.read_text("utf-8", errors="ignore")
            except Exception:
                continue
            n += txt.count("\n") + (1 if txt and not txt.endswith("\n") else 0)
            files += 1
    per_repo[r["name"]] = n
    loc += n

shutil.rmtree(WORK, ignore_errors=True)

q = """{ viewer { createdAt
  contributionsCollection { totalCommitContributions totalPullRequestContributions
    totalIssueContributions contributionCalendar { totalContributions
      weeks { contributionDays { date contributionCount } } } } } }"""
c = json.loads(gh("api", "graphql", "-f", f"query={q}"))["data"]["viewer"]
cal = c["contributionsCollection"]["contributionCalendar"]
days = [d for w in cal["weeks"] for d in w["contributionDays"]]
year = [d for d in days if d["date"].startswith("2026")]

streak = best = 0
for d in days:
    streak = streak + 1 if d["contributionCount"] else 0
    best = max(best, streak)

data = {
    "login": user["login"],
    "repos_public": sum(1 for r in owned if not r["private"]),
    "repos_total": len(owned),
    "private": sum(1 for r in owned if r["private"]),
    "stars": sum(r["stargazers_count"] for r in owned),
    "followers": user["followers"],
    "storage_kb": sum(r["size"] for r in owned),
    "loc": loc,
    "loc_files": files,
    "loc_per_repo": per_repo,
    "loc_failed": failed,
    "commits": c["contributionsCollection"]["totalCommitContributions"],
    "prs": c["contributionsCollection"]["totalPullRequestContributions"],
    "issues": c["contributionsCollection"]["totalIssueContributions"],
    "contributions_year": sum(d["contributionCount"] for d in year),
    "contributions_12mo": cal["totalContributions"],
    "longest_streak": best,
    "hours": hours,
    "weekdays": weekdays,
    "commit_total": commit_total,
    "since": c["createdAt"][:4],
    "calendar": [[d["date"], d["contributionCount"]] for d in days],
}
(OUT / "build.json").write_text(json.dumps(data, indent=1))
print(json.dumps({k: v for k, v in data.items() if k not in ("calendar", "loc_per_repo")}, indent=1))
print("per repo:", per_repo)
print("failed:", failed)
