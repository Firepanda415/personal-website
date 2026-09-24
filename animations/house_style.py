"""Shared look and narration sync for the website explainers.

Colors follow style.css on mqzh.science. Text uses IBM Plex Sans from fonts/.
Mathematics is typeset by Typst (New Computer Modern Math) and imported as SVG.
"""
import hashlib
import json
import re
import subprocess
from contextlib import contextmanager
from pathlib import Path

import manimpango
from manim import *

HERE = Path(__file__).parent
BUILD = HERE / "build"

PAPER = "#f6f5f1"
INK = "#242b2d"
MUTED = "#5b6262"
ACCENT = "#793e4b"
LINE = "#d4d5ce"
WASH = "#ecece5"
CV = "#2b6c70"     # oscillator (continuous variable)
DV = "#3d5a86"     # qubits (discrete variable)
GOLD = "#a06b12"

FONT = "IBM Plex Sans"
for ttf in sorted((HERE / "fonts").glob("*.ttf")):
    manimpango.register_font(str(ttf))

config.background_color = PAPER


def T(text, size=30, color=INK, weight=NORMAL, **kw):
    """Plex text, laid out at 4x size because Pango collapses word spaces at small sizes.

    Manim wraps Text at the output pixel width, so layout uses a wide page instead.
    """
    saved = config.pixel_width
    config.pixel_width = 8000
    try:
        return Text(text, font=FONT, font_size=4 * size, color=color, weight=weight, **kw).scale(0.25)
    finally:
        config.pixel_width = saved


def eyebrow(text, color=ACCENT, size=17):
    """Small upper-case label in the style of the site's section headings (tracked with hair spaces)."""
    return T("\u200a".join(text.upper()), size, color, weight=MEDIUM)


_TYPST = r'''#set page(width: auto, height: auto, margin: 1pt, fill: none)
#set text(size: 20pt, fill: rgb("{color}"))
#let c(col, body) = text(fill: rgb(col), body)
#let bra(x) = $lr(chevron.l #x |)$
#let ket(x) = $lr(| #x chevron.r)$
$ {expr} $
'''
TYPST_BIN = Path(subprocess.os.sys.executable).with_name("typst")
PT = 0.0205  # Manim units per typographic point, so 20 pt math matches ~40 px Text


_RULE = re.compile(r'<path fill="none" stroke="(#[0-9a-f]{6})" stroke-width="([0-9.]+)"[^>]*'
                   r'transform="translate\(([-0-9.]+) ([-0-9.]+)\)" d="M 0 0h ([0-9.]+)"/>')


def _fill_rules(svg):
    """Typst draws fraction bars as stroked lines. Redraw them as filled rectangles so
    they scale with the formula, since glyphs are imported with stroke width zero."""
    def rect(m):
        color, w, x, y, length = m.group(1), float(m.group(2)), m.group(3), float(m.group(4)), m.group(5)
        return f'<rect x="{x}" y="{y - w / 2}" width="{length}" height="{w}" fill="{color}"/>'
    svg = _RULE.sub(rect, svg)
    if "stroke=" in svg:
        raise ValueError("Typst SVG has a stroked shape other than a horizontal rule")
    return svg


def M(expr, size=1.0, color=INK):
    """Typeset a Typst math expression. Use #c("#hex", $...$) to color a part."""
    src = _TYPST.format(expr=expr, color=color)
    key = hashlib.sha256(src.encode()).hexdigest()[:16]
    out = BUILD / "typst" / f"{key}.svg"
    if not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        typ = out.with_suffix(".typ")
        typ.write_text(src)
        subprocess.run([str(TYPST_BIN), "compile", str(typ), str(out)], check=True)
        out.write_text(_fill_rules(out.read_text()))
    mob = SVGMobject(str(out), height=None, width=None, stroke_width=0)
    height_pt = float(out.read_text().split('height="')[1].split("pt")[0])
    mob.scale_to_fit_height(height_pt * PT * size)
    return mob


class Explainer(Scene):
    """Scene whose segments are timed by pre-synthesized narration."""

    timing_file = None

    def setup(self):
        self.timing = json.loads(Path(self.timing_file).read_text())
        self.captions = []

    @contextmanager
    def voice(self, key):
        seg = self.timing[key]
        start = self.renderer.time
        self.add_sound(str(Path(self.timing_file).with_name(seg["file"])))
        for s in seg["sentences"]:
            self.captions.append((start + s["start"], start + s["end"], s["text"]))
        tracker = _Tracker(self, start, seg)
        yield tracker
        left = seg["duration"] - (self.renderer.time - start)
        self.wait(max(left, 0) + 0.45)

    def tear_down(self):
        out = BUILD / f"{type(self).__name__}.captions.json"
        out.write_text(json.dumps(self.captions, ensure_ascii=False, indent=0))


class _Tracker:
    def __init__(self, scene, start, seg):
        self.scene, self.start, self.seg = scene, start, seg
        self.duration = seg["duration"]

    def elapsed(self):
        return self.scene.renderer.time - self.start

    def until(self, sentence, frac=0.0):
        """Wait until a fraction of the way into a sentence (index within the segment)."""
        s = self.seg["sentences"][sentence]
        target = s["start"] + frac * (s["end"] - s["start"])
        if target > self.elapsed() + 1e-3:
            self.scene.wait(target - self.elapsed())

    def dur(self, sentence):
        s = self.seg["sentences"][sentence]
        return s["end"] - s["start"]

    def left(self):
        return max(self.duration - self.elapsed(), 0.1)


def part(mob, color):
    """Glyphs of a Typst formula drawn in the given color."""
    return VGroup(*[m for m in mob.family_members_with_points() if m.get_fill_color().to_hex().lower() == color.lower()])
