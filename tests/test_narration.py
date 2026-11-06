"""Word cues and speech overruns with a fake scene clock."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from explainer import narration
from explainer.narration import Narration, NarrationMixin


class ClockScene:
    engine = "qwen"
    voice = "Ellis"
    speed = 1.0

    def __init__(self, time=10.0):
        self.renderer = SimpleNamespace(time=time)
        self.waits = []
        self.warnings = []
        self._lint = SimpleNamespace(warn=lambda key, message: self.warnings.append((key, message)),
                                     check_span=lambda: None)
        self._beats = []
        self._line = None
        self.mobjects = [object()]

    def wait(self, seconds):
        self.waits.append(seconds)
        self.renderer.time += seconds

    def add_sound(self, path):
        self.sound = path


def passage(scene):
    return Narration(scene, "First word, then word.", 10.0, 5.0, [
        {"word": "First", "start": 0.1, "end": 0.6},
        {"word": "word,", "start": 1.5, "end": 1.9},
        {"word": "then", "start": 2.2, "end": 2.6},
        {"word": "word.", "start": 3.25, "end": 3.7},
    ])


def test_wait_until_waits_only_until_measured_word_start():
    scene = ClockScene(time=10.5)
    passage(scene).wait_until("WORD")
    assert scene.waits == [1.0]
    assert scene.renderer.time == 11.5 and not scene.warnings


def test_repeated_word_occurrence_uses_its_own_timestamp():
    scene = ClockScene(time=11.5)
    line = passage(scene)
    assert line.time_of("word", occurrence=2) == 3.25
    line.wait_until("word", occurrence=2)
    assert scene.waits == [1.75]
    assert scene.renderer.time == 13.25


@pytest.mark.parametrize("time", [11.5, 11.7])
def test_on_time_or_slightly_late_cue_does_not_wait_or_warn(time):
    scene = ClockScene(time=time)
    passage(scene).wait_until("word")
    assert not scene.waits and not scene.warnings


def test_late_cue_warns_without_rewinding_clock():
    scene = ClockScene(time=12.0)
    passage(scene).wait_until("word")
    assert not scene.waits and scene.renderer.time == 12.0
    assert scene.warnings[0][0] == ("late-cue", 10.0, "word", 1)
    assert "0.50s late" in scene.warnings[0][1]


def test_missing_occurrence_fails_instead_of_mistiming_animation():
    with pytest.raises(ValueError, match="occurrence 3"):
        passage(ClockScene()).wait_until("word", occurrence=3)


@pytest.mark.parametrize("finish,overrun,wait", [(11.5, False, 0.62), (12.2, False, 0), (12.6, True, 0)])
def test_passage_completion_waits_or_reports_animation_overrun(monkeypatch, finish, overrun, wait):
    scene = ClockScene()
    meta = {"text": "Watch this.", "duration": 2.0,
            "words": [{"word": "Watch", "start": 0, "end": 0.7},
                      {"word": "this.", "start": 1, "end": 1.5}]}
    monkeypatch.setattr(narration, "synthesize", lambda *args, **kwargs: (Path("speech.wav"), meta))
    monkeypatch.setattr(narration, "visible", lambda m: True)

    with NarrationMixin.narrate(scene, "Watch this."):
        scene.renderer.time = finish

    overrun_warnings = [message for key, message in scene.warnings if key[0] == "overrun"]
    assert bool(overrun_warnings) is overrun
    if overrun:
        assert "0.60s after speech" in overrun_warnings[0]
    assert sum(scene.waits) == pytest.approx(wait)
    assert scene._line is None
    assert scene._beats[0]["settled"] == max(finish, 12.0)
