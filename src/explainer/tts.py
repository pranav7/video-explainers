"""Local speech, with cached audio and word alignment.

The qwen engine clones a bundled narrator voice with Qwen3-TTS on MLX. The kokoro engine uses Kokoro.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import logging
import math
import os
import re
import subprocess
import tempfile
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

DEFAULT_ENGINE = os.environ.get("EXPLAINER_ENGINE", "qwen")
# Ellis reads with long pauses. At 1.3 times his own pace he is brisk but natural.
DEFAULT_SPEED = float(os.environ.get("EXPLAINER_SPEED", "1.3"))
CACHE_DIR = Path(os.environ.get("EXPLAINER_TTS_CACHE", "media/narration"))
KOKORO_VOICES = ["af_heart", "af_bella", "am_michael", "am_fenrir", "bf_emma", "bm_george", "bm_fable"]
# Each Qwen voice is a reference clip, <name>.wav, with its transcript, <name>.txt. See voices/README.md.
VOICE_DIR = Path(__file__).parent / "voices"
QWEN_VOICES = sorted(p.stem for p in VOICE_DIR.glob("*.wav"))
QWEN_VOICE = "Ellis"
QWEN_MODEL = "mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16"
QWEN_REVISION = "a6eb4f68e4b056f1215157bb696209bc82a6db48"
ALIGN_MODEL = "mlx-community/Qwen3-ForcedAligner-0.6B-8bit"
ALIGN_REVISION = "0e1a68e91d815300c7c9754b2a7639378b23db15"
_models: dict[str, object] = {}
_pipelines: dict[str, object] = {}
_ALIAS = re.compile(r"\[([^\]\n]+)\]\(([^)\n]+)\)")
logging.getLogger("httpx").setLevel(logging.WARNING)


def _offline() -> bool:
    return os.environ.get("EXPLAINER_OFFLINE", "").lower() in {"1", "true", "yes"}


def resolve_engine(voice: str | None = None, engine: str | None = None) -> str:
    """Keep explicit engine choices and recognize legacy Kokoro voice overrides."""
    voice = voice or os.environ.get("EXPLAINER_VOICE")
    return engine or ("kokoro" if voice and re.fullmatch(r"[ab][fm]_\w+", voice) else DEFAULT_ENGINE)


def _model_path(repo: str, revision: str) -> Path:
    if _offline():
        os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    from huggingface_hub import snapshot_download
    from huggingface_hub.errors import LocalEntryNotFoundError

    try:
        return Path(snapshot_download(repo, revision=revision, local_files_only=True))
    except LocalEntryNotFoundError as error:
        if _offline():
            raise RuntimeError(f"Local model {repo} is incomplete. Run `explainer models` online once, then retry offline.") from error
        return Path(snapshot_download(repo, revision=revision))


def setup_models() -> None:
    """Download pinned speech and alignment weights. Inference uses local paths."""
    for repo, revision in ((QWEN_MODEL, QWEN_REVISION), (ALIGN_MODEL, ALIGN_REVISION)):
        print(_model_path(repo, revision))


def prepare_text(text: str, spoken: str | None = None, engine: str = "qwen") -> tuple[str, str]:
    """Separate caption text from spoken aliases and the project pronunciation dictionary."""
    display = _ALIAS.sub(lambda m: m[1], text)
    source = text if spoken is None else spoken

    def alias(match):
        value = match[2]
        if value.startswith("/") and value.endswith("/"):
            if engine != "kokoro":
                raise ValueError("Kokoro phonemes require --engine kokoro; use a spoken spelling for Qwen")
            return match[0]
        return value

    source = _ALIAS.sub(alias, source)
    lexicon = Path(os.environ.get("EXPLAINER_PRONUNCIATIONS", "pronunciations.json"))
    if lexicon.exists() or "EXPLAINER_PRONUNCIATIONS" in os.environ:
        entries = json.loads(lexicon.read_text())
        if not isinstance(entries, dict) or any(
            not isinstance(k, str) or not k.strip() or not isinstance(v, str) or not v.strip()
            for k, v in entries.items()
        ):
            raise ValueError(f"{lexicon}: expected an object of nonempty term: spoken spelling strings")
        if entries:
            replacements = {k.casefold(): v for k, v in entries.items()}
            pattern = r"(?<!\w)(?:" + "|".join(re.escape(k) for k in sorted(entries, key=len, reverse=True)) + r")(?!\w)"
            source = re.sub(pattern, lambda m: replacements[m[0].casefold()], source, flags=re.IGNORECASE)
    if not any(c.isalnum() for c in source):
        raise ValueError("narration needs words")
    return display, source


def _pipeline(lang_code: str):
    if lang_code not in _pipelines:
        import espeakng_loader

        prefix = os.environ.get("ESPEAK_PREFIX", "/opt/homebrew/opt/espeak-ng")
        espeakng_loader.get_library_path = lambda: f"{prefix}/lib/libespeak-ng.dylib"
        espeakng_loader.get_data_path = lambda: f"{prefix}/share/espeak-ng-data"
        if _offline():
            os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
        from kokoro import KPipeline

        _pipelines[lang_code] = KPipeline(lang_code=lang_code, repo_id="hexgrad/Kokoro-82M")
    return _pipelines[lang_code]


def _kokoro(text: str, voice: str, speed: float):
    import numpy as np

    chunks, words, offset = [], [], 0.0
    for result in _pipeline(voice[0])(text, voice=voice, speed=speed):
        audio = result.audio.numpy()
        for token in result.tokens or []:
            if token.start_ts is not None and token.end_ts is not None:
                words.append({"word": token.text, "start": offset + token.start_ts, "end": offset + token.end_ts})
        chunks.append(audio)
        offset += len(audio) / 24000
    if not chunks:
        raise ValueError(f"Kokoro produced no speech for {text!r}")
    return np.concatenate(chunks), 24000, words


def _qwen(text: str, voice: str):
    import numpy as np
    try:
        from mlx_audio.tts.utils import load_model
    except ImportError as error:
        raise RuntimeError("Qwen requires Apple Silicon and MLX. Run `explainer doctor`, or use --engine kokoro.") from error

    if "qwen" not in _models:
        _models["qwen"] = load_model(_model_path(QWEN_MODEL, QWEN_REVISION))
    # The clone takes its timbre, pace and intonation from the reference clip.
    reference = VOICE_DIR / f"{voice}.wav"
    results = list(_models["qwen"].generate(
        text=text, ref_audio=str(reference), ref_text=reference.with_suffix(".txt").read_text().strip(),
        lang_code="english", verbose=False,
    ))
    if not results:
        raise ValueError("Qwen produced no speech")
    return np.concatenate([np.asarray(r.audio) for r in results]), results[0].sample_rate


def _trim_lead(audio, rate: int):
    """Start 80 ms before the first sound. A cloned voice begins after a pause of 0.3 to 0.7 s
    that varies from take to take; trimming it lets `gap` alone set the pause between passages."""
    import numpy as np

    sound = np.flatnonzero(np.abs(audio) > np.abs(audio).max() / 100)
    if not len(sound):
        return audio
    return audio[max(0, sound[0] - int(0.08 * rate)):]


def _aligned_words(text: str, items, duration: float) -> list[dict]:
    """Restore English caption punctuation without changing measured timestamps."""
    tokens, prefix, quote_open = [], "", False
    for token in text.split():
        if any(c.isalnum() for c in token):
            tokens.append(prefix + token)
            prefix = ""
        elif token in {"(", "[", "{", "$", "£", "€", "\u201c", "\u2018"} or (token == '"' and not quote_open):
            prefix += token
            if token == '"':
                quote_open = True
        elif tokens:
            tokens[-1] += token
            if token == '"':
                quote_open = False
    items = list(items)
    norm = lambda s: "".join(c for c in s.casefold() if c.isalnum())
    if len(tokens) != len(items) or any(norm(t) != norm(i.text) for t, i in zip(tokens, items)):
        raise ValueError("Word alignment did not match the caption text; use plain English narration")
    words, previous = [], 0.0
    for token, item in zip(tokens, items):
        start, end = float(item.start_time), float(item.end_time)
        if not math.isfinite(start) or not math.isfinite(end) or end < start or start < previous - 0.02:
            raise ValueError("Word alignment returned invalid timestamps")
        start = min(max(start, previous), duration)
        end = min(max(end, start), duration)
        words.append({"word": token, "start": start, "end": end})
        previous = end
    if not words or all(w["start"] == w["end"] for w in words):
        raise ValueError("Word alignment produced no usable timestamps")
    return words


def _align(wav: Path, text: str, duration: float) -> list[dict]:
    from mlx_audio.stt.utils import load_model

    if "align" not in _models:
        _models["align"] = load_model(_model_path(ALIGN_MODEL, ALIGN_REVISION))
    result = _models["align"].generate(audio=str(wav), text=text, language="English")
    return _aligned_words(text, result, duration)


def synthesize(text: str, voice: str | None = None, speed: float | None = None, *,
               engine: str | None = None, spoken: str | None = None) -> tuple[Path, dict]:
    """Return cached stereo WAV and metadata. Caption text and spoken spellings stay separate.

    `speed` changes tempo. 1.0 is the voice's own pace; the default is DEFAULT_SPEED.
    """
    # Existing scenes with a Kokoro voice keep their narrator after the default changes.
    engine = resolve_engine(voice, engine)
    if engine not in {"qwen", "kokoro"}:
        raise ValueError(f"Unknown speech engine {engine!r}; use qwen or kokoro")
    voice = voice or os.environ.get("EXPLAINER_VOICE") or (QWEN_VOICE if engine == "qwen" else "af_heart")
    if engine == "kokoro" and not re.fullmatch(r"[ab][fm]_\w+", voice):
        raise ValueError("Kokoro needs an English Kokoro voice, such as af_heart or bm_george")
    if engine == "qwen" and voice not in QWEN_VOICES:
        raise ValueError(f"Unknown Qwen voice {voice!r}. Voices: {', '.join(QWEN_VOICES)}")
    speed = DEFAULT_SPEED if speed is None else speed
    if not math.isfinite(speed) or not 0.5 <= speed <= 2.0:
        raise ValueError("Speech speed must be between 0.5 and 2.0")
    display, speech = prepare_text(text, spoken, engine)
    try:
        engine_version = version("mlx-audio" if engine == "qwen" else "kokoro")
    except PackageNotFoundError as error:
        raise RuntimeError("Speech dependencies missing. Run `explainer doctor`; Qwen needs Apple Silicon, or use --engine kokoro.") from error
    # A changed reference clip or transcript is a changed voice.
    reference = ""
    if engine == "qwen":
        clip = VOICE_DIR / f"{voice}.wav"
        reference = hashlib.sha256(clip.read_bytes() + clip.with_suffix(".txt").read_bytes()).hexdigest()[:16]
    settings = {"schema": 3, "engine": engine, "version": engine_version,
                "model": QWEN_REVISION if engine == "qwen" else "Kokoro-82M-v1.0",
                "aligner": ALIGN_REVISION, "text": display, "spoken": speech, "voice": voice,
                "reference": reference, "speed": speed}
    key = hashlib.sha256(json.dumps(settings, sort_keys=True).encode()).hexdigest()[:24]
    wav, meta_path = CACHE_DIR / f"{key}.wav", CACHE_DIR / f"{key}.json"

    def cached():
        if wav.exists() and meta_path.exists():
            return wav, json.loads(meta_path.read_text())

    if hit := cached():
        return hit
    # Parallel scene processes must not load multiple uncached MLX models at once.
    lock = Path.home() / ".cache/video-explainer/synthesis.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        if hit := cached():
            return hit
        import numpy as np
        import soundfile as sf

        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=CACHE_DIR) as tmp:
            audio_path = Path(tmp) / "speech.wav"
            if engine == "qwen":
                audio, rate = _qwen(speech, voice)
                words = None
            else:
                audio, rate, words = _kokoro(speech, voice, speed)
                if speech != text:
                    words = None
            if not len(audio) or not np.isfinite(audio).all():
                raise ValueError("Speech engine produced empty or invalid audio")
            if engine == "qwen":
                audio = _trim_lead(audio, rate)
            sf.write(audio_path, audio, rate)
            if engine == "qwen" and speed != 1.0:
                adjusted = Path(tmp) / "tempo.wav"
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(audio_path),
                                "-af", f"atempo={speed}", str(adjusted)], check=True)
                os.replace(adjusted, audio_path)
            duration = sf.info(audio_path).duration
            if words is None:
                words = _align(audio_path, display, duration)
            # Some players send a mono file to the left ear only. Put the voice in both channels.
            mono, rate = sf.read(audio_path)
            sf.write(audio_path, np.column_stack([mono, mono]), rate)
            meta = {**settings, "duration": duration, "sample_rate": rate, "words": words}
            temp_meta = Path(tmp) / "speech.json"
            temp_meta.write_text(json.dumps(meta, indent=1))
            os.replace(audio_path, wav)
            os.replace(temp_meta, meta_path)
    return wav, meta
