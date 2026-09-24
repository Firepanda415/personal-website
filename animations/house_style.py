"""Shared look and narration sync for the website explainers.

Colors follow style.css on mqzh.science. Text uses IBM Plex Sans from fonts/.
Mathematics is typeset by Typst (New Computer Modern Math) and imported as SVG.
"""
import hashlib
import itertools
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


def header(number, title):
    return eyebrow(f"{number:02d} / {title}").to_corner(UL, buff=0.55)


def gate(label, width=1.0, height=0.75, color=INK, size=0.85):
    box = RoundedRectangle(corner_radius=0.08, width=width, height=height, stroke_color=color,
                           stroke_width=2.5, fill_color=PAPER, fill_opacity=1)
    lab = M(label, size) if isinstance(label, str) else label
    if lab.width > width - 0.2:
        lab.scale_to_fit_width(width - 0.2)
    return VGroup(box, lab.move_to(box))


def meter(color=INK):
    box = RoundedRectangle(corner_radius=0.08, width=0.8, height=0.62, stroke_color=color, stroke_width=2.5,
                           fill_color=PAPER, fill_opacity=1)
    arc = Arc(radius=0.24, start_angle=PI / 6, angle=2 * PI / 3, color=color, stroke_width=2.5).move_to(box).shift(0.02 * DOWN)
    needle = Line(box.get_center() + 0.16 * DOWN, box.get_center() + 0.16 * UP + 0.14 * RIGHT, color=color, stroke_width=2.5)
    return VGroup(box, arc, needle)


def wire(y, x0, x1, color=INK, width=2.5):
    return Line([x0, y, 0], [x1, y, 0], color=color, stroke_width=width)


def card(lines, width, color=LINE, pad=0.3):
    body = VGroup(*lines).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
    frame = RoundedRectangle(corner_radius=0.1, width=max(width, body.width + 2 * pad), height=body.height + 2 * pad,
                             stroke_color=color, stroke_width=2, fill_color=PAPER, fill_opacity=1)
    body.move_to(frame).align_to(frame, LEFT).shift(pad * RIGHT)
    return VGroup(frame, body)


CAPTION_BAND = 0.9   # height of the subtitle strip below the 8-unit design frame
CAPTION_WORDS = 14   # longest subtitle line, in words
CAPTION_CHARS = 70   # longest subtitle line, in characters (about 1600 px of Plex at 46 px)


# A subtitle line should not end on one of these words.
_WEAK_END = {"a", "an", "the", "of", "to", "in", "on", "by", "with", "for", "and", "or", "as", "at", "from",
             "its", "their", "that", "whose", "which", "these", "this", "is", "are", "than", "into", "per", "−"}


def _lines(words, n):
    """Split words into n lines of similar length, preferring breaks after punctuation and
    avoiding lines that end on an article, preposition, or conjunction."""
    if n == 1:
        return [words]
    sizes = [len(w) + 1 for w in words]
    ideal = sum(sizes) / n
    best = None
    for cuts in itertools.combinations(range(1, len(words)), n - 1):
        bounds = (0, *cuts, len(words))
        cost = sum(((sum(sizes[a:b]) - ideal) / ideal) ** 2 for a, b in zip(bounds, bounds[1:]))
        for c in cuts:
            last = words[c - 1]
            cost += (0.15 if last.lower() in _WEAK_END else 0) - (0.06 if last[-1] in ",;:." else 0)
            cost += 0.08 if words[c] == "of" else 0
        if best is None or cost < best[0]:
            best = (cost, bounds)
    return [words[a:b] for a, b in zip(best[1], best[1][1:])]


def cues(start, end, text):
    """Split a narrated sentence into subtitle lines timed in proportion to their length."""
    words = text.split()
    n = max(-(-len(words) // CAPTION_WORDS), -(-len(text) // CAPTION_CHARS))
    chunks = [" ".join(line) for line in _lines(words, n)]
    total = sum(len(c) for c in chunks)
    out, t = [], start
    for c in chunks:
        dt = (end - start) * len(c) / total
        out.append((t, t + dt, c))
        t += dt
    return out


class Explainer(Scene):
    """Scene whose segments are timed by pre-synthesized narration.

    The camera shows the usual 8-unit frame plus a strip below it, so subtitles never
    cover the animation. Scene layout code keeps using the 8-unit frame. The subtitle
    text is burned into the strip by finish.py from the cues written in tear_down.
    """

    timing_file = None

    def setup(self):
        self.timing = json.loads(Path(self.timing_file).read_text())
        self.captions = []
        cam = self.camera
        cam.frame_height = config.frame_height + CAPTION_BAND
        cam.frame_width = cam.frame_height * config.frame_width / config.frame_height
        cam.frame_center = np.array([0.0, -CAPTION_BAND / 2, 0.0])
        bottom = -config.frame_height / 2
        self.subtitle_band = Rectangle(width=cam.frame_width + 0.1, height=CAPTION_BAND, stroke_width=0,
                                       fill_color=WASH, fill_opacity=1).move_to([0, bottom - CAPTION_BAND / 2, 0])
        self.add(self.subtitle_band)

    def clear_stage(self, keep=(), run_time=0.7):
        """Fade out everything except the subtitle strip and the given mobjects."""
        keep = [*keep, self.subtitle_band]
        gone = [m for m in self.mobjects if m not in keep]
        if gone:
            self.play(*[FadeOut(m) for m in gone], run_time=run_time)

    @contextmanager
    def voice(self, key):
        seg = self.timing[key]
        start = self.renderer.time
        # Scene.add_sound drops the sound whenever the previous animation came from Manim's
        # render cache, so the narration goes straight to the file writer.
        self.renderer.file_writer.add_sound(str(Path(self.timing_file).with_name(seg["file"])), start)
        for s in seg["sentences"]:
            self.captions += cues(start + s["start"], start + s["end"], s["text"])
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
