#!/usr/bin/env python3
"""Regenerates the profile assets: ASCII banner + contribution grid.

Requires an authenticated `gh` CLI. Run:  python3 tools/generate_assets.py
"""

import json
import subprocess
from pathlib import Path

USER = "kkaleb-w"
OUT = Path(__file__).resolve().parent.parent / "assets"
OUT.mkdir(parents=True, exist_ok=True)

MONO = "'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace"

# ── 5-row ASCII font, 5 cells wide per glyph ────────────────────────────────
FONT = {
    "K": ["#   #", "#  # ", "###  ", "#  # ", "#   #"],
    "A": [" ### ", "#   #", "#####", "#   #", "#   #"],
    "L": ["#    ", "#    ", "#    ", "#    ", "#####"],
    "E": ["#####", "#    ", "#### ", "#    ", "#####"],
    "B": ["#### ", "#   #", "#### ", "#   #", "#### "],
    " ": ["     "] * 5,
}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def banner_art(word="KALEB"):
    rows = [[] for _ in range(5)]
    for i, ch in enumerate(word):
        for r in range(5):
            rows[r].append(FONT[ch][r] + (" " if i < len(word) - 1 else ""))
    return ["".join(r) for r in rows]


def build_banner(dark: bool) -> str:
    art = banner_art()
    width = max(len(a) for a in art) + 8
    role = "engineer / ai research"

    lines = ["", *["  " + a for a in art], ""]
    top = ["+" + "-" * width + "+"] + ["|" + l.ljust(width) + "|" for l in lines] + ["+" + "-" * width + "+"]
    mid = ["|  " + role.ljust(width - 2) + "|"]
    bottom = ["+" + "-" * width + "+"]

    fs = 13.0
    cw = fs * 0.6
    lh = fs * 1.5
    padx, pady = 16, 14
    w = int((width + 2) * cw + padx * 2)
    h = int(len(top + mid + bottom) * lh + pady * 2)

    ink = "#39d353" if dark else "#1a7f37"
    dim = "#2f8a56" if dark else "#5aa87a"
    faint = "#1d4b33" if dark else "#b7dcc4"

    def style_for(line):
        if "#" in line:
            return ink, "bold"
        if "engineer" in line:
            return dim, "normal"
        return faint, "normal"

    rows = []
    for i, line in enumerate(top + mid + bottom):
        fill, weight = style_for(line)
        y = pady + (i + 0.8) * lh
        rows.append(f'<text x="{padx}" y="{y:.1f}" fill="{fill}" font-weight="{weight}">{esc(line)}</text>')

    # caret sits just past the role text
    caret_i = len(top)
    caret_y = pady + (caret_i + 0.8) * lh - fs * 0.9
    caret_x = padx + (3 + len(role)) * cw
    rows.append(
        f'<rect x="{caret_x:.1f}" y="{caret_y:.1f}" width="{cw * 1.05:.1f}" height="{fs * 1.1:.1f}" fill="{ink}">'
        '<animate attributeName="opacity" values="1;1;0;0;1" dur="1.5s" repeatCount="indefinite"/></rect>'
    )

    filt = (
        '<filter id="g" x="-15%" y="-30%" width="130%" height="160%">'
        '<feGaussianBlur stdDeviation="2.6" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>'
        "</filter>"
    ) if dark else ""

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Kaleb — engineer, AI research">
<style>text{{font-family:{MONO};font-size:{fs}px;white-space:pre;letter-spacing:0.6px}}</style>
<defs>{filt}</defs>
<g{' filter="url(#g)"' if dark else ''}>
{chr(10).join(rows)}
</g>
</svg>
'''


def build_commits(dark: bool) -> str:
    raw = subprocess.run(
        ["gh", "api", "graphql", "-f",
         'query={ viewer { contributionsCollection { contributionCalendar { '
         'totalContributions weeks { contributionDays { date contributionCount } } } } } }'],
        capture_output=True, text=True, check=True).stdout
    cal = json.loads(raw)["data"]["viewer"]["contributionsCollection"]["contributionCalendar"]
    weeks, total = cal["weeks"], cal["totalContributions"]

    scale = (["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"] if dark
             else ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"])
    label = "#8b949e" if dark else "#57606a"

    def bucket(n):
        return 0 if n == 0 else 1 if n <= 2 else 2 if n <= 5 else 3 if n <= 9 else 4

    cell, gap, top = 11, 3.5, 15
    w = int(len(weeks) * (cell + gap) + 2)
    h = int(top + 7 * (cell + gap) + 25)

    cells, months, last = [], [], None
    names = {"01": "jan", "02": "feb", "03": "mar", "04": "apr", "05": "may", "06": "jun",
             "07": "jul", "08": "aug", "09": "sep", "10": "oct", "11": "nov", "12": "dec"}
    for wi, wk in enumerate(weeks):
        days = wk["contributionDays"]
        for di, d in enumerate(days):
            x, y = 1 + wi * (cell + gap), top + di * (cell + gap)
            cells.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" rx="2" '
                         f'fill="{scale[bucket(d["contributionCount"])]}"/>')
        m = days[0]["date"][5:7]
        if m != last and wi < len(weeks) - 2:
            months.append(f'<text x="{1 + wi * (cell + gap):.1f}" y="10" fill="{label}" font-size="9" '
                          f'font-family="{MONO}">{names[m]}</text>')
            last = m

    cap = f"{total} contributions · last 12 months"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{cap}">
{chr(10).join(months)}
{chr(10).join(cells)}
<text x="1" y="{top + 7 * (cell + gap) + 13:.1f}" fill="{label}" font-size="9.5" font-family="{MONO}" letter-spacing="0.6">{esc(cap)}</text>
</svg>
'''


if __name__ == "__main__":
    for dark in (True, False):
        s = "dark" if dark else "light"
        (OUT / f"banner-{s}.svg").write_text(build_banner(dark))
        (OUT / f"commits-{s}.svg").write_text(build_commits(dark))
        print("wrote assets/banner-%s.svg assets/commits-%s.svg" % (s, s))
