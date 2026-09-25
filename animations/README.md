# Explainer animations

This folder builds the narrated explainer videos shown in the project column of the Projects page, below the project diagram. Each video has its own folder, such as `lchs/`, with the narration, the data it plots, and a [Manim](https://www.manim.community/) scene. Shared pieces sit at this level:

- `house_style.py`: site colors, IBM Plex Sans text, Typst mathematics, narration timing, and burned-in subtitles.
- `tts.py`: speech synthesis with [Kokoro](https://huggingface.co/hexgrad/Kokoro-82M), voice `am_puck` at speed 1.08.
- `finish.py`: web encoding and poster image.
- `render.py`: runs all three steps for one video.

## Setup

```sh
conda env create -f animations/environment.yml
conda activate personal-website-animations
```

The first synthesis downloads the Kokoro-82M model (about 330 MB) from Hugging Face. The fonts in `fonts/` are IBM Plex Sans under the SIL Open Font License (`fonts/OFL.txt`).

## Build a video

```sh
cd animations
python render.py lchs --preview
python render.py lchs
```

The preview writes a 480p check to `build/preview/`. The full build writes a 1080p, 30 fps video to `../explainers/lchs.mp4`, together with a poster image (`.jpg`), and prints the video length. Copy that length into the paper's `explainer.duration` in `data.mjs`. Subtitles are drawn into the video in a strip below the animation, one line per part of a narrated sentence. Synthesis reuses cached audio for unchanged narration segments.

The LCHS scene plots squeezed-Fock coefficients and truncation errors from the CV-DV-LCHS repository. After those results change, refresh the copy with `python lchs/extract_data.py /path/to/CV-DV-LCHS`.

Section 04 of the Bayesian scene repeats the consistent Bayesian inference on the ibm_perth tutorial data in the paper's code repository, which differs from the paper's ibmqx2 experiments. Rebuild `bayesian/data.json` with `python bayesian/extract_data.py /path/to/Bayesian-Error-Characterization-and-Mitigation`.

The QFlow scene plots the water energy profile traced from Fig. 3 of arXiv:2606.04186, because the raw ExaChem output is not published, and reruns the paper's active-space sampling to check the Table 1 cycle sizes. Rebuild `qflow/data.json` with `python qflow/extract_data.py /path/to/arXiv-2606.04186-source`.

## Add a video

1. Write `<id>/narration.py` with `SEGMENTS`, a list of `(key, sentences)` pairs. Each sentence has a caption `text` and, where symbols need spoken words, a `say` string.
2. Write `<id>/scene.py` with a subclass of `Explainer`. Wrap each narrated part in `with self.voice("key") as v:` and call `v.until(i)` to start an animation with sentence `i`.
3. Add the scene class and a poster still scene to `VIDEOS` in `render.py`, then add an `explainer` entry to the paper in `data.mjs`.
