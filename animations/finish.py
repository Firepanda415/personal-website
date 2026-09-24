"""Encode a rendered explainer for the website and write its poster and captions.

Usage: python finish.py <rendered.mp4> <captions.json> <site stem, e.g. ../explainers/lchs> <poster.png>
"""
import json
import subprocess
import sys
from pathlib import Path

FFMPEG = str(Path(sys.executable).with_name("ffmpeg"))
MAX_WORDS = 14


def stamp(t):
    m, s = divmod(t, 60)
    return f"{int(m // 60):02d}:{int(m % 60):02d}:{s:06.3f}"


def cues(captions):
    """Split each narrated sentence into short cues, timed in proportion to their length."""
    for start, end, text in captions:
        words = text.split()
        n = -(-len(words) // MAX_WORDS)
        size = -(-len(words) // n)
        chunks = [" ".join(words[i:i + size]) for i in range(0, len(words), size)]
        total = sum(len(c) for c in chunks)
        t = start
        for c in chunks:
            dt = (end - start) * len(c) / total
            yield t, t + dt, c
            t += dt


def main(rendered, captions, stem, poster):
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    video = stem.with_suffix(".mp4")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", rendered,
                    "-c:v", "libx264", "-preset", "slow", "-crf", "24", "-tune", "animation", "-pix_fmt", "yuv420p",
                    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
                    "-movflags", "+faststart", str(video)], check=True)
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", poster, "-vf", "scale=640:-2", "-q:v", "3",
                    str(stem.with_suffix(".jpg"))], check=True)
    lines = ["WEBVTT", ""]
    for i, (a, b, text) in enumerate(cues(json.loads(Path(captions).read_text())), 1):
        lines += [str(i), f"{stamp(a)} --> {stamp(b)}", text, ""]
    stem.with_suffix(".vtt").write_text("\n".join(lines))
    probe = subprocess.run([FFMPEG, "-i", str(video)], capture_output=True, text=True).stderr
    duration = probe.split("Duration: ")[1].split(",")[0]
    h, m, s = duration.split(":")
    total = round(int(h) * 3600 + int(m) * 60 + float(s))
    print(f"{video}: {video.stat().st_size / 1e6:.1f} MB, {total // 60}:{total % 60:02d}")


if __name__ == "__main__":
    main(*sys.argv[1:5])
