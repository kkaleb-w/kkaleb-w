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
                  olive="#6E7B3F", mustard="#E3B23C", shade="#F0DFBD", empty="#F7EBD2"),
    "dark": dict(paper="#181008", card="#221607", ink="#F4E5C8", sub="#BBA689",
                 rule="#48381F", orange="#E4813F", amber="#EBA84C", rust="#C05F31",
                 olive="#9BA96B", mustard="#EFC65F", shade="#2C1D0E", empty="#1B1106"),
}

LEAF = ("M0,-11 C1.5,-8.2 2.2,-7.2 3.2,-6.6 C4.6,-9 6,-9.4 7,-8.4 "
        "C6.4,-6.4 6,-5 6.6,-4 C8.6,-5 10.4,-4.4 11,-3 "
        "C9,-1.4 7.6,-0.6 7.1,0.9 C8.6,1.4 9.4,2.6 8.9,3.9 "
        "C6.9,4.4 5,4.4 3.6,5 C3.1,7 2.1,8.4 0.7,9.4 L0.7,12 L-0.7,12 L-0.7,9.4 "
        "C-2.1,8.4 -3.1,7 -3.6,5 C-5,4.4 -6.9,4.4 -8.9,3.9 "
        "C-9.4,2.6 -8.6,1.4 -7.1,0.9 C-7.6,-0.6 -9,-1.4 -11,-3 "
        "C-10.4,-4.4 -8.6,-5 -6.6,-4 C-6,-5 -6.4,-6.4 -7,-8.4 "
        "C-6,-9.4 -4.6,-9 -3.2,-6.6 C-2.2,-7.2 -1.5,-8.2 0,-11 Z")


def leaf(x, y, s, rot, fill, op=1.0, vein=None):
    v = ""
    if vein:
        v = (f'<path d="M0,-8 L0,10 M0,-2 L-6,-6 M0,-2 L6,-6 M0,3 L-5,7 M0,3 L5,7" '
             f'stroke="{vein}" stroke-width="0.9" fill="none" opacity="0.5"/>')
    return (f'<g transform="translate({x},{y}) rotate({rot}) scale({s})" opacity="{op}">'
            f'<path d="{LEAF}" fill="{fill}"/>{v}</g>')


def acorn(x, y, s, body, cap, ink):
    return (f'<g transform="translate({x},{y}) scale({s})">'
            f'<path d="M-7,-3 C-7,-8 -3,-10 0,-10 C3,-10 7,-8 7,-3 Z" fill="{cap}"/>'
            f'<path d="M-6,-3 C-6,4 -3,10 0,11 C3,10 6,4 6,-3 Z" fill="{body}"/>'
            f'<path d="M0,-10 L0,-13" stroke="{ink}" stroke-width="1.6" stroke-linecap="round"/></g>')


def doghouse(x, y, s, ink, fill):
    return (f'<g transform="translate({x},{y}) scale({s})">'
            f'<path d="M-46,0 L0,-38 L46,0 L38,0 L38,54 L-38,54 L-38,0 Z" '
            f'fill="{fill}" stroke="{ink}" stroke-width="3" stroke-linejoin="round"/>'
            f'<path d="M-20,54 L-20,26 C-20,14 20,14 20,26 L20,54" '
            f'fill="none" stroke="{ink}" stroke-width="3"/>'
            f'<path d="M-40,-2 L40,-2" stroke="{ink}" stroke-width="3" opacity="0"/></g>')


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

    b.append(f'<rect x="2" y="2" width="{W-4}" height="{H-4}" rx="24" fill="{c["card"]}"/>')
    b.append(misreg(2, 2, W - 4, H - 4, 24, c["orange"], 2.0, 3, 3, 0.30))
    b.append(f'<rect x="2" y="2" width="{W-4}" height="{H-4}" rx="24" fill="none" '
             f'stroke="{c["rule"]}" stroke-width="1.4"/>')

    # branch: trunk in from the right edge, one twig, tapering to a tip
    b.append(f'<path d="M1216,40 C1136,70 1066,106 1010,146 C986,163 972,184 966,208" '
             f'fill="none" stroke="{c["ink"]}" stroke-width="9" stroke-linecap="round"/>')
    b.append(f'<path d="M1046,120 C1020,148 998,172 980,200" fill="none" stroke="{c["ink"]}" '
             f'stroke-width="4" stroke-linecap="round" opacity="0.95"/>')
    b.append(f'<path d="M1104,82 C1074,66 1048,58 1022,56" fill="none" stroke="{c["ink"]}" '
             f'stroke-width="3.4" stroke-linecap="round" opacity="0.9"/>')

    # leaves sit on the branch, not around it
    b.append(leaf(1128, 82, 1.35, 208, c["orange"], .98, vein=c["card"]))
    b.append(leaf(1062, 122, 1.5, 150, c["amber"], .97, vein=c["card"]))
    b.append(leaf(1016, 158, 1.2, 118, c["rust"], .96, vein=c["card"]))
    b.append(leaf(962, 202, 1.0, 84, c["mustard"], .95))
    b.append(leaf(1018, 54, 1.15, -22, c["olive"], .92, vein=c["card"]))
    b.append(leaf(1088, 150, .8, 40, c["rust"], .8))
    b.append(acorn(1032, 138, .95, c["mustard"], c["rust"], c["ink"]))

    # two on the way down
    b.append(leaf(922, 108, .8, -40, c["amber"], .55))
    b.append(leaf(898, 186, .65, 25, c["rust"], .5))
    # one come to rest at the end of the rule, tying both halves together
    b.append(leaf(372, 176, 1.05, -22, c["orange"], .95, vein=c["card"]))
    b.append(leaf(392, 196, .55, 30, c["rust"], .7))

    # type
    x = 92
    b.append(text(x, 143, "Kaleb Wright", 82, c["ink"], weight="bold", ls=-2))
    b.append(f'<path d="M{x},178 C{x+80},174 {x+180},178 {x+268},176" fill="none" '
             f'stroke="{c["orange"]}" stroke-width="2.6" stroke-linecap="round"/>')
    b.append(text(x, 216, "est. 2020", 15, c["sub"], font=SERIF, style='font-style="italic"'))
    b.append(text(x + 78, 216, "·", 15, c["sub"], font=SERIF))
    b.append(text(x + 96, 216, "github.com/kkaleb-w", 15, c["sub"], font=SERIF, style='font-style="italic"'))

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
        ("languages", str(len(languages())), "in use"),
    ]

    # calculate height
    grid_top = 142
    row_h = 76
    rows = 2
    grid_bottom = grid_top + rows * row_h
    loc_top = grid_bottom + 46
    bars_top = loc_top + 142
    H = int(bars_top + 4 * 42 + 44)


    b.append(f'<rect x="2" y="2" width="{W-4}" height="{H-4}" rx="20" fill="{c["card"]}"/>')
    b.append(misreg(2, 2, W - 4, H - 4, 20, c["orange"], 1.8, 3, 3, 0.26))
    b.append(f'<rect x="2" y="2" width="{W-4}" height="{H-4}" rx="20" fill="none" '
             f'stroke="{c["rule"]}" stroke-width="1.3"/>')


    # heading
    b.append(leaf(P + 6, 58, .62, -12, c["orange"]))
    b.append(text(P + 26, 69, "my github data", 17, c["sub"], weight="bold", ls=2.6))
    b.append(text(W - P, 68, "github.com/kkaleb-w", 12.5, c["sub"], font=MONO, anchor="end", ls=0.4, opacity=.85))
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
        b.append(text(x, y + 55, note, 12.5, c["sub"], opacity=.88))

    # lines of code
    b.append(f'<path d="M{P},{loc_top-8} C{P+200},{loc_top-14} {W-P-200},{loc_top-2} {W-P},{loc_top-10}" '
             f'fill="none" stroke="{c["rule"]}" stroke-width="1.4"/>')
    b.append(text(P, loc_top + 26, "lines of code", 17, c["sub"], weight="bold", ls=2.6))
    b.append(text(P, loc_top + 84, fmt(D["loc"]), 54, c["orange"], weight="bold", ls=-1))
    b.append(text(W - P, loc_top + 70, f'{D["loc_files"]} source files', 13.5, c["sub"],
                  font=MONO, anchor="end"))
    b.append(text(W - P, loc_top + 92, f'across {len([k for k, v in D["loc_per_repo"].items() if v])} repositories',
                  13.5, c["sub"], font=MONO, anchor="end"))

    # rhythm bars
    hours = D["hours"]
    buckets = [
        ("morning", "5–11", sum(hours[5:12])),
        ("daytime", "12–16", sum(hours[12:17])),
        ("evening", "17–21", sum(hours[17:22])),
        ("night", "22–4", sum(hours[22:24]) + sum(hours[0:5])),
    ]
    total = max(1, sum(v for _, _, v in buckets))
    b.append(text(P, bars_top - 24, "when i commit", 17, c["sub"], weight="bold", ls=2.6))

    bar_x = P + 132
    bar_w = W - P - bar_x - 78
    for i, (name, span, v) in enumerate(buckets):
        y = bars_top + 16 + i * 42
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

    b = []
    b.append(f'<rect x="2" y="2" width="{W-4}" height="{H-4}" rx="20" fill="{c["card"]}"/>')
    b.append(misreg(2, 2, W - 4, H - 4, 20, c["orange"], 1.8, 3, 3, 0.26))
    b.append(f'<rect x="2" y="2" width="{W-4}" height="{H-4}" rx="20" fill="none" '
             f'stroke="{c["rule"]}" stroke-width="1.3"/>')

    b.append(text(P, 47, "the year in commits", 17, c["sub"], weight="bold", ls=2.6))
    b.append(text(W - P, 47, f'{fmt(D["contributions_12mo"])} contributions', 13, c["sub"],
                  font=MONO, anchor="end"))

    scale = [c["empty"], "#E4BC7E" if mode == "light" else "#6B4A24",
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
                 f'fill="{scale[bucket(counts[date])]}" stroke="{c["rule"]}" '
                 f'stroke-width="0.6" stroke-opacity="0.55"/>')

    # legend
    ly = top + 7 * (cell + gap) + 18
    b.append(text(P, ly + 9, "less", 12, c["sub"]))
    for i, col in enumerate(scale):
        b.append(f'<rect x="{P+40+i*19}" y="{ly}" width="13" height="13" rx="2.5" fill="{col}"/>')
    b.append(text(P + 40 + 6 * 19 + 3, ly + 9, "more", 12, c["sub"]))

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

    b = []
    b.append(f'<rect x="2" y="2" width="{W-4}" height="{H-4}" rx="20" fill="{c["card"]}"/>')
    b.append(misreg(2, 2, W - 4, H - 4, 20, c["orange"], 1.8, 3, 3, 0.26))
    b.append(f'<rect x="2" y="2" width="{W-4}" height="{H-4}" rx="20" fill="none" '
             f'stroke="{c["rule"]}" stroke-width="1.3"/>')
    b.append(text(P, 47, "where the code is", 17, c["sub"], weight="bold", ls=2.6))
    b.append(text(W - P, 46, "share of lines written", 13, c["sub"], font=MONO, anchor="end"))

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


def stamp():
    """Put a content hash in the README image URLs — camo caches by URL."""
    import hashlib, re
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



# ─────────────────────────── the one panel ─────────────────────────────────
def panel(mode):
    c = T[mode]
    W, H = 1000, 1040
    P, R = 48, 952
    b = []

    # paper
    b.append(f'<rect x="2" y="2" width="{W-4}" height="{H-4}" rx="26" fill="{c["card"]}"/>')
    b.append(misreg(2, 2, W - 4, H - 4, 26, c["orange"], 2.0, 3, 3, 0.28))
    b.append(f'<rect x="2" y="2" width="{W-4}" height="{H-4}" rx="26" fill="none" '
             f'stroke="{c["rule"]}" stroke-width="1.4"/>')

    def rule(y):
        b.append(f'<path d="M{P},{y} C{P+240},{y-5} {R-240},{y+5} {R},{y-1}" fill="none" '
                 f'stroke="{c["rule"]}" stroke-width="1.3"/>')

    # ── masthead ───────────────────────────────────────────────────────────
    b.append(f'<path d="M1006,30 C900,54 806,96 744,150 C720,170 704,186 696,200" '
             f'fill="none" stroke="{c["ink"]}" stroke-width="8.5" stroke-linecap="round"/>')
    b.append(f'<path d="M812,80 C788,66 766,58 744,56" fill="none" stroke="{c["ink"]}" '
             f'stroke-width="3.4" stroke-linecap="round" opacity="0.9"/>')
    b.append(f'<path d="M760,138 C736,140 716,146 700,154" fill="none" stroke="{c["ink"]}" '
             f'stroke-width="3" stroke-linecap="round" opacity="0.85"/>')
    b.append(leaf(918, 60, 1.3, 202, c["orange"], .97, vein=c["card"]))
    b.append(leaf(846, 96, 1.45, 156, c["amber"], .96, vein=c["card"]))
    b.append(leaf(760, 148, 1.2, 122, c["rust"], .95, vein=c["card"]))
    b.append(leaf(740, 54, 1.15, -22, c["olive"], .92, vein=c["card"]))
    b.append(leaf(700, 152, .9, 70, c["mustard"], .9))
    b.append(leaf(878, 140, .8, 40, c["rust"], .8))
    b.append(acorn(806, 118, .95, c["mustard"], c["rust"], c["ink"]))
    b.append(leaf(650, 96, .7, -44, c["amber"], .5))
    b.append(leaf(660, 196, .55, 26, c["rust"], .45))
    b.append(leaf(1000, 132, .6, 12, c["rust"], .55))

    b.append(text(P, 136, "Kaleb Wright", 74, c["ink"], weight="bold", ls=-1.8))
    b.append(f'<path d="M{P},168 C{P+80},164 {P+180},168 {P+262},166" fill="none" '
             f'stroke="{c["orange"]}" stroke-width="2.6" stroke-linecap="round"/>')
    b.append(leaf(330, 166, 1.0, -22, c["orange"], .95, vein=c["card"]))
    b.append(text(P, 202, "est. 2020", 14.5, c["sub"], style='font-style="italic"'))
    b.append(text(P + 76, 202, "·", 14.5, c["sub"]))
    b.append(text(P + 94, 202, "github.com/kkaleb-w", 14.5, c["sub"], style='font-style="italic"'))
    rule(246)

    # ── eight numbers ──────────────────────────────────────────────────────
    stats = [
        ("contributions", fmt(D["contributions_year"]), "this year"),
        ("commits", fmt(D["commits"]), "last 12 mo"),
        ("repositories", str(D["repos_total"]), f'{D["private"]} private'),
        ("stars", str(D["stars"]), "earned"),
        ("longest streak", f'{D["longest_streak"]} d', "in a row"),
        ("storage", f'{D["storage_kb"]/1024:.0f} MB', "on github"),
        ("active days", str(sum(1 for _, n in D["calendar"] if n > 0)), "of 366"),
        ("languages", str(len(languages())), "in use"),
    ]
    col_w = (R - P) / 4
    for i, (label, val, note) in enumerate(stats):
        r, col = divmod(i, 4)
        x = P + col * col_w
        y = 292 + r * 74
        b.append(text(x, y, label, 13.5, c["sub"], font=MONO, ls=1))
        b.append(text(x, y + 36, val, 30, c["ink"], weight="bold"))
        b.append(text(x, y + 57, note, 12.5, c["sub"], opacity=.88))
    rule(440)

    # ── lines of code, and when ─────────────────────────────────────────────
    b.append(text(P, 480, "lines of code", 16, c["sub"], weight="bold", ls=2.4))
    b.append(text(P, 542, fmt(D["loc"]), 52, c["orange"], weight="bold", ls=-1))
    b.append(text(P, 568, f'{D["loc_files"]} source files across '
                           f'{len([k for k, v in D["loc_per_repo"].items() if v])} repositories',
                  12.5, c["sub"], font=MONO))

    hours = D["hours"]
    buckets = [("morning", "5–11", sum(hours[5:12]), c["mustard"]),
               ("daytime", "12–16", sum(hours[12:17]), c["amber"]),
               ("evening", "17–21", sum(hours[17:22]), c["orange"]),
               ("night", "22–4", sum(hours[22:24]) + sum(hours[0:5]), c["rust"])]
    total = max(1, sum(v for _, _, v, _ in buckets))
    bx = 520
    b.append(text(bx, 480, "when i commit", 16, c["sub"], weight="bold", ls=2.4))
    bar_x, bar_w = bx + 116, R - bx - 116 - 46
    for i, (name, span, v, fill) in enumerate(buckets):
        y = 512 + i * 34
        b.append(text(bx, y + 4, name, 14, c["ink"]))
        b.append(text(bx + 72, y + 4, span, 11, c["sub"], font=MONO))
        b.append(f'<rect x="{bar_x}" y="{y-8}" width="{bar_w}" height="13" rx="6.5" fill="{c["shade"]}"/>')
        b.append(f'<rect x="{bar_x}" y="{y-8}" width="{max(5, bar_w*v/total):.1f}" height="13" '
                 f'rx="6.5" fill="{fill}"/>')
        b.append(text(R, y + 4, f"{v/total*100:.0f}%", 13, c["sub"], font=MONO, anchor="end"))
    rule(626)

    # ── the year ───────────────────────────────────────────────────────────
    b.append(text(P, 664, "the year in commits", 16, c["sub"], weight="bold", ls=2.4))

    import datetime as dt
    dates = {d: n for d, n in D["calendar"]}
    first = dt.date.fromisoformat(min(dates))
    start = first - dt.timedelta(days=(first.weekday() + 1) % 7)
    scale = [c["empty"], "#E4BC7E" if mode == "light" else "#6B4A24",
             c["mustard"], c["amber"], c["orange"], c["rust"]]

    def bucket(n):
        return 0 if n == 0 else 1 if n <= 1 else 2 if n <= 3 else 3 if n <= 6 else 4 if n <= 12 else 5

    cols_n = (dt.date.fromisoformat(max(dates)) - start).days // 7 + 1
    gap, top = 3.6, 688
    cell = ((R - P) - (cols_n - 1) * gap) / cols_n
    for date, n in dates.items():
        d0 = dt.date.fromisoformat(date)
        x = P + ((d0 - start).days // 7) * (cell + gap)
        y = top + ((d0.weekday() + 1) % 7) * (cell + gap)
        b.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" rx="2.6" '
                 f'fill="{scale[bucket(n)]}" stroke="{c["rule"]}" stroke-width="0.6" '
                 f'stroke-opacity="0.5"/>')

    # legend sits on the label row, right aligned, with real gaps
    sw, sgap, n = 13, 5, len(scale)
    band = 34 + n * sw + (n - 1) * sgap + 4          # "less" + swatches + pad
    lx = R - (band + 30)                             # 30 = width of "more"
    b.append(text(lx, 664, "less", 11, c["sub"], font=MONO))
    for i, col in enumerate(scale):
        b.append(f'<rect x="{lx + 34 + i*(sw+sgap)}" y="{654}" width="{sw}" height="{sw}" rx="2.6" '
                 f'fill="{col}" stroke="{c["rule"]}" stroke-width="0.6" stroke-opacity="0.5"/>')
    b.append(text(lx + band + 4, 664, "more", 11, c["sub"], font=MONO))
    rule(826)

    # ── languages ──────────────────────────────────────────────────────────
    b.append(text(P, 864, "where the code is", 16, c["sub"], weight="bold", ls=2.4))
    cols = [c["orange"], c["amber"], c["olive"], c["rust"], c["mustard"], c["sub"]]
    for i, (name, share) in enumerate(languages()):
        col, row = divmod(i, 3)
        x = P + col * 476
        y = 904 + row * 42
        b.append(text(x, y, name, 14, c["ink"]))
        b.append(f'<rect x="{x+120}" y="{y-9}" width="230" height="12" rx="6" fill="{c["shade"]}"/>')
        b.append(f'<rect x="{x+120}" y="{y-9}" width="{max(5, 230*share):.1f}" height="12" '
                 f'rx="6" fill="{cols[i % len(cols)]}"/>')
        b.append(text(x + 366, y, f"{share*100:.1f}%", 13, c["sub"], font=MONO, anchor="end"))

    return svg(W, H, "\n".join(b), "Kaleb Wright — GitHub data, contributions, languages")


if __name__ == "__main__":
    for mode in ("light", "dark"):
        (OUT / f"panel-{mode}.svg").write_text(panel(mode))
        print("rendered", mode)
    tag, n = stamp()
    print(f"cache tag {tag} on {n} refs")
    print("loc", D["loc"], "files", D["loc_files"], "langs", languages()[:3])
