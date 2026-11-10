"""Speech contracts without model downloads or GPU work."""

import json
from importlib.metadata import PackageNotFoundError
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from explainer import tts


def lexicon(entries):
    Path("pronunciations.json").write_text(json.dumps(entries))


def test_pronunciations_use_longest_term_case_and_word_boundaries():
    lexicon({"SQL": "sequel", "SQL query": "database request", "API": "A P I"})
    text = "SQL query, sql; SQLquery PostgreSQL API."
    display, speech = tts.prepare_text(text)
    assert display == text
    assert speech == "database request, sequel; SQLquery PostgreSQL A P I."


def test_dictionary_replacements_do_not_cascade():
    lexicon({"API": "interface", "interface": "connection"})
    assert tts.prepare_text("API interface.") == ("API interface.", "interface connection.")


def test_spoken_alias_and_override_leave_captions_readable():
    assert tts.prepare_text("Use [SQL](sequel).") == ("Use SQL.", "Use sequel.")
    assert tts.prepare_text("The API responds.", spoken="The A P I responds.") == (
        "The API responds.", "The A P I responds.",
    )


def test_kokoro_phonemes_require_kokoro():
    text = "[Kokoro](/kˈOkəɹO/) speaks."
    with pytest.raises(ValueError, match="Kokoro phonemes require"):
        tts.prepare_text(text)
    assert tts.prepare_text(text, engine="kokoro") == ("Kokoro speaks.", text)


@pytest.mark.parametrize("entries", [[], "SQL", {"": "sequel"}, {"SQL": " "}, {"SQL": 12}])
def test_malformed_dictionary_is_rejected(entries):
    lexicon(entries)
    with pytest.raises(ValueError, match="expected an object"):
        tts.prepare_text("SQL.")


def test_invalid_dictionary_json_is_rejected():
    Path("pronunciations.json").write_text('{"SQL":')
    with pytest.raises(json.JSONDecodeError):
        tts.prepare_text("SQL.")


def test_explicit_dictionary_must_exist(monkeypatch):
    monkeypatch.setenv("EXPLAINER_PRONUNCIATIONS", "missing.json")
    with pytest.raises(FileNotFoundError):
        tts.prepare_text("SQL.")


def test_explicit_dictionary_path_overrides_project_dictionary(tmp_path, monkeypatch):
    lexicon({"SQL": "wrong"})
    external = tmp_path / "custom.json"
    external.write_text('{"SQL": "sequel"}')
    monkeypatch.setenv("EXPLAINER_PRONUNCIATIONS", str(external))
    assert tts.prepare_text("SQL.") == ("SQL.", "sequel.")


def test_offline_model_resolution_uses_only_cached_pinned_revision(tmp_path, monkeypatch):
    import huggingface_hub

    calls = []

    def snapshot(repo, **kwargs):
        calls.append((repo, kwargs))
        return str(tmp_path)

    monkeypatch.setenv("EXPLAINER_OFFLINE", "1")
    monkeypatch.setenv("HF_HUB_OFFLINE", "0")
    monkeypatch.setenv("TRANSFORMERS_OFFLINE", "0")
    monkeypatch.setattr(huggingface_hub, "snapshot_download", snapshot)
    assert tts._model_path("test/model", "pinned-revision") == tmp_path
    assert calls == [("test/model", {"revision": "pinned-revision", "local_files_only": True})]


def item(text, start, end):
    return SimpleNamespace(text=text, start_time=start, end_time=end)


def test_alignment_preserves_caption_punctuation_and_hyphens():
    result = tts._aligned_words(
        "Twenty-three SQL queries, done!",
        [item("Twentythree", 0.1, 0.5), item("SQL", 0.6, 1.0),
         item("queries", 1.1, 1.5), item("done", 1.7, 2.2)],
        2.5,
    )
    assert [w["word"] for w in result] == ["Twenty-three", "SQL", "queries,", "done!"]
    assert result[0]["start"] == 0.1 and result[-1]["end"] == 2.2


@pytest.mark.parametrize("text,expected", [
    ("The cost is $ 5.", "The cost is $5."),
    ('He said " hello "', 'He said "hello"'),
    ("( One )", "(One)"),
])
def test_alignment_preserves_standalone_openers_and_quotes(text, expected):
    from explainer.render import _join

    tokens = [t for t in text.split() if any(c.isalnum() for c in t)]
    aligned = [item(t, i * 0.2, i * 0.2 + 0.1) for i, t in enumerate(tokens)]
    assert _join(tts._aligned_words(text, aligned, 2)) == expected


@pytest.mark.parametrize("aligned", [[], [item("different", 0, 1)],
                                      [item("one", 0, 1), item("extra", 1, 2)]])
def test_alignment_must_match_caption_words(aligned):
    with pytest.raises(ValueError, match="did not match"):
        tts._aligned_words("One.", aligned, 2)


@pytest.mark.parametrize("aligned", [
    [item("one", float("nan"), 0.5)],
    [item("one", 0, float("inf"))],
    [item("one", 0.5, 0.4)],
    [item("one", -0.5, 0.4)],
    [item("one", 0, 0)],
])
def test_invalid_alignment_timestamps_fail(aligned):
    with pytest.raises(ValueError, match="timestamps"):
        tts._aligned_words("One.", aligned, 1)


def test_alignment_stays_monotonic_with_small_timestamp_overlap():
    words = tts._aligned_words("One two.", [item("one", 0, 0.5), item("two", 0.49, 0.495)], 1)
    assert all(0 <= w["start"] <= w["end"] <= 1 for w in words)
    assert words[1]["start"] >= words[0]["end"]


@pytest.fixture
def fake_speech(tmp_path, monkeypatch):
    """Use real WAV/cache I/O with deterministic CPU-only engine stubs."""
    calls = []
    monkeypatch.setattr(tts, "CACHE_DIR", tmp_path / "narration")
    monkeypatch.setattr(tts.Path, "home", classmethod(lambda cls: tmp_path))
    monkeypatch.setattr(tts, "version", lambda name: "test-1")

    def qwen(text, voice):
        calls.append(("qwen", text, voice))
        return np.zeros(2400, dtype=np.float32), 24000

    def kokoro(text, voice, speed):
        calls.append(("kokoro", text, voice, speed))
        return np.zeros(2400, dtype=np.float32), 24000, [{"word": text, "start": 0, "end": 0.1}]

    def align(wav, text, duration):
        calls.append(("align", text))
        return [{"word": text, "start": 0, "end": duration}]

    monkeypatch.setattr(tts, "_qwen", qwen)
    monkeypatch.setattr(tts, "_kokoro", kokoro)
    monkeypatch.setattr(tts, "_align", align)
    return calls


@pytest.mark.parametrize("options", [{"engine": "qwen", "voice": "Ellis"},
                                     {"engine": "kokoro", "voice": "af_heart"}])
def test_speech_is_stereo_with_the_voice_in_both_ears(fake_speech, monkeypatch, options):
    """Some players send a mono file to the left ear only."""
    import soundfile as sf

    tone = np.sin(np.linspace(0, 200, 2400)).astype(np.float32)
    monkeypatch.setattr(tts, "_qwen", lambda *args: (tone, 24000))
    monkeypatch.setattr(tts, "_kokoro", lambda *args: (tone, 24000, [{"word": "Hello.", "start": 0, "end": 0.1}]))
    wav, _ = tts.synthesize("Hello.", speed=1.0, **options)
    audio, _ = sf.read(wav)
    assert audio.shape == (2400, 2)
    assert np.array_equal(audio[:, 0], audio[:, 1]) and np.abs(audio).max() > 0.5


def test_cloned_speech_starts_after_a_fixed_short_pause(fake_speech, monkeypatch):
    import soundfile as sf

    tone = np.sin(np.linspace(0, 2000, 24000)).astype(np.float32)
    monkeypatch.setattr(tts, "_qwen", lambda *args: (np.concatenate([np.zeros(12000, np.float32), tone]), 24000))
    wav, meta = tts.synthesize("Hello.", engine="qwen", voice="Ellis", speed=1.0)
    audio, _ = sf.read(wav)
    first = np.flatnonzero(np.abs(audio[:, 0]) > 0.01)[0] / 24000
    assert first == pytest.approx(0.08, abs=0.002)
    assert meta["duration"] == pytest.approx(1.08, abs=0.002)


def test_cache_hit_skips_synthesis_and_alignment(fake_speech):
    wav, meta = tts.synthesize("Hello.", engine="qwen", voice="Ellis", speed=1.0)
    first_calls = list(fake_speech)
    cached_wav, cached_meta = tts.synthesize("Hello.", engine="qwen", voice="Ellis", speed=1.0)
    assert cached_wav == wav and cached_meta == meta
    assert fake_speech == first_calls
    assert [call[0] for call in first_calls] == ["qwen", "align"]
    assert wav.is_file() and meta["duration"] == pytest.approx(0.1)


def test_qwen_default_uses_bundled_narrator(fake_speech, monkeypatch):
    monkeypatch.delenv("EXPLAINER_VOICE", raising=False)
    _, meta = tts.synthesize("Hello.", engine="qwen")
    assert meta["voice"] == "Ellis" and meta["speed"] == 1.3
    assert fake_speech[0] == ("qwen", "Hello.", "Ellis")


def test_every_bundled_voice_has_a_transcript():
    assert "Ellis" in tts.QWEN_VOICES
    for voice in tts.QWEN_VOICES:
        assert (tts.VOICE_DIR / f"{voice}.txt").read_text().strip()


def test_unknown_qwen_voice_names_the_available_voices(fake_speech):
    with pytest.raises(ValueError, match="Unknown Qwen voice 'Aiden'. Voices: Ellis"):
        tts.synthesize("Hello.", engine="qwen", voice="Aiden")
    assert not fake_speech


def test_missing_package_metadata_has_actionable_error(fake_speech, monkeypatch):
    def missing_version(name):
        raise PackageNotFoundError(name)

    monkeypatch.setattr(tts, "version", missing_version)
    with pytest.raises(RuntimeError, match="explainer doctor"):
        tts.synthesize("Hello.", engine="qwen", voice="Ellis")
    assert not fake_speech


@pytest.mark.parametrize("changed", [{"voice": "af_heart", "engine": "kokoro"}, {"spoken": "Hi."}])
def test_cache_invalidates_changed_voice_or_spoken_text(fake_speech, changed):
    options = {"engine": "qwen", "voice": "Ellis"}
    first, _ = tts.synthesize("Hello.", **options)
    second, meta = tts.synthesize("Hello.", **(options | changed))
    assert first != second
    assert meta["text"] == "Hello."
    assert meta["words"][0]["word"] == "Hello."


@pytest.mark.parametrize("suffix", [".wav", ".txt"])
def test_cache_invalidates_changed_reference_clip(fake_speech, tmp_path, monkeypatch, suffix):
    voices = tmp_path / "voices"
    voices.mkdir()
    for f in tts.VOICE_DIR.glob("Ellis.*"):
        (voices / f.name).write_bytes(f.read_bytes())
    monkeypatch.setattr(tts, "VOICE_DIR", voices)
    first, _ = tts.synthesize("Hello.", engine="qwen", voice="Ellis")
    with (voices / f"Ellis{suffix}").open("ab") as f:
        f.write(b" ")
    second, _ = tts.synthesize("Hello.", engine="qwen", voice="Ellis")
    assert first != second


def test_cache_invalidates_model_and_aligner_revisions(fake_speech, monkeypatch):
    first, _ = tts.synthesize("Hello.", engine="qwen", voice="Ellis")
    monkeypatch.setattr(tts, "QWEN_REVISION", "another-model")
    second, _ = tts.synthesize("Hello.", engine="qwen", voice="Ellis")
    monkeypatch.setattr(tts, "ALIGN_REVISION", "another-aligner")
    third, _ = tts.synthesize("Hello.", engine="qwen", voice="Ellis")
    assert len({first, second, third}) == 3


def test_cache_invalidates_engine_package_version(fake_speech, monkeypatch):
    first, _ = tts.synthesize("Hello.", engine="qwen", voice="Ellis")
    monkeypatch.setattr(tts, "version", lambda name: "test-2")
    second, _ = tts.synthesize("Hello.", engine="qwen", voice="Ellis")
    assert first != second


def test_cache_separates_engines(fake_speech):
    qwen, qwen_meta = tts.synthesize("Hello.", engine="qwen", voice="Ellis")
    kokoro, kokoro_meta = tts.synthesize("Hello.", engine="kokoro", voice="af_heart")
    assert qwen != kokoro
    assert qwen_meta["engine"] == "qwen" and kokoro_meta["engine"] == "kokoro"
    assert [call[0] for call in fake_speech] == ["qwen", "align", "kokoro"]


def test_existing_kokoro_voice_keeps_its_engine(fake_speech, monkeypatch):
    monkeypatch.setattr(tts, "DEFAULT_ENGINE", "qwen")
    _, meta = tts.synthesize("Hello.", voice="af_heart")
    assert meta["engine"] == "kokoro" and meta["voice"] == "af_heart"
    assert [call[0] for call in fake_speech] == ["kokoro"]


def test_legacy_kokoro_phonemes_keep_native_word_timing(fake_speech, monkeypatch):
    native_words = [{"word": "Kokoro", "start": 0, "end": 0.05},
                    {"word": "speaks.", "start": 0.05, "end": 0.1}]
    monkeypatch.setattr(tts, "_kokoro", lambda *args: (np.zeros(2400), 24000, native_words))

    def unexpected_alignment(*args):
        raise AssertionError("Kokoro phonemes already have readable word timing")

    monkeypatch.setattr(tts, "_align", unexpected_alignment)
    _, meta = tts.synthesize("[Kokoro](/kˈOkəɹO/) speaks.", engine="kokoro", voice="af_heart")
    assert meta["text"] == "Kokoro speaks." and meta["words"] == native_words


def test_kokoro_speed_changes_invalidate_cache(fake_speech):
    first, _ = tts.synthesize("Hello.", engine="kokoro", voice="af_heart", speed=1)
    second, _ = tts.synthesize("Hello.", engine="kokoro", voice="af_heart", speed=1.2)
    assert first != second


@pytest.mark.parametrize("speed", [0, -1, float("nan"), float("inf"), 2.1])
def test_invalid_speed_fails_before_synthesis(fake_speech, speed):
    with pytest.raises(ValueError, match="Speech speed"):
        tts.synthesize("Hello.", engine="qwen", speed=speed)
    assert not fake_speech


def test_dictionary_change_invalidates_cache_without_changing_captions(fake_speech):
    lexicon({"SQL": "sequel"})
    first, _ = tts.synthesize("SQL.", engine="qwen", voice="Ellis")
    lexicon({"SQL": "S Q L"})
    second, meta = tts.synthesize("SQL.", engine="qwen", voice="Ellis")
    assert first != second and meta["text"] == "SQL." and meta["spoken"] == "S Q L."


def test_missing_metadata_regenerates_incomplete_cache(fake_speech):
    wav, _ = tts.synthesize("Hello.", engine="qwen", voice="Ellis")
    wav.with_suffix(".json").unlink()
    regenerated, _ = tts.synthesize("Hello.", engine="qwen", voice="Ellis")
    assert regenerated == wav
    assert [call[0] for call in fake_speech].count("qwen") == 2


@pytest.mark.parametrize("audio", [np.array([], dtype=np.float32), np.array([float("nan")])])
def test_invalid_audio_never_populates_cache(fake_speech, monkeypatch, audio):
    monkeypatch.setattr(tts, "_qwen", lambda *args: (audio, 24000))
    with pytest.raises(ValueError, match="empty or invalid audio"):
        tts.synthesize("Hello.", engine="qwen", voice="Ellis")
    assert not list(tts.CACHE_DIR.glob("*.wav"))
    assert not list(tts.CACHE_DIR.glob("*.json"))
