#!/usr/bin/env python3
"""Regenerates the profile assets.

    python3 tools/generate_assets.py

Writes assets/banner-{dark,light}.svg, assets/status-{dark,light}.svg and
assets/commits-{dark,light}.svg. Needs an authenticated `gh` CLI for the
contribution grid; the banner and status block are pure text.
"""

import json
import subprocess
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets"
OUT.mkdir(parents=True, exist_ok=True)

MONO = "'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace"

NAME = "KALEB"
ROLE = "engineer / ai research"

# ── the words in the status block. keep the right column under ~26 chars ─────
STATUS = [
    ("now", "a model that gets bored"),
    ("learning", "systems design, brevity"),
    ("open to", "research collaborations"),
    ("elsewhere", "film, long walks, unread PDFs"),
]

# ── 5-row ASCII font, 5 cells per glyph ─────────────────────────────────────
FONT = {
    "K": ["#   #", "#  # ", "###  ", "#  # ", "#   #"],
    "A": [" ### ", "#   #", "#####", "#   #", "#   #"],
    "L": ["#    ", "#    ", "#    ", "#    ", "#####"],
    "E": ["#####", "#    ", "#### ", "#    ", "#####"],
    "B": ["#### ", "#   #", "#### ", "#   #", "#### "],
    " ": ["     "] * 5,
}

GAP = 2          # blank columns between glyphs
BOX = 43         # inner width shared by every box, so the frames line up

INK = {"dark": "#39d353", "light": "#1a7f37"}
DIM = {"dark": "#3f9c66", "light": "#4f9a6d"}
FAINT = {"dark": "#1f5236", "light": "#a9d3b7"}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def banner_art(word=NAME):
    rows = [[] for _ in range(5)]
    for i, ch in enumerate(word):
        for r in range(5):
            rows[r].append(FONT[ch][r] + (" " * GAP if i < len(word) - 1 else ""))
    return ["".join(r) for r in rows]


def boxed(lines, width=BOX):
    out = ["+" + "-" * width + "+"]
    out += ["|" + l.ljust(width)[:width] + "|" for l in lines]
    out += ["+" + "-" * width + "+"]
    return out


def svg(width, height, body, dark, label, extra_defs=""):
    glow = (
        '<filter id="g" x="-15%" y="-30%" width="130%" height="160%">'
        '<feGaussianBlur stdDeviation="2.2" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
    ) if dark else ""
    body = "\n".join(body) if isinstance(body, list) else body
    filt_attr = ' filter="url(#g)"' if dark else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{esc(label)}">\n'
        f"<style>text{{font-family:{MONO};white-space:pre;letter-spacing:0.55px}}</style>\n"
        f"<defs>{glow}{extra_defs}</defs>\n"
        f"<g{filt_attr}>\n{body}\n</g>\n</svg>\n"
    )


def text_lines(lines, x, y0, fs=13.0, lh=1.5, colors=None):
    """Render ASCII lines as one <text> each, colour picked per line."""
    out = []
    for i, line in enumerate(lines):
        fill, weight = colors(line) if colors else (INK["dark"], "normal")
        y = y0 + (i + 0.8) * fs * lh
        out.append(
            f'<text x="{x}" y="{y:.1f}" font-size="{fs}" fill="{fill}" '
            f'font-weight="{weight}">{esc(line)}</text>'
        )
    return out


def build_banner(dark: bool) -> str:
    key = "dark" if dark else "light"
    art = banner_art()
    pad = max(1, (BOX - len(art[0])) // 2)

    top = boxed([""] + [" " * pad + a for a in art] + [""])
    role = ["+" + "-" * BOX + "+",
            "|" + ("  " + ROLE).ljust(BOX) + "|",
            "+" + "-" * BOX + "+"]
    lines = top + role

    fs, lh, padx, pady = 13.0, 1.5, 16, 14
    cw = fs * 0.6
    w = int((BOX + 2) * cw + padx * 2)
    h = int(len(lines) * fs * lh + pady * 2)

    def colors(line):
        if "#" in line:
            return INK[key], "bold"
        if "engineer" in line:
            return DIM[key], "normal"
        return FAINT[key], "normal"

    body = text_lines(lines, padx, pady, fs, lh, colors)

    # caret blinking just past the role text
    i_role = len(top)
    caret_x = padx + (3 + len(ROLE)) * cw
    caret_y = pady + (i_role + 0.8) * fs * lh - fs * 0.88
    body.append(
        f'<rect x="{caret_x:.1f}" y="{caret_y:.1f}" width="{cw * 1.05:.1f}" '
        f'height="{fs * 1.08:.1f}" fill="{INK[key]}">'
        '<animate attributeName="opacity" values="1;1;0;0;1" dur="1.6s" repeatCount="indefinite"/></rect>'
    )

    return svg(w, h, "\n".join(body), dark, f"{NAME.title()} — {ROLE}")


def build_status(dark: bool) -> str:
    key = "dark" if dark else "light"
    lw = max(len(k) for k, _ in STATUS) + 2
    rows = ["  " + k.ljust(lw) + v for k, v in STATUS]
    lines = boxed(rows)

    fs, lh, padx, pady = 13.0, 1.5, 16, 14
    cw = fs * 0.6
    w = int((BOX + 2) * cw + padx * 2)
    h = int(len(lines) * fs * lh + pady * 2)

    def colors(line):
        if line.startswith("+"):
            return FAINT[key], "normal"
        return INK[key], "normal"

    body = text_lines(lines, padx, pady, fs, lh, colors)
    return svg(w, h, "\n".join(body), dark, "currently")


def build_commits(dark: bool) -> str:
    raw = subprocess.run(
        ["gh", "api", "graphql", "-f",
         "query={ viewer { contributionsCollection { contributionCalendar { "
         "totalContributions weeks { contributionDays { date contributionCount } } } } } }"],
        capture_output=True, text=True, check=True).stdout
    cal = json.loads(raw)["data"]["viewer"]["contributionsCollection"]["contributionCalendar"]
    weeks, total = cal["weeks"], cal["totalContributions"]

    key = "dark" if dark else "light"
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
        days = wk["contributionDays"]
        for di, d in enumerate(days):
            x, y = 1 + wi * (cell + gap), top + di * (cell + gap)
            cells.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" '
                         f'rx="2" fill="{scale[bucket(d["contributionCount"])]}"/>')
        m = days[0]["date"][5:7]
        if m != last and wi < len(weeks) - 2:
            months.append(f'<text x="{1 + wi * (cell + gap):.1f}" y="11" fill="{label}" '
                          f'font-size="9" font-family="{MONO}">{names[m]}</text>')
            last = m

    # legend: less [][][][][] more, right aligned
    lx = w - 5 * (cell * 0.62 + 4) - 34
    legend = [f'<text x="{lx - 26:.1f}" y="{legend_y + 9:.1f}" fill="{label}" font-size="9" '
              f'font-family="{MONO}">less</text>']
    for i, c in enumerate(scale):
        legend.append(f'<rect x="{lx + i * (cell * 0.62 + 4):.1f}" y="{legend_y + 1:.1f}" '
                      f'width="{cell * 0.62:.1f}" height="{cell * 0.62:.1f}" rx="1.5" fill="{c}"/>')
    legend.append(f'<text x="{lx + 5 * (cell * 0.62 + 4) + 4:.1f}" y="{legend_y + 9:.1f}" '
                  f'fill="{label}" font-size="9" font-family="{MONO}">more</text>')

    cap = (f'<text x="1" y="{legend_y + 9:.1f}" fill="{label}" font-size="9.5" '
           f'font-family="{MONO}" letter-spacing="0.6">{total} contributions · last 12 months</text>')

    body = "\n".join(months + cells + [cap] + legend)
    return svg(w, h, body, False, f"{total} contributions in the last 12 months")


if __name__ == "__main__":
    for dark in (True, False):
        s = "dark" if dark else "light"
        (OUT / f"banner-{s}.svg").write_text(build_banner(dark))
        (OUT / f"status-{s}.svg").write_text(build_status(dark))
        (OUT / f"commits-{s}.svg").write_text(build_commits(dark))
        print(f"wrote banner-{s}.svg status-{s}.svg commits-{s}.svg")
