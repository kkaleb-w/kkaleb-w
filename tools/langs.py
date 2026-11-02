#!/usr/bin/env python3
"""Counts code lines by file extension so the language card reflects code
actually written, not bytes of whatever ended up in the repo."""
import json, os, shutil, subprocess, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
repos = json.loads(subprocess.run(
    ["gh", "api", "user/repos?per_page=100&affiliation=owner"],
    capture_output=True, text=True, check=True).stdout)

CODE_EXT = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".html", ".css",
            ".scss", ".sass", ".go", ".rs", ".java", ".kt", ".c", ".h", ".cpp",
            ".hpp", ".cs", ".rb", ".php", ".swift", ".sh", ".sql", ".lua",
            ".ex", ".exs", ".zig", ".vue", ".svelte"}
SKIP_DIR = {".git", "node_modules", "dist", "build", ".next", "venv", ".venv",
            "__pycache__", "vendor", "target", ".idea", ".vscode", "corpus",
            "data", "datasets", "models", "checkpoints", "cache", "coverage",
            "public", "static", "assets", "out", ".turbo", ".cache"}

env = {**os.environ, "GIT_TERMINAL_PROMPT": "0",
       "GIT_SSH_COMMAND": "ssh -o BatchMode=yes -o StrictHostKeyChecking=no"}
work = Path(tempfile.mkdtemp(prefix="lg-"))
counts = {}

for r in repos:
    if r["fork"]:
        continue
    d = work / r["name"]
    try:
        subprocess.run(["git", "clone", "--depth", "1", "-q", r["ssh_url"], str(d)],
                       check=True, timeout=300, capture_output=True, env=env)
    except Exception:
        continue
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
            n = txt.count("\n") + (1 if txt and not txt.endswith("\n") else 0)
            counts[p.suffix.lower()] = counts.get(p.suffix.lower(), 0) + n

shutil.rmtree(work, ignore_errors=True)
(ROOT / "data" / "loc_by_ext.json").write_text(json.dumps(counts, indent=1, sort_keys=True))
print(json.dumps(dict(sorted(counts.items(), key=lambda kv: -kv[1])), indent=1))
