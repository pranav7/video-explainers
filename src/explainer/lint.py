"""Layout check: finds problems in the frame after each animation.

It looks for:

- objects that run past the edge of the frame,
- text on top of text,
- text that straddles the edge of a box (text wholly inside a box is a label),
- arrows that cross text,
- text too small to read,
- content that fills only a small part of the frame (checked at the end of each line).

Set `m.lint_ok = True` on a mobject to leave it out of the check.
"""

from __future__ import annotations

import re

from manim import (
    DL,
    UR,
    ComplexPlane,
    DecimalNumber,
    FullScreenRectangle,
    Line,
    MarkupText,
    NumberPlane,
    Paragraph,
    SingleStringMathTex,
    SurroundingRectangle,
    Text,
    ThreeDScene,
    TipableVMobject,
    VMobject,
    config,
)
from manim.mobject.types.image_mobject import AbstractImageMobject

MIN_FONT_SIZE = 20  # font_size as seen on screen, after scaling and camera zoom
MIN_SPAN = 0.4  # share of the frame's width or height that the content of a line must span

TEXT_TYPES = (Text, MarkupText, Paragraph, SingleStringMathTex, DecimalNumber)
# Drawn larger than the frame on purpose.
BACKDROP_TYPES = (NumberPlane, ComplexPlane, FullScreenRectangle)


def short(text: str, n: int = 40) -> str:
    return text if len(text) <= n else text[: n - 1] + "…"


def texts_in(mobject) -> list:
    """Text-like mobjects inside `mobject`, without descending into them."""
    if isinstance(mobject, TEXT_TYPES):
        return [mobject]
    return [t for sub in mobject.submobjects for t in texts_in(sub)]


def shapes_in(mobject) -> list:
    """Closed or filled shapes inside `mobject`: boxes, circles, cells. Not text, lines or arrows."""
    # Highlights and background rectangles sit around or behind text on purpose.
    if isinstance(mobject, TEXT_TYPES + (Line, SurroundingRectangle)):
        return []
    own = isinstance(mobject, VMobject) and len(mobject.points) and (mobject.is_closed() or mobject.get_fill_opacity() > 0.05)
    return [mobject] * bool(own) + [s for sub in mobject.submobjects for s in shapes_in(sub)]


def describe(mobject) -> str:
    texts = texts_in(mobject)
    if texts:
        t = texts[0]
        words = getattr(t, "original_text", None) or getattr(t, "tex_string", None) or getattr(t, "text", "")
        words = re.sub(r"<[^>]+>", "", words)  # MarkupText
        if words:
            return f'{type(mobject).__name__} "{short(" ".join(words.split()), 30)}"'
    x, y, _ = mobject.get_center()
    return f"{type(mobject).__name__} at ({x:.1f}, {y:.1f})"


def visible(mobject) -> bool:
    for m in mobject.get_family():
        if isinstance(m, VMobject):
            if len(m.points) and (m.get_fill_opacity() > 0.05 or (m.get_stroke_opacity() > 0.05 and m.get_stroke_width() > 0)):
                return True
        elif isinstance(m, AbstractImageMobject):
            return True
        # Anything else draws nothing: a ValueTracker, or the empty Mobject that Scene.wait() adds.
    return False


def _box(mobject) -> tuple[float, float, float, float]:
    (x0, y0, _), (x1, y1, _) = mobject.get_corner(DL), mobject.get_corner(UR)
    return x0, y0, x1, y1


def _area(b) -> float:
    return max(b[2] - b[0], 0) * max(b[3] - b[1], 0)


def _intersection(a, b) -> tuple[float, float, float, float]:
    return max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])


class Lint:
    """Collects layout warnings for one scene. Each problem is reported once."""

    def __init__(self, scene):
        self.scene = scene
        self.seen: set[tuple] = set()
        self.lines: list[str] = []

    def warn(self, key: tuple, message: str) -> None:
        if key in self.seen:
            return
        self.seen.add(key)
        where = f"{type(self.scene).__name__} {self.scene.renderer.time:5.1f}s"
        line = getattr(self.scene, "_line", None)
        if line is not None:
            where += f' "{short(line.text)}"'
        self.lines.append(f"{where}: {message}")

    def frame(self):
        """The visible area as (x0, y0, x1, y1), and the camera zoom (2 = twice as close)."""
        camera = self.scene.camera
        if hasattr(camera, "frame"):
            f = camera.frame
            (cx, cy, _), w, h = f.get_center(), f.width, f.height
        else:
            cx = cy = 0.0
            w, h = config.frame_width, config.frame_height
        return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), config.frame_width / w

    def check(self) -> None:
        if isinstance(self.scene, ThreeDScene):
            return
        frame, zoom = self.frame()
        shown = [m for m in self.scene.mobjects if visible(m) and not getattr(m, "lint_ok", False)]
        layout = [m for m in shown if not isinstance(m, BACKDROP_TYPES)]

        # Zoomed in, the parts left outside the frame are outside on purpose.
        if zoom <= 1.05:
            for m in layout:
                b = _box(m)
                over = max(frame[0] - b[0], frame[1] - b[1], b[2] - frame[2], b[3] - frame[3])
                if over > 0.05:
                    self.warn(("frame", id(m)), f"{describe(m)} runs {over:.2f} units past the frame edge")

        texts = [t for m in shown for t in texts_in(m) if visible(t) and not getattr(t, "lint_ok", False)]
        for t in texts:
            size = getattr(t, "font_size", None)
            if size and size * zoom < MIN_FONT_SIZE:
                self.warn(("small", id(t)), f"{describe(t)} is font size {size * zoom:.1f} on screen; use {MIN_FONT_SIZE} or more")

        boxes = [(t, _box(t)) for t in texts]
        for i, (a, ba) in enumerate(boxes):
            for b, bb in boxes[i + 1 :]:
                smaller = min(_area(ba), _area(bb))
                if smaller and _area(_intersection(ba, bb)) > 0.2 * smaller:
                    self.warn(("overlap", id(a), id(b)), f"{describe(a)} overlaps {describe(b)}")

        for m in layout:
            for shape in shapes_in(m):
                if not visible(shape):
                    continue
                bs = _box(shape)
                for t, bt in boxes:
                    share = _area(_intersection(bs, bt)) / (_area(bt) or 1)
                    if 0.1 < share < 0.9:
                        self.warn(("covered", id(t), id(m)), f"{describe(t)} is partly covered by {describe(m)}")

        # Every connector with a tip: arrows, curved and dashed arrows, elbows.
        arrows = [a for m in shown for a in m.get_family()
                  if isinstance(a, TipableVMobject) and a.has_tip() and visible(a)]
        for arrow in arrows:
            if len(arrow.points):
                samples = [arrow.point_from_proportion(k / 20) for k in range(1, 20)]
            else:  # a dashed line keeps its points in its dashes
                start, end = arrow.get_start(), arrow.get_end()
                samples = [start + (end - start) * k / 20 for k in range(1, 20)]
            for t, (x0, y0, x1, y1) in boxes:
                # Shrink the box so an arrow that only touches a label's edge passes.
                dx, dy = (x1 - x0) * 0.15, (y1 - y0) * 0.15
                if any(x0 + dx < x < x1 - dx and y0 + dy < y < y1 - dy for x, y, _ in samples):
                    self.warn(("arrow", id(arrow), id(t)), f"an arrow crosses {describe(t)}")

    def check_span(self) -> None:
        """Warn when the content on screen spans less than MIN_SPAN of the frame's width and height."""
        if isinstance(self.scene, ThreeDScene):
            return
        frame, _ = self.frame()
        layout = [m for m in self.scene.mobjects
                  if visible(m) and not getattr(m, "lint_ok", False) and not isinstance(m, BACKDROP_TYPES)]
        if len(layout) < 2:
            return  # one object alone (a title, a headline number) is a deliberate composition
        boxes = [_box(m) for m in layout]
        w = max(b[2] for b in boxes) - min(b[0] for b in boxes)
        h = max(b[3] for b in boxes) - min(b[1] for b in boxes)
        fw, fh = frame[2] - frame[0], frame[3] - frame[1]
        if w < MIN_SPAN * fw and h < MIN_SPAN * fh:
            self.warn(("span", self.scene.renderer.time),
                      f"content spans only {w / fw:.0%} of the frame width and {h / fh:.0%} of its height; scale it up")
