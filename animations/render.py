"""Build a narrated explainer: synthesize speech, render the Manim scene, encode for the site.

Usage: python render.py lchs [--preview]
"""
import importlib
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import tts

# video id: (scene class, poster still scene)
VIDEOS = {"lchs": ("LCHSExplainer", "LCHSPoster"), "downfolding": ("DownfoldingExplainer", "DownfoldingPoster")}


def main(name, preview=False):
    scene, poster = VIDEOS[name]
    segments = importlib.import_module(f"{name}.narration").SEGMENTS
    tts.synthesize(segments, HERE / "build" / name / "audio")
    quality = ["-ql"] if preview else ["-r", "1920,1080", "--fps", "30"]
    manim = Path(sys.executable).with_name("manim")
    subprocess.run([str(manim), *quality, "--media_dir", "build/manim", f"{name}/scene.py", scene], cwd=HERE, check=True)
    subprocess.run([str(manim), "-s", "-r", "1920,1080", "--media_dir", "build/manim", f"{name}/scene.py", poster], cwd=HERE, check=True)
    still = next((HERE / "build" / "manim" / "images" / "scene").glob(f"{poster}_ManimCE_*.png"))
    folder = "480p15" if preview else "1080p30"
    rendered = HERE / "build" / "manim" / "videos" / "scene" / folder / f"{scene}.mp4"
    stem = HERE / "build" / "preview" / name if preview else HERE.parent / "explainers" / name
    cues = HERE / "build" / f"{scene}.captions.json"
    subprocess.run([sys.executable, str(HERE / "finish.py"), str(rendered), str(cues), str(stem), str(still)], check=True)


if __name__ == "__main__":
    main(sys.argv[1], "--preview" in sys.argv[2:])
