"""Narrated Manim scenes: each line of speech sets the timing of its animations.

Each narrate() block adds its audio to the scene, and on exit waits until the
speech has finished, so the next block never talks over this one.

After each animation the scene runs the layout check (explainer.lint) and, when the
scene ends, writes the warnings to media/lint/<Scene>.txt. It also writes the timing
of each line to media/beats/, which `explainer render` uses for captions, chapters
and contact sheets.
"""

from __future__ import annotations

import json
import os
import re
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

from manim import ORIGIN, FadeIn, FadeOut, Group, MovingCameraScene, Rectangle, Wait, config

from explainer.theme import BG
from explainer.lint import Lint, visible
from explainer.tts import DEFAULT_SPEED, DEFAULT_VOICE, synthesize

config.background_color = BG
# `explainer render` runs each scene in its own process and names it here. Each scene keeps its
# own text and LaTeX caches, so parallel renders never write the same cache file.
if os.environ.get("EXPLAINER_SCENE"):
    config.text_dir = "{media_dir}/texts/" + os.environ["EXPLAINER_SCENE"]
    config.tex_dir = "{media_dir}/Tex/" + os.environ["EXPLAINER_SCENE"]

# Silence kept after each narrate() block, in seconds.
GAP = 0.3
STATIC_SECONDS = 6.0  # longest stretch of a line with no animation
MAX_WORDS = 32  # words in one narrate() line


def _norm(word: str) -> str:
    return re.sub(r"[^\w']", "", word.lower())


@dataclass
class Narration:
    """One spoken line. narrate() yields it as `t`."""

    scene: object
    text: str
    start: float
    duration: float
    words: list[dict]
    # (start, end) scene times of each animation played during the line
    changes: list[tuple[float, float]] = field(default_factory=list)

    def elapsed(self) -> float:
        return self.scene.renderer.time - self.start

    def remaining(self, minimum: float = 1 / 60) -> float:
        """Seconds of speech left, at least `minimum`. Use as run_time to end an animation with the line."""
        return max(self.duration - self.elapsed(), minimum)

    def time_of(self, word: str, occurrence: int = 1) -> float:
        """Seconds from the start of the line until `word` is spoken."""
        target, seen = _norm(word), 0
        for w in self.words:
            if _norm(w["word"]) == target:
                seen += 1
                if seen == occurrence:
                    return w["start"]
        spoken = " ".join(w["word"] for w in self.words)
        raise ValueError(f"word {word!r} (occurrence {occurrence}) not in narration: {spoken}")

    def wait_until(self, word: str, occurrence: int = 1) -> None:
        """Hold the picture until `word` is spoken, so the next animation starts on it.

        Matching ignores case and punctuation: "side" matches "Side,". occurrence picks a repeated word.
        """
        delay = self.time_of(word, occurrence) - self.elapsed()
        if delay > 1 / 60:
            self.scene.wait(delay)

    def longest_static(self) -> float:
        """Longest stretch of the spoken line with no animation playing."""
        end = self.start + self.duration
        longest, cursor = 0.0, self.start
        for a, b in sorted(self.changes):
            longest = max(longest, min(a, end) - cursor)
            cursor = max(cursor, b)
        return max(longest, end - cursor)


class NarrationMixin:
    """Narration for any Manim scene class: `class Zoom(NarrationMixin, ThreeDScene)`."""

    voice = DEFAULT_VOICE
    speed = DEFAULT_SPEED
    # Chapter title in the video. Default: the class name split into words.
    title: str | None = None

    def setup(self):
        super().setup()
        self._line: Narration | None = None
        self._beats: list[dict] = []
        self._lint = Lint(self)
        self._veil = None
        self._focused: list = []

    @contextmanager
    def narrate(self, text: str, gap: float = GAP):
        """Speak `text` from now. On exit, wait until the speech ends, plus `gap` seconds."""
        wav, meta = synthesize(text, self.voice, self.speed)
        self.add_sound(str(wav))
        line = Narration(self, text, self.renderer.time, meta["duration"], meta["words"])
        self._line = line
        self._beats.append({"start": line.start, "duration": line.duration, "text": text, "words": meta["words"]})
        words = len(text.split())
        if words > MAX_WORDS:
            self._lint.warn(("long", line.start), f"line has {words} words; split it, one visual change per line")
        yield line
        # When the line's own animations have finished: the moment a contact-sheet tile shows.
        self._beats[-1]["settled"] = max(self.renderer.time, line.start + line.duration)
        if not any(visible(m) for m in self.mobjects) and line.remaining() > 1:
            self._lint.warn(("blank", line.start), f"screen is blank for {line.remaining():.1f}s of speech")
        self._lint.check_span()
        static = line.longest_static()
        if static > STATIC_SECONDS:
            self._lint.warn(("static", line.start), f"picture is static for {static:.1f}s of this line")
        left = line.duration + gap - line.elapsed()
        if left > 1 / 60:
            self.wait(left)
        self._line = None

    def say(self, text: str, *animations, at: str | None = None, run_time: float | None = None):
        """One beat: speak `text` and play `animations` together, starting at word `at`.

        run_time defaults to the speech left, kept between 0.6 and 1.2 seconds.
        """
        with self.narrate(text) as t:
            if at:
                t.wait_until(at)
            if animations:
                self.play(*animations, run_time=run_time or min(max(t.remaining(), 0.6), 1.2))

    def fade_all(self, run_time: float = 0.6):
        """Fade out everything on screen. End each scene with this."""
        if self.mobjects:
            self.play(FadeOut(Group(*self.mobjects)), run_time=run_time)

    def focus(self, *mobjects, dim: float = 0.78, run_time: float = 0.6):
        """Dim everything except `mobjects`, to point the viewer at them. Undo with self.unfocus().

        Calling it again while focused moves the focus. Objects added while focused sit under the veil.
        """
        for m, z in self._focused:
            m.z_index = z
        self._focused = [(m, m.z_index) for f in mobjects for m in f.get_family()]
        # Raise each part by the same amount, so a group keeps its own stacking order.
        for m, z in self._focused:
            m.z_index = z + 2000
        if self._veil is not None:
            return
        frame = self.camera.frame if hasattr(self.camera, "frame") else None
        veil = Rectangle(width=(frame.width if frame else config.frame_width) * 1.2,
                         height=(frame.height if frame else config.frame_height) * 1.2,
                         fill_color=BG, fill_opacity=dim, stroke_width=0)
        veil.move_to(frame.get_center() if frame else ORIGIN)
        veil.lint_ok = True
        veil.set_z_index(1000)
        self._veil = veil
        self.play(FadeIn(veil), run_time=run_time)

    def unfocus(self, run_time: float = 0.6):
        """Undo self.focus()."""
        if self._veil is None:
            return
        self.play(FadeOut(self._veil), run_time=run_time)
        self._veil = None
        for m, z in self._focused:
            m.z_index = z
        self._focused = []

    def play(self, *animations, **kwargs):
        start = self.renderer.time
        super().play(*animations, **kwargs)
        # Scene.wait() is a play() of a Wait animation: not a visual change, unless updaters move things.
        moving = not all(isinstance(a, Wait) for a in animations) or bool(self.updaters) or any(
            m.updaters for m in self.get_mobject_family_members())
        if self._line is not None and moving:
            self._line.changes.append((start, self.renderer.time))
        self._lint.check()

    def tear_down(self):
        super().tear_down()
        name = type(self).__name__
        if any(visible(m) for m in self.mobjects):
            self._lint.warn(("end",), "scene ends with things on screen; end it with self.fade_all()")
        media = Path(config.media_dir)
        stem = Path(config.input_file).stem if config.input_file else "scene"
        lint = media / "lint" / stem / f"{name}.txt"
        lint.parent.mkdir(parents=True, exist_ok=True)
        lint.write_text("".join(f"{line}\n" for line in self._lint.lines))
        res = f"{config.pixel_height}p{config.frame_rate:g}"
        beats = media / "beats" / stem / res / f"{name}.json"
        beats.parent.mkdir(parents=True, exist_ok=True)
        title = self.title or re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", name)
        beats.write_text(json.dumps({"title": title, "beats": self._beats}, indent=1))


class ExplainerScene(NarrationMixin, MovingCameraScene):
    """A narrated scene. self.camera.frame can pan and zoom:
    self.play(self.camera.frame.animate.scale(0.6).move_to(target))."""
