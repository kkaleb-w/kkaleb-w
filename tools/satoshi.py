"""Satoshi, shaped to SVG outlines.

The ITF Free Font License (Satoshi ships under it) allows self-hosting and
embedding for your own use, and forbids redistributing the font software — so
this module never puts a font file in the repository. It loads Satoshi from
disk (the Fontshare download) or fetches it from Fontshare's public CDN into a
temp cache, shapes the string, and emits plain `<path>` data. The SVG ends up
with vector letterforms, which are artwork, not font software: nothing to
extract, nothing to license downstream, and no webfont request from GitHub's
image proxy.

    from satoshi import shape
    shape("Kaleb Wright", 74, weight="bold", tracking=-1.8)   # -> (path_d, width)
"""

from __future__ import annotations

import io
import os
import urllib.request
import zipfile
from pathlib import Path

CACHE = Path(os.environ.get("SATOSHI_CACHE", "/tmp/satoshi-cache"))
ZIP_URL = "https://api.fontshare.com/v2/fonts/download/satoshi"

# weight/style -> file inside the Fontshare download
FILES = {
    ("regular", False): "Satoshi-Regular.otf",
    ("medium", False): "Satoshi-Medium.otf",
    ("bold", False): "Satoshi-Bold.otf",
    ("black", False): "Satoshi-Black.otf",
    ("light", False): "Satoshi-Light.otf",
    ("regular", True): "Satoshi-Italic.otf",
    ("medium", True): "Satoshi-MediumItalic.otf",
    ("bold", True): "Satoshi-BoldItalic.otf",
    ("black", True): "Satoshi-BlackItalic.otf",
    ("light", True): "Satoshi-LightItalic.otf",
}


def _font_dir() -> Path:
    """Where the Satoshi files live: explicit dir, the upload, or a CDN cache."""
    for env in ("SATOSHI_DIR",):
        p = os.environ.get(env)
        if p and Path(p).is_dir():
            return Path(p)
    here = Path(__file__).resolve().parent.parent
    for cand in (here / "Satoshi_Complete" / "Fonts" / "OTF",
                 Path("/tmp/satoshi/Satoshi_Complete/Fonts/OTF")):
        if cand.is_dir():
            return cand
    otf = CACHE / "Satoshi_Complete" / "Fonts" / "OTF"
    if otf.is_dir():
        return otf
    CACHE.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(ZIP_URL, timeout=60) as r:
        blob = r.read()
    zipfile.ZipFile(io.BytesIO(blob)).extractall(CACHE)
    return otf


class _Face:
    """One weight/style: glyph outlines and advances in font units."""

    def __init__(self, path: Path):
        from fontTools.ttLib import TTFont
        from fontTools.pens.svgPathPen import SVGPathPen

        font = TTFont(path, fontNumber=0)
        self.upem = font["head"].unitsPerEm
        self.glyphs = font.getGlyphSet()
        self.cmap = font.getBestCmap()
        self._paths: dict[str, str] = {}
        self._pen_cls = SVGPathPen

    def glyph(self, ch: str) -> tuple[str, float] | None:
        name = self.cmap.get(ord(ch))
        if name is None:
            return None
        if name not in self._paths:
            pen = self._pen_cls(self.glyphs)
            self.glyphs[name].draw(pen)
            self._paths[name] = pen.getCommands()
        return self._paths[name], self.glyphs[name].width


_FACES: dict[tuple[str, bool], _Face] = {}


def _face(weight: str, italic: bool) -> _Face:
    key = (weight if (weight, italic) in FILES else "regular", italic)
    if key not in _FACES:
        _FACES[key] = _Face(_font_dir() / FILES[key])
    return _FACES[key]


def shape(s: str, size: float, weight: str = "normal", italic: bool = False,
          tracking: float = 0.0) -> tuple[str, float]:
    """Outline `s` at `size` px. Returns (svg path data in px, advance width)."""
    w = {"normal": "regular", "bold": "bold", "medium": "medium",
         "light": "light", "black": "black"}.get(str(weight), "regular")
    face = _face(w, italic)
    k = size / face.upem
    parts: list[str] = []
    pen = 0.0
    for ch in s:
        got = face.glyph(ch)
        if got is None:
            pen += size * 0.5 + tracking
            continue
        d, adv = got
        if d:
            # Font units are y-up, SVG is y-down: flip the glyph, then scale.
            parts.append(
                f'<path transform="translate({pen:.2f} 0) scale({k:.5f} {-k:.5f})" d="{d}"/>'
            )
        pen += adv * k + tracking
    width = pen - tracking if s else 0.0
    return "".join(parts), width


def measure(s: str, size: float, weight: str = "normal", italic: bool = False,
            tracking: float = 0.0) -> float:
    return shape(s, size, weight, italic, tracking)[1]
