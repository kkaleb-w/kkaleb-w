#!/usr/bin/env python3
"""Renders the profile cards.

    python3 tools/build.py

Reads data/build.json (written by tools/collect.py) and writes
assets/*-{light,dark}.svg. Palette is autumn: cream paper, burnt orange,
rust, olive, mustard. Nothing here is hard-coded data.
"""

import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
OUT.mkdir(exist_ok=True)
D = json.loads((ROOT / "data" / "build.json").read_text())

SERIF = "'Iowan Old Style','Palatino Linotype',Palatino,Georgia,'Times New Roman',serif"
MONO = "'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace"

T = {
    "light": dict(paper="#FBF1DC", card="#FFF9EC", ink="#3B2A1A", sub="#7C6A50",
                  rule="#E4CFA9", orange="#C2551F", amber="#D98B2B", rust="#8C3B12",
                  olive="#6E7B3F", mustard="#E3B23C", shade="#F0DFBD"),
    "dark": dict(paper="#181008", card="#221607", ink="#F4E5C8", sub="#BBA689",
                 rule="#48381F", orange="#E4813F", amber="#EBA84C", rust="#C05F31",
                 olive="#9BA96B", mustard="#EFC65F", shade="#2C1D0E"),
}

LEAF = ("M0,-12 L2.6,-4.8 L7.2,-7 L5,-2.2 L11.4,0 L5,2.4 L7.2,7 L2.6,4.8 "
        "L0,12 L-2.6,4.8 L-7.2,7 L-5,2.4 L-11.4,0 L-5,-2.2 L-7.2,-7 L-2.6,-4.8 Z")


def leaf(x, y, s, rot, fill, op=1.0):
    return (f'<g transform="translate({x},{y}) rotate({rot}) scale({s})" opacity="{op}">'
            f'<path d="{LEAF}" fill="{fill}"/></g>')


def halftone(uid, c, size=7, r=1.7):
    return (f'<pattern id="ht{uid}" width="{size}" height="{size}" patternUnits="userSpaceOnUse">'
            f'<circle cx="{size/2}" cy="{size/2}" r="{r}" fill="{c}"/></pattern>')


def misreg(x, y, w, h, rx, c, sw=1.6, dx=2.5, dy=2.5, op=0.28):
    """Offset second impression — cheap risograph misregistration."""
    return (f'<rect x="{x+dx}" y="{y+dy}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="none" stroke="{c}" stroke-width="{sw}" opacity="{op}"/>')


def svg(w, h, body, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" aria-label="{label}">\n'
            f'{body}\n</svg>\n')


def text(x, y, s, size, fill, font=SERIF, weight="normal", anchor="start",
         ls=0, opacity=1, style=""):
    s = (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    return (f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}" letter-spacing="{ls}" '
            f'opacity="{opacity}"{(" " + style) if style else ""}>{s}</text>')


def fmt(n):
    return f"{n:,}"


# ─────────────────────────── header ────────────────────────────────────────
def header(mode):
    c = T[mode]
    W, H = 1200, 300
    b = []
    b.append(f'<defs>{halftone("a", c["ink"], 8, 1.6)}{halftone("b", c["orange"], 10, 2.2)}</defs>')

    # paper panel
    b.append(f'<rect x="2" y="2" width="{W-4}" height="{H-4}" rx="22" fill="{c["card"]}"/>')
    b.append(misreg(2, 2, W - 4, H - 4, 22, c["orange"], 2.0, 3, 3, 0.30))
    b.append(f'<rect x="2" y="2" width="{W-4}" height="{H-4}" rx="22" fill="none" '
             f'stroke="{c["rule"]}" stroke-width="1.4"/>')

    # halftone corners
    b.append(f'<rect x="{W-250}" y="2" width="180" height="120" rx="22" fill="url(#hta)" opacity="0.10"/>')
    b.append(f'<rect x="2" y="{H-110}" width="150" height="100" rx="22" fill="url(#htb)" opacity="0.09"/>')

    # leaves
    b += [
        leaf(96, 96, 1.5, -18, c["orange"]),
        leaf(168, 208, 1.0, 26, c["rust"], .9),
        leaf(W - 150, 214, 1.25, -34, c["amber"], .95),
        leaf(W - 92, 96, .85, 12, c["olive"], .85),
        leaf(250, 62, .7, 40, c["mustard"], .8),
        leaf(W - 268, 250, .6, -8, c["rust"], .7),
    ]

    # name, printed twice
    cx = W / 2
    b.append(text(cx + 3, 158, "Kaleb Wright", 76, c["amber"], weight="bold",
                  anchor="middle", ls=-1.5, opacity=.35))
    b.append(text(cx, 155, "Kaleb Wright", 76, c["ink"], weight="bold", anchor="middle", ls=-1.5))
    b.append(f'<path d="M{cx-150},186 C{cx-60},178 {cx+60},194 {cx+150},184" fill="none" '
             f'stroke="{c["orange"]}" stroke-width="3" stroke-linecap="round" opacity="0.85"/>')
    b.append(text(cx, 232, "e s t .  2 0 2 0", 15, c["sub"], font=MONO, anchor="middle", ls=2))

    return svg(W, H, "\n".join(b), "Kaleb Wright")


# ─────────────────────────── data card ─────────────────────────────────────
def data_card(mode):
    c = T[mode]
    W = 860
    P = 46
    b = []

    stats = [
        ("contributions", fmt(D["contributions_year"]), "this year"),
        ("commits", fmt(D["commits"]), "last 12 mo"),
        ("repositories", str(D["repos_total"]), f'{D["private"]} private'),
        ("stars", str(D["stars"]), "earned"),
        ("longest streak", f'{D["longest_streak"]} d', "in a row"),
        ("storage", f'{D["storage_kb"]/1024:.0f} MB', "on github"),
        ("active days", str(sum(1 for _, n in D["calendar"] if n > 0)), "of 366"),
        ("since", D["since"], "public code"),
    ]

    # calculate height
    grid_top = 150
    row_h = 74
    rows = 2
    grid_bottom = grid_top + rows * row_h
    loc_top = grid_bottom + 58
    bars_top = loc_top + 150
    H = int(bars_top + 4 * 46 + 70)

    b.append(f'<defs>{halftone("d", c["ink"], 9, 1.8)}</defs>')
    b.append(f'<rect x="2" y="2" width="{W-4}" height="{H-4}" rx="20" fill="{c["card"]}"/>')
    b.append(misreg(2, 2, W - 4, H - 4, 20, c["orange"], 1.8, 3, 3, 0.26))
    b.append(f'<rect x="2" y="2" width="{W-4}" height="{H-4}" rx="20" fill="none" '
             f'stroke="{c["rule"]}" stroke-width="1.3"/>')
    b.append(f'<rect x="{W-170}" y="2" width="168" height={H-4} rx="20" fill="url(#htd)" opacity="0.07"/>')

    # heading
    b.append(leaf(P + 6, 58, .62, -12, c["orange"]))
    b.append(text(P + 26, 68, "MY GITHUB DATA", 15, c["sub"], font=MONO, ls=3.4))
    b.append(text(W - P, 68, "github.com/kkaleb-w", 13, c["sub"], font=MONO, anchor="end", ls=0.5))
    b.append(f'<path d="M{P},92 C{P+180},86 {W-P-180},98 {W-P},90" fill="none" '
             f'stroke="{c["rule"]}" stroke-width="1.4"/>')

    # 4x2 stat grid
    col_w = (W - 2 * P) / 4
    for i, (label, val, note) in enumerate(stats):
        r, col = divmod(i, 4)
        x = P + col * col_w
        y = grid_top + r * row_h
        b.append(text(x, y, label, 14, c["sub"], font=MONO, ls=1.2))
        b.append(text(x, y + 34, val, 34, c["ink"], weight="bold"))
        b.append(text(x, y + 54, note, 12.5, c["sub"], opacity=.9))

    # lines of code
    b.append(f'<path d="M{P},{loc_top-8} C{P+200},{loc_top-14} {W-P-200},{loc_top-2} {W-P},{loc_top-10}" '
             f'fill="none" stroke="{c["rule"]}" stroke-width="1.4"/>')
    b.append(text(P, loc_top + 28, "LINES OF CODE", 15, c["sub"], font=MONO, ls=3.4))
    b.append(text(P, loc_top + 88, fmt(D["loc"]), 58, c["orange"], weight="bold", ls=-1))
    b.append(text(P + 6, loc_top + 116, f'across {D["loc_files"]} source files, '
                                      f'{len([k for k, v in D["loc_per_repo"].items() if v])} repositories',
                  13.5, c["sub"], font=MONO))

    # rhythm bars
    hours = D["hours"]
    buckets = [
        ("morning", "5–11", sum(hours[5:12])),
        ("daytime", "12–16", sum(hours[12:17])),
        ("evening", "17–21", sum(hours[17:22])),
        ("night", "22–4", sum(hours[22:24]) + sum(hours[0:5])),
    ]
    total = max(1, sum(v for _, _, v in buckets))
    b.append(text(P, bars_top - 14, "WHEN I COMMIT", 15, c["sub"], font=MONO, ls=3.4))

    bar_x = P + 132
    bar_w = W - P - bar_x - 78
    for i, (name, span, v) in enumerate(buckets):
        y = bars_top + 18 + i * 46
        pct = v / total
        b.append(text(P, y + 5, name, 15, c["ink"]))
        b.append(text(P + 96, y + 5, span, 12, c["sub"], font=MONO))
        b.append(f'<rect x="{bar_x}" y="{y-9}" width="{bar_w}" height="14" rx="7" fill="{c["shade"]}"/>')
        fill = [c["mustard"], c["amber"], c["orange"], c["rust"]][i]
        b.append(f'<rect x="{bar_x}" y="{y-9}" width="{max(6, bar_w*pct):.1f}" height="14" rx="7" fill="{fill}"/>')
        b.append(text(W - P, y + 5, f"{pct*100:.0f}%", 14, c["sub"], font=MONO, anchor="end"))

    return svg(W, H, "\n".join(b), "My GitHub data")


# ─────────────────────────── activity ──────────────────────────────────────
def activity(mode):
    c = T[mode]
    weeks = {}
    for date, n in D["calendar"]:
        y, m, d = map(int, date.split("-"))
        # ISO week index by column date
        weeks.setdefault(date, n)

    dates = [d for d, _ in D["calendar"]]
    counts = {d: n for d, n in D["calendar"]}

    # group into columns of 7 starting from the first Sunday
    import datetime as dt
    first = dt.date.fromisoformat(dates[0])
    start = first - dt.timedelta(days=(first.weekday() + 1) % 7)
    cols = (dt.date.fromisoformat(dates[-1]) - start).days // 7 + 1

    P, cell, gap, top = 46, 12, 4, 74
    W = 860
    grid_w = cols * (cell + gap) - gap
    H = int(top + 7 * (cell + gap) + 56)

    b = [f'<defs>{halftone("e", c["ink"], 9, 1.8)}</defs>']
    b.append(f'<rect x="2" y="2" width="{W-4}" height="{H-4}" rx="20" fill="{c["card"]}"/>')
    b.append(misreg(2, 2, W - 4, H - 4, 20, c["orange"], 1.8, 3, 3, 0.26))
    b.append(f'<rect x="2" y="2" width="{W-4}" height="{H-4}" rx="20" fill="none" '
             f'stroke="{c["rule"]}" stroke-width="1.3"/>')

    b.append(text(P, 46, "THE YEAR IN COMMITS", 15, c["sub"], font=MONO, ls=3.4))
    b.append(text(W - P, 46, f'{fmt(D["contributions_12mo"])} contributions', 13, c["sub"],
                  font=MONO, anchor="end"))

    scale = [c["shade"], "#E9C58A" if mode == "light" else "#6B4A24",
             c["mustard"], c["amber"], c["orange"], c["rust"]]

    def bucket(n):
        return 0 if n == 0 else 1 if n <= 1 else 2 if n <= 3 else 3 if n <= 6 else 4 if n <= 12 else 5

    for i, date in enumerate(dates):
        d0 = dt.date.fromisoformat(date)
        col = (d0 - start).days // 7
        row = (d0.weekday() + 1) % 7
        x = P + col * (cell + gap)
        y = top + row * (cell + gap)
        b.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2.5" '
                 f'fill="{scale[bucket(counts[date])]}"/>')

    # legend
    ly = top + 7 * (cell + gap) + 18
    b.append(text(P, ly + 8, "less", 11, c["sub"], font=MONO))
    for i, col in enumerate(scale):
        b.append(f'<rect x="{P+34+i*18}" y="{ly}" width="12" height="12" rx="2.5" fill="{col}"/>')
    b.append(text(P + 34 + 6 * 18 + 2, ly + 8, "more", 11, c["sub"], font=MONO))

    return svg(W, H, "\n".join(b), "Contributions over the last year")


# ─────────────────────────── languages ─────────────────────────────────────
LANG_OF = {
    ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript",
    ".py": "Python", ".css": "CSS", ".scss": "SCSS", ".html": "HTML",
    ".sh": "Shell", ".go": "Go", ".rs": "Rust", ".java": "Java", ".sql": "SQL",
    ".c": "C", ".h": "C", ".cpp": "C++", ".rb": "Ruby", ".php": "PHP",
}


def languages():
    """Share of code lines per language — measured from source, not repo bytes."""
    f = ROOT / "data" / "loc_by_ext.json"
    counts = json.loads(f.read_text())
    agg = {}
    for ext, n in counts.items():
        lang = LANG_OF.get(ext)
        if lang:
            agg[lang] = agg.get(lang, 0) + n
    total = max(1, sum(agg.values()))
    return sorted(((k, v / total) for k, v in agg.items()), key=lambda x: -x[1])[:6]


def lang_card(mode):
    c = T[mode]
    langs = languages()
    W = 860
    P = 46
    row_h = 44
    H = int(120 + len(langs) * row_h + 30)

    b = [f'<defs>{halftone("f", c["ink"], 9, 1.8)}</defs>']
    b.append(f'<rect x="2" y="2" width="{W-4}" height="{H-4}" rx="20" fill="{c["card"]}"/>')
    b.append(misreg(2, 2, W - 4, H - 4, 20, c["orange"], 1.8, 3, 3, 0.26))
    b.append(f'<rect x="2" y="2" width="{W-4}" height="{H-4}" rx="20" fill="none" '
             f'stroke="{c["rule"]}" stroke-width="1.3"/>')
    b.append(text(P, 46, "WHERE THE CODE IS", 15, c["sub"], font=MONO, ls=3.4))
    b.append(text(W - P, 46, "by bytes, public repos", 13, c["sub"], font=MONO, anchor="end"))

    cols = [c["orange"], c["amber"], c["olive"], c["rust"], c["mustard"], c["sub"]]
    bar_x = P + 150
    bar_w = W - P - bar_x - 90
    for i, (name, share) in enumerate(langs):
        y = 96 + i * row_h
        b.append(text(P, y + 5, name, 15, c["ink"]))
        b.append(f'<rect x="{bar_x}" y="{y-10}" width="{bar_w}" height="14" rx="7" fill="{c["shade"]}"/>')
        b.append(f'<rect x="{bar_x}" y="{y-10}" width="{max(6, bar_w*share):.1f}" height="14" '
                 f'rx="7" fill="{cols[i % len(cols)]}"/>')
        b.append(text(W - P, y + 5, f"{share*100:.1f}%", 14, c["sub"], font=MONO, anchor="end"))

    return svg(W, H, "\n".join(b), "Languages")


if __name__ == "__main__":
    for mode in ("light", "dark"):
        for name, fn in (("header", header), ("data", data_card),
                         ("activity", activity), ("langs", lang_card)):
            (OUT / f"{name}-{mode}.svg").write_text(fn(mode))
        print("rendered", mode)
    print("loc", D["loc"], "files", D["loc_files"], "langs", languages()[:3])
