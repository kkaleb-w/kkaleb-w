#!/usr/bin/env python3
"""Renders the profile panel.

    python3 tools/build.py

Reads data/build.json (written by tools/collect.py) and writes assets/panel.svg.
OLED: pure black paper, a grey-only ink ramp, no ornament. All type is Satoshi,
outlined to paths at render time (see tools/satoshi.py). Nothing here is
hard-coded data.
"""

import hashlib
import json
import re
from pathlib import Path

from satoshi import shape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
OUT.mkdir(exist_ok=True)
D = json.loads((ROOT / "data" / "build.json").read_text())

# One paper, one ink ramp, one highlight. Nothing here has a hue; emphasis is a
# step on the ramp, never a colour.
C = dict(
    paper="#000000",
    ink="#b5b5b5",
    sub="#6b6b6b",
    hi="#ffffff",
    rule="#161616",
    shade="#101010",
    empty="#0a0a0a",
    s1="#2e2e2e",
    s2="#4a4a4a",
    s3="#6b6b6b",
    s4="#8f8f8f",
    s5="#cfcfcf",
    s6="#ffffff",
)

# Type scale, px. Every string is Satoshi.
T_NAME, T_META, T_LABEL, T_VALUE = 52, 10.5, 10, 22
T_NOTE, T_SECTION, T_HEAD, T_BODY, T_NUM = 9.5, 10.5, 44, 11.5, 10


def svg(w, h, body, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" aria-label="{label}">\n'
            f'<rect width="{w}" height="{h}" fill="{C["paper"]}"/>\n{body}\n</svg>\n')


def text(x, y, s, size, fill, weight="normal", anchor="start", ls=0.0, opacity=1):
    """Satoshi, outlined. No <text> element reaches the SVG, so the panel renders
    identically everywhere and no font file ships with the repo."""
    d, w = shape(s, size, weight=weight, tracking=ls)
    if anchor == "middle":
        x -= w / 2
    elif anchor == "end":
        x -= w
    return (f'<g transform="translate({x:.2f} {y:.2f})" fill="{fill}" '
            f'opacity="{opacity}">{d}</g>')


def fmt(n):
    return f"{n:,}"


LANG_OF = {
    ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript",
    ".py": "Python", ".css": "CSS", ".scss": "SCSS", ".html": "HTML",
    ".sh": "Shell", ".go": "Go", ".rs": "Rust", ".java": "Java", ".sql": "SQL",
    ".c": "C", ".h": "C", ".cpp": "C++", ".rb": "Ruby", ".php": "PHP",
}


def languages():
    """Share of code lines per language — measured from source, not repo bytes."""
    counts = json.loads((ROOT / "data" / "loc_by_ext.json").read_text())
    agg = {}
    for ext, n in counts.items():
        lang = LANG_OF.get(ext)
        if lang:
            agg[lang] = agg.get(lang, 0) + n
    total = max(1, sum(agg.values()))
    return sorted(((k, v / total) for k, v in agg.items()), key=lambda kv: -kv[1])[:6]


# ─────────────────────────────── the panel ──────────────────────────────────
def panel():
    W, H = 1000, 812
    P, R = 48, 952
    b = []

    def rule(y):
        b.append(f'<rect x="{P}" y="{y}" width="{R - P}" height="1" fill="{C["rule"]}"/>')

    # ── masthead: the name is the only thing at full white ────────────────────
    b.append(text(P, 92, "Kaleb Wright", T_NAME, C["hi"], weight="bold", ls=-1.2))
    b.append(text(P, 122, "est. 2020  ·  github.com/kkaleb-w", T_META, C["sub"]))
    rule(150)

    # ── eight numbers, two rows ───────────────────────────────────────────────
    stats = [
        ("contributions", fmt(D["contributions_year"]), "this year"),
        ("commits", fmt(D["commits"]), "last 12 mo"),
        ("repositories", str(D["repos_total"]), f'{D["private"]} private'),
        ("stars", str(D["stars"]), "earned"),
        ("longest streak", f'{D["longest_streak"]} d', "in a row"),
        ("storage", f'{D["storage_kb"] / 1024:.0f} MB', "on github"),
        ("active days", str(sum(1 for _, n in D["calendar"] if n > 0)), "of 366"),
        ("languages", str(len(languages())), "in use"),
    ]
    col_w = (R - P) / 4
    for i, (label, val, note) in enumerate(stats):
        r, col = divmod(i, 4)
        x = P + col * col_w
        y = 194 + r * 70
        b.append(text(x, y, label, T_LABEL, C["sub"], ls=0.8))
        b.append(text(x, y + 28, val, T_VALUE, C["ink"], weight="bold"))
        b.append(text(x, y + 45, note, T_NOTE, C["sub"]))
    rule(316)

    # ── lines of code, and when ───────────────────────────────────────────────
    b.append(text(P, 352, "lines of code", T_SECTION, C["sub"], ls=1.4))
    b.append(text(P, 400, fmt(D["loc"]), T_HEAD, C["hi"], weight="bold", ls=-0.8))
    b.append(text(
        P, 420,
        f'{D["loc_files"]} source files across '
        f'{len([k for k, v in D["loc_per_repo"].items() if v])} repositories',
        T_NOTE, C["sub"]))

    hours = D["hours"]
    buckets = [("morning", sum(hours[5:12])), ("daytime", sum(hours[12:17])),
               ("evening", sum(hours[17:22])),
               ("night", sum(hours[22:24]) + sum(hours[0:5]))]
    total = max(1, sum(v for _, v in buckets))
    bx = 520
    b.append(text(bx, 352, "when i commit", T_SECTION, C["sub"], ls=1.4))
    bar_x, bar_w = bx + 74, R - bx - 74 - 38
    fills = [C["s5"], C["s4"], C["s3"], C["s6"]]
    for i, (name, v) in enumerate(buckets):
        y = 380 + i * 24
        b.append(text(bx, y + 3, name, T_BODY, C["ink"]))
        b.append(f'<rect x="{bar_x}" y="{y - 6}" width="{bar_w}" height="8" rx="4" '
                 f'fill="{C["shade"]}"/>')
        b.append(f'<rect x="{bar_x}" y="{y - 6}" width="{max(4, bar_w * v / total):.1f}" '
                 f'height="8" rx="4" fill="{fills[i]}"/>')
        b.append(text(R, y + 3, f"{v / total * 100:.0f}%", T_NUM, C["sub"], anchor="end"))
    rule(486)

    # ── the year ──────────────────────────────────────────────────────────────
    import datetime as dt

    b.append(text(P, 524, "the year in commits", T_SECTION, C["sub"], ls=1.4))
    dates = {d: n for d, n in D["calendar"]}
    first = dt.date.fromisoformat(min(dates))
    start = first - dt.timedelta(days=(first.weekday() + 1) % 7)
    scale = [C["empty"], C["s1"], C["s2"], C["s3"], C["s4"], C["s6"]]

    def bucket(n):
        return 0 if n == 0 else 1 if n <= 1 else 2 if n <= 3 else 3 if n <= 6 else 4 if n <= 12 else 5

    cols_n = (dt.date.fromisoformat(max(dates)) - start).days // 7 + 1
    gap, top = 3.2, 546
    cell = ((R - P) - (cols_n - 1) * gap) / cols_n
    for date, n in dates.items():
        d0 = dt.date.fromisoformat(date)
        x = P + ((d0 - start).days // 7) * (cell + gap)
        y = top + ((d0.weekday() + 1) % 7) * (cell + gap)
        b.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell:.1f}" height="{cell:.1f}" '
                 f'rx="1.8" fill="{scale[bucket(n)]}"/>')

    sw, sgap = 10, 4
    band = 24 + len(scale) * sw + (len(scale) - 1) * sgap + 4
    lx = R - (band + 22)
    b.append(text(lx, 524, "less", T_NUM, C["sub"]))
    for i, col in enumerate(scale):
        b.append(f'<rect x="{lx + 24 + i * (sw + sgap)}" y="{516}" width="{sw}" height="{sw}" '
                 f'rx="1.8" fill="{col}"/>')
    b.append(text(lx + band + 4, 524, "more", T_NUM, C["sub"]))
    rule(676)

    # ── languages ─────────────────────────────────────────────────────────────
    b.append(text(P, 714, "where the code is", T_SECTION, C["sub"], ls=1.4))
    steps = [C["s6"], C["s5"], C["s4"], C["s3"], C["s2"], C["s1"]]
    for i, (name, share) in enumerate(languages()):
        col, row = divmod(i, 3)
        x = P + col * 302
        y = 750 + row * 30
        b.append(text(x, y, name, T_BODY, C["ink"]))
        b.append(f'<rect x="{x + 88}" y="{y - 6}" width="150" height="6" rx="3" '
                 f'fill="{C["shade"]}"/>')
        b.append(f'<rect x="{x + 88}" y="{y - 6}" width="{max(4, 150 * share):.1f}" '
                 f'height="6" rx="3" fill="{steps[i % len(steps)]}"/>')
        b.append(text(x + 258, y, f"{share * 100:.1f}%", T_NUM, C["sub"], anchor="end"))

    return svg(W, H, "\n".join(b), "Kaleb Wright — GitHub data, contributions, languages")


def stamp():
    """Put a content hash in the README image URL — camo caches by URL."""
    h = hashlib.sha1()
    for f in sorted(OUT.glob("*.svg")):
        h.update(f.read_bytes())
    tag = h.hexdigest()[:8]
    readme = ROOT / "README.md"
    txt = readme.read_text()
    new, n = re.subn(r"\?v=[0-9a-f]+", f"?v={tag}", txt)
    if n:
        readme.write_text(new)
    return tag, n


if __name__ == "__main__":
    (OUT / "panel.svg").write_text(panel())
    print("rendered panel.svg")
    tag, n = stamp()
    print(f"cache tag {tag} on {n} refs")
    print("loc", D["loc"], "files", D["loc_files"], "langs", languages()[:3])
