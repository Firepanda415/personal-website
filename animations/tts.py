"""Synthesize narration with Kokoro and record sentence timings.

Each segment becomes one WAV file. Sentences inside a segment are separated by
a short pause, and their start and end times are written to timing.json so the
scene can sync animations and the build can emit WebVTT captions.
Unchanged segments are reused from the cache.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import soundfile as sf

RATE = 24_000
VOICE = "am_puck"
SPEED = 1.08
SENTENCE_GAP = 0.28

_pipeline = None


def _speak(text, voice, speed):
    global _pipeline
    if _pipeline is None:
        from kokoro import KPipeline
        _pipeline = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
    chunks = [np.asarray(audio) for _, _, audio in _pipeline(text, voice=voice, speed=speed, split_pattern=None)]
    return np.concatenate(chunks)


def _trim(audio, threshold=1e-3, pad=0.04):
    """Remove leading and trailing silence, keeping a short pad."""
    loud = np.flatnonzero(np.abs(audio) > threshold)
    if loud.size == 0:
        return audio
    lo = max(loud[0] - int(pad * RATE), 0)
    hi = min(loud[-1] + int(pad * RATE), audio.size)
    return audio[lo:hi]


def synthesize(segments, out_dir, voice=VOICE, speed=SPEED):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    timing_path = out_dir / "timing.json"
    old = json.loads(timing_path.read_text()) if timing_path.exists() else {}
    timing = {}
    for key, sentences in segments:
        spoken = [s.get("say", s["text"]) for s in sentences]
        digest = hashlib.sha256(json.dumps([voice, speed, SENTENCE_GAP, spoken]).encode()).hexdigest()[:16]
        wav = out_dir / f"{key}.wav"
        if key in old and old[key]["hash"] == digest and wav.exists():
            timing[key] = old[key]
            continue
        pieces, spans, t = [], [], 0.0
        gap = np.zeros(int(SENTENCE_GAP * RATE), dtype=np.float32)
        for i, (sentence, say) in enumerate(zip(sentences, spoken)):
            audio = _trim(_speak(say, voice, speed)).astype(np.float32)
            if i:
                pieces.append(gap)
                t += gap.size / RATE
            spans.append({"text": sentence["text"], "start": round(t, 3), "end": round(t + audio.size / RATE, 3)})
            pieces.append(audio)
            t += audio.size / RATE
        sf.write(wav, np.concatenate(pieces), RATE)
        timing[key] = {"hash": digest, "file": wav.name, "duration": round(t, 3), "sentences": spans}
        print(f"{key}: {t:.1f} s")
    timing_path.write_text(json.dumps(timing, indent=1, ensure_ascii=False))
    return timing
