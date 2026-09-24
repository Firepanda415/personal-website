"""Burn subtitles into a rendered explainer, encode it for the website, and write its poster.

Usage: python finish.py <rendered.mp4> <cues.json> <site stem, e.g. ../explainers/lchs> <poster.png>
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import ImageFont

FFMPEG = str(Path(sys.executable).with_name("ffmpeg"))
FONTS = Path(__file__).resolve().parent / "fonts"
HOLD = 0.8  # seconds a line stays up into a pause before the next line
SUB_PX, MAX_LINE_PX = 46, 1760  # subtitle font size and widest line, in 1080p pixels
SUB_FONT = ImageFont.truetype(str(FONTS / "IBMPlexSans-Regular.ttf"), SUB_PX)
# The subtitle strip is the bottom 0.9 of 8.9 frame units (house_style.CAPTION_BAND).
BAND_CENTER_Y = round(1080 * (1 - 0.45 / 8.9))

ASS_HEAD = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,IBM Plex Sans,{SUB_PX},&H002D2B24,&H00000000,&H00000000,0,0,1,0,0,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def stamp(t):
    cs = round(t * 100)
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def fit_width(cues):
    """Split any subtitle line wider than the frame into balanced pieces timed by length."""
    out = []
    for start, end, text in cues:
        words, n = text.split(), 1
        while True:
            target = SUB_FONT.getlength(text) / n
            chunks, current = [], []
            for w in words:
                if current and SUB_FONT.getlength(" ".join(current + [w])) > target * 1.08 and len(chunks) < n - 1:
                    chunks.append(" ".join(current))
                    current = []
                current.append(w)
            chunks.append(" ".join(current))
            if all(SUB_FONT.getlength(c) <= MAX_LINE_PX for c in chunks):
                break
            n += 1
        total, t = sum(len(c) for c in chunks), start
        for c in chunks:
            dt = (end - start) * len(c) / total
            out.append((t, t + dt, c))
            t += dt
    return out


def write_ass(cues, path):
    lines = [ASS_HEAD]
    for i, (a, b, text) in enumerate(cues):
        end = min(b + HOLD, cues[i + 1][0]) if i + 1 < len(cues) else b + HOLD
        lines.append(f"Dialogue: 0,{stamp(a)},{stamp(end)},Sub,,0,0,0,,{{\\pos(960,{BAND_CENTER_Y})}}{text}\n")
    path.write_text("".join(lines))


def check_narration(video, cues, floor_db=-40):
    """Fail if any subtitle line has no narration under it."""
    pcm = subprocess.run([FFMPEG, "-loglevel", "error", "-i", str(video), "-vn", "-ac", "1", "-ar", "8000",
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    audio = np.frombuffer(pcm, dtype=np.float32)
    silent = [(round(a, 1), text) for a, b, text in cues
              if 20 * np.log10(np.sqrt(np.mean(audio[int(a * 8000):int(b * 8000)] ** 2)) + 1e-9) < floor_db]
    if silent:
        raise SystemExit(f"{len(silent)} subtitle lines have no narration, first at {silent[0]}")


def main(rendered, cues, stem, poster):
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    video = stem.with_suffix(".mp4")
    ass = Path(cues).with_suffix(".ass")
    cues = json.loads(Path(cues).read_text())
    write_ass(fit_width(cues), ass)
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", rendered, "-vf", f"subtitles={ass}:fontsdir={FONTS}",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "24", "-tune", "animation", "-pix_fmt", "yuv420p",
                    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
                    "-movflags", "+faststart", str(video)], check=True)
    check_narration(video, cues)
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", poster, "-vf", "scale=640:-2", "-q:v", "3",
                    str(stem.with_suffix(".jpg"))], check=True)
    probe = subprocess.run([FFMPEG, "-i", str(video)], capture_output=True, text=True).stderr
    duration = probe.split("Duration: ")[1].split(",")[0]
    h, m, s = duration.split(":")
    total = round(int(h) * 3600 + int(m) * 60 + float(s))
    print(f"{video}: {video.stat().st_size / 1e6:.1f} MB, {total // 60}:{total % 60:02d}")


if __name__ == "__main__":
    main(*sys.argv[1:5])
