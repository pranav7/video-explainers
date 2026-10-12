"""Local Kokoro text-to-speech, cached by text, voice and speed."""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path

SAMPLE_RATE = 24000
DEFAULT_VOICE = os.environ.get("EXPLAINER_VOICE", "af_heart")
DEFAULT_SPEED = float(os.environ.get("EXPLAINER_SPEED", "1.0"))
CACHE_DIR = Path(os.environ.get("EXPLAINER_TTS_CACHE", "media/narration"))
VOICES = ["af_heart", "af_bella", "am_michael", "am_fenrir", "bf_emma", "bm_george", "bm_fable"]

_pipelines: dict[str, object] = {}

# Manim's log handler shows every Hugging Face download request at INFO.
logging.getLogger("httpx").setLevel(logging.WARNING)


def _pipeline(lang_code: str):
    if lang_code not in _pipelines:
        # The espeak-ng build bundled in espeakng-loader ignores the data path it
        # is given on macOS and exits the process. Use Homebrew's build instead.
        import espeakng_loader

        prefix = os.environ.get("ESPEAK_PREFIX", "/opt/homebrew/opt/espeak-ng")
        espeakng_loader.get_library_path = lambda: f"{prefix}/lib/libespeak-ng.dylib"
        espeakng_loader.get_data_path = lambda: f"{prefix}/share/espeak-ng-data"

        from kokoro import KPipeline

        _pipelines[lang_code] = KPipeline(lang_code=lang_code, repo_id="hexgrad/Kokoro-82M")
    return _pipelines[lang_code]


def synthesize(text: str, voice: str = DEFAULT_VOICE, speed: float = DEFAULT_SPEED) -> tuple[Path, dict]:
    """Return (wav path, metadata). Metadata has the duration and a timestamp for each word.

    Results are cached by (text, voice, speed), so re-renders do not re-synthesize.
    """
    key = hashlib.sha256(f"{voice}|{speed}|{text}".encode()).hexdigest()[:16]
    wav, meta_path = CACHE_DIR / f"{key}.wav", CACHE_DIR / f"{key}.json"
    if wav.exists() and meta_path.exists():
        return wav, json.loads(meta_path.read_text())

    import numpy as np
    import soundfile as sf

    # Kokoro voice names start with the language code: a = US English, b = UK English.
    pipeline = _pipeline(voice[0])
    chunks, words, offset = [], [], 0.0
    for result in pipeline(text, voice=voice, speed=speed):
        audio = result.audio.numpy()
        for token in result.tokens or []:
            if token.start_ts is not None:
                words.append({"word": token.text, "start": offset + token.start_ts, "end": offset + token.end_ts})
        chunks.append(audio)
        offset += len(audio) / SAMPLE_RATE

    if not chunks:
        raise ValueError(f"Kokoro produced no speech for {text!r}: narration needs words")
    # Scenes render in parallel, so write to a temporary name and rename.
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = f".{os.getpid()}.tmp"
    sf.write(f"{wav}{tmp}", np.concatenate(chunks), SAMPLE_RATE, format="WAV")
    meta = {"text": text, "voice": voice, "speed": speed, "duration": offset, "words": words}
    Path(f"{meta_path}{tmp}").write_text(json.dumps(meta, indent=1))
    os.replace(f"{wav}{tmp}", wav)
    os.replace(f"{meta_path}{tmp}", meta_path)
    return wav, meta
