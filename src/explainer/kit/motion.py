"""Animations with the kit's timing: entrances, exits and flow along connectors.

For pointing at one object, Manim's Indicate, Circumscribe and Flash also work well.
To dim everything except some objects, use self.focus(...) and self.unfocus() in a scene.
"""

from __future__ import annotations

from manim import DOWN, UP, Dot, FadeIn, FadeOut, LaggedStart, Line, MoveAlongPath, ShowPassingFlash, Succession, VMobject
from manim.utils.rate_functions import ease_in_cubic, ease_in_out_cubic, ease_out_cubic

from explainer.theme import AMBER


def appear(*mobjects, lag: float = 0.12, shift=UP * 0.2):
    """Fade in, rising slightly and settling: the default entrance. Staggers several objects."""
    return LaggedStart(*[FadeIn(m, shift=shift, scale=0.95, rate_func=ease_out_cubic) for m in mobjects],
                       lag_ratio=lag)


def disappear(*mobjects, lag: float = 0.04, shift=DOWN * 0.1):
    """Fade out, sinking slightly. The pair of appear()."""
    # Keep the default group: with an empty one, Manim does not remove a group whose parts were added one by one.
    return LaggedStart(*[FadeOut(m, shift=shift, rate_func=ease_in_cubic) for m in mobjects], lag_ratio=lag)


def flow(path, color=None, pulses: int = 1, width: float = 7, time_width: float = 0.4):
    """A bright pulse that runs along a connector, to show data or control moving along it.

    The connector stays on screen. pulses > 1 sends a stream.
    """
    # One path with the connector's shaft and no tip, so a single pulse runs from start to end.
    if len(path.points):
        trail = VMobject().set_points(path.points.copy())
    else:  # a dashed line keeps its points in its dashes
        trail = Line(path.get_start(), path.get_end())
    trail.set_fill(opacity=0).set_stroke(color or path.get_color(), width=width)
    return LaggedStart(*[ShowPassingFlash(trail.copy(), time_width=time_width) for _ in range(pulses)], lag_ratio=0.35)


def travel(path, color=AMBER, text: str | None = None):
    """A dot, or a tag with `text`, that appears at the start of a connector, moves along it,
    and fades out at the end: a request, a document or a message on its way."""
    from explainer.kit.shapes import pill

    item = pill(text, color, filled=True) if text else Dot(radius=0.1, color=color)
    # A dashed line keeps its points in its dashes, so follow the straight line from start to end.
    track = path if len(path.points) else Line(path.get_start(), path.get_end())
    item.move_to(track.point_from_proportion(0))
    return Succession(FadeIn(item, scale=0.6, run_time=0.15),
                      MoveAlongPath(item, track, rate_func=ease_in_out_cubic, run_time=1),
                      FadeOut(item, scale=0.6, run_time=0.15))
