#!/usr/bin/env python3
"""Regenerates the profile assets.

    python3 tools/generate_assets.py

Every number comes from the GitHub API — nothing here is hand-written.
Needs an authenticated `gh` CLI.
"""

import json
import subprocess
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets"
OUT.mkdir(parents=True, exist_ok=True)

MONO = "'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace"
NAME = "KALEB"

INK = {"dark": "#39d353", "light": "#1a7f37"}
DIM = {"dark": "#4a9e6a", "light": "#5f9d78"}

FONT = {
    "K": ["#   #", "#  # ", "###  ", "#  # ", "#   #"],
    "A": [" ### ", "#   #", "#####", "#   #", "#   #"],
    "L": ["#    ", "#    ", "#    ", "#    ", "#####"],
    "E": ["#####", "#    ", "#### ", "#    ", "#####"],
    "B": ["#### ", "#   #", "#### ", "#   #", "#### "],
    " ": ["     "] * 5,
}

GAP = 3  # blank columns between glyphs


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def api():
    raw = subprocess.run(
        ["gh", "api", "graphql", "-f",
         "query={ viewer { login createdAt contributionsCollection { "
         "totalCommitContributions contributionCalendar { totalContributions weeks { "
         "contributionDays { date contributionCount } } } } "
         "repositories(ownerAffiliations:OWNER, isFork:false, first:100) "
         "{ nodes { stargazerCount } } } }"],
        capture_output=True, text=True, check=True).stdout
    return json.loads(raw)["data"]["viewer"]


def stats(v):
    cal = v["contributionsCollection"]["contributionCalendar"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    return [
        ("commits", v["contributionsCollection"]["totalCommitContributions"]),
        ("active days", sum(1 for d in days if d["contributionCount"] > 0)),
        ("repositories", len(v["repositories"]["nodes"])),
        ("stars earned", sum(n["stargazerCount"] for n in v["repositories"]["nodes"])),
        ("on github since", v["createdAt"][:4]),
    ]


def svg(width, height, body, dark, label, extra_defs=""):
    glow = (
        '<filter id="g" x="-15%" y="-30%" width="130%" height="160%">'
        '<feGaussianBlur stdDeviation="2.2" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
    ) if dark else ""
    filt = ' filter="url(#g)"' if dark else ""
    body = "\n".join(body) if isinstance(body, list) else body
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{esc(label)}">\n'
        f"<style>text{{font-family:{MONO};white-space:pre}}</style>\n"
        f"<defs>{glow}{extra_defs}</defs>\n"
        f"<g{filt}>\n{body}\n</g>\n</svg>\n"
    )


def banner_art(word=NAME):
    rows = [[] for _ in range(5)]
    for i, ch in enumerate(word):
        for r in range(5):
            rows[r].append(FONT[ch][r] + (" " * GAP if i < len(word) - 1 else ""))
    return ["".join(r) for r in rows]


def build_banner(dark: bool) -> str:
    key = "dark" if dark else "light"
    art = banner_art()

    fs, lh, padx, pady = 15.0, 1.4, 10, 8
    cw = fs * 0.655
    w = int(len(art[0]) * cw + padx * 2)
    h = int(len(art) * fs * lh + pady * 2)

    body = [
        f'<text x="{padx}" y="{pady + (i + 0.85) * fs * lh:.1f}" font-size="{fs}" '
        f'fill="{INK[key]}" font-weight="bold">{esc(line)}</text>'
        for i, line in enumerate(art)
    ]

    extra = ""
    if dark:
        extra = (f'<radialGradient id="bg" cx="50%" cy="50%" r="62%">'
                 f'<stop offset="0%" stop-color="{INK[key]}" stop-opacity="0.13"/>'
                 f'<stop offset="100%" stop-color="{INK[key]}" stop-opacity="0"/></radialGradient>')
        body = [f'<rect width="{w}" height="{h}" fill="url(#bg)"/>'] + body

    return svg(w, h, body, dark, NAME.title(), extra)


def build_ledger(v, dark: bool) -> str:
    key = "dark" if dark else "light"
    rows = stats(v)

    lw = max(len(k) for k, _ in rows)
    vw = max(len(str(n)) for _, n in rows)
    width = lw + 1 + 20 + 1 + vw          # chars per line

    fs, lh, padx, pady = 13.0, 1.62, 10, 9
    cw = fs * 0.655
    w = int(width * cw + padx * 2)
    h = int(len(rows) * fs * lh + pady * 2)

    body = []
    for i, (label, n) in enumerate(rows):
        y = pady + (i + 0.8) * fs * lh
        dots = "." * (width - lw - vw - 2)
        body.append(
            f'<text x="{padx}" y="{y:.1f}" font-size="{fs}" fill="{DIM[key]}">'
            f"{esc(label.ljust(lw))} {dots}</text>"
            f'<text x="{padx + (width - vw) * cw:.1f}" y="{y:.1f}" font-size="{fs}" '
            f'fill="{INK[key]}" font-weight="bold">{n}</text>'
        )
    return svg(w, h, body, dark, " · ".join(f"{k} {n}" for k, n in rows))


def build_commits(v, dark: bool) -> str:
    cal = v["contributionsCollection"]["contributionCalendar"]
    weeks, total = cal["weeks"], cal["totalContributions"]

    scale = (["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"] if dark
             else ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"])
    label = "#8b949e" if dark else "#57606a"

    def bucket(n):
        return 0 if n == 0 else 1 if n <= 2 else 2 if n <= 5 else 3 if n <= 9 else 4

    cell, gap, top = 11, 3.5, 16
    w = int(len(weeks) * (cell + gap) + 2)
    legend_y = top + 7 * (cell + gap) + 9
    h = int(legend_y + 14)

    cells, months, last = [], [], None
    names = {"01": "jan", "02": "feb", "03": "mar", "04": "apr", "05": "may", "06": "jun",
             "07": "jul", "08": "aug", "09": "sep", "10": "oct", "11": "nov", "12": "dec"}
    for wi, wk in enumerate(weeks):
        for di, d in enumerate(wk["contributionDays"]):
            x, y = 1 + wi * (cell + gap), top + di * (cell + gap)
            cells.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" '
                         f'rx="2" fill="{scale[bucket(d["contributionCount"])]}"/>')
        m = wk["contributionDays"][0]["date"][5:7]
        if m != last and wi < len(weeks) - 2:
            months.append(f'<text x="{1 + wi * (cell + gap):.1f}" y="11" fill="{label}" '
                          f'font-size="9" font-family="{MONO}">{names[m]}</text>')
            last = m

    lx = w - 5 * (cell * 0.62 + 4) - 34
    legend = [f'<text x="{lx - 26:.1f}" y="{legend_y + 9:.1f}" fill="{label}" font-size="9" '
              f'font-family="{MONO}">less</text>']
    for i, c in enumerate(scale):
        legend.append(f'<rect x="{lx + i * (cell * 0.62 + 4):.1f}" y="{legend_y + 1:.1f}" '
                      f'width="{cell * 0.62:.1f}" height="{cell * 0.62:.1f}" rx="1.5" fill="{c}"/>')
    legend.append(f'<text x="{lx + 5 * (cell * 0.62 + 4) + 4:.1f}" y="{legend_y + 9:.1f}" '
                  f'fill="{label}" font-size="9" font-family="{MONO}">more</text>')

    cap = (f'<text x="1" y="{legend_y + 9:.1f}" fill="{label}" font-size="9.5" '
           f'font-family="{MONO}">{total} contributions · last 12 months</text>')

    return svg(w, h, months + cells + [cap] + legend, False,
               f"{total} contributions in the last 12 months")


if __name__ == "__main__":
    v = api()
    for dark in (True, False):
        s = "dark" if dark else "light"
        (OUT / f"banner-{s}.svg").write_text(build_banner(dark))
        (OUT / f"ledger-{s}.svg").write_text(build_ledger(v, dark))
        (OUT / f"commits-{s}.svg").write_text(build_commits(v, dark))
        print(f"wrote banner-{s} ledger-{s} commits-{s}.svg")
    print("stats:", dict(stats(v)))
