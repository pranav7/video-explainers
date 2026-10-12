"""Numbers and data: bars, bar charts, counters, big statistics, legends, checklists."""

from __future__ import annotations

from functools import partial

from manim import DOWN, LEFT, RIGHT, UP, Circle, DecimalNumber, RoundedRectangle, Text, VGroup

from explainer.kit.shapes import tick, xmark
from explainer.kit.text import label
from explainer.theme import FAINT, INK, LINE, SANS, SKY, SMALL_SIZE, SUBTLE, TEXT_SIZE


def _track(width: float, height: float):
    return RoundedRectangle(corner_radius=height / 2, width=width, height=height, fill_color=LINE, fill_opacity=1,
                            stroke_width=0)


def _fill(track, share: float, color):
    h = track.height
    w = max(track.width * min(max(share, 0), 1), h)
    return RoundedRectangle(corner_radius=h / 2, width=w, height=h, fill_color=color, fill_opacity=1,
                            stroke_width=0).align_to(track, LEFT)


def bar(value: float, total: float, color, width: float = 5, height: float = 0.32, size: float = SMALL_SIZE,
        text: str | None = None) -> VGroup:
    """A rounded progress bar with "value of total" at its right. [0] track, [1] fill, [2] text.

    Grow the fill with GrowFromEdge(b[1], LEFT).
    """
    track = _track(width, height)
    fill = _fill(track, value / total if total else 0, color)
    words = label(text or f"{value:g} of {total:g}", size, color, weight="MEDIUM").next_to(track, RIGHT, buff=0.3)
    return VGroup(track, fill, words)


def bars(items, color=SKY, width: float = 6, height: float = 0.36, size: float = SMALL_SIZE,
         max_value: float | None = None) -> VGroup:
    """A horizontal bar chart. items: (label, value) or (label, value, colour).

    Returns a VGroup of rows; a row is VGroup(name, track, fill, value). Grow the fills with
    LaggedStart(*[GrowFromEdge(r[2], LEFT) for r in chart]).
    """
    items = [(i[0], i[1], i[2] if len(i) > 2 else color) for i in items]
    if not items:
        raise ValueError("bars() needs at least one (label, value) item")
    top = max_value or max(v for _, v, _ in items) or 1
    names = [label(n, size, SUBTLE) for n, _, _ in items]
    column = max(n.width for n in names)
    rows = VGroup()
    for name, (_, value, c) in zip(names, items):
        track = _track(width, height)
        fill = _fill(track, value / top, c)
        number = label(f"{value:g}", size, c, weight="SEMIBOLD").next_to(track, RIGHT, buff=0.25)
        name.next_to(track, LEFT, buff=0.3).shift(LEFT * (column - name.width))
        rows.add(VGroup(name, track, fill, number))
    return rows.arrange(DOWN, buff=0.35, aligned_edge=LEFT)


def number(value: float, color=INK, size: float = 72, decimals: int = 0, weight: str = "BOLD") -> DecimalNumber:
    """A number in the kit font. Show it as it is, with appear(n). Do not count up to it.

    When the value changes from one real state to another (2 rows agree, then 10), turn the old
    number into the new one: Transform(n, number(10, color, size).move_to(n)).
    Use this, not Integer or DecimalNumber, which draw digits in a LaTeX serif font.
    """
    return DecimalNumber(value, num_decimal_places=decimals, mob_class=partial(Text, font=SANS, weight=weight),
                         font_size=size, color=color)


def stat(value: float, caption: str, color=SKY, size: float = 96, decimals: int = 0) -> VGroup:
    """A big number with a caption under it, for the one figure that matters. [0] number, [1] caption.

    Show it with appear(s).
    """
    return VGroup(number(value, color, size, decimals), label(caption, TEXT_SIZE, SUBTLE)).arrange(DOWN, buff=0.25)


def legend(items, size: float = SMALL_SIZE, buff: float = 0.7) -> VGroup:
    """A row of colour keys. items: (colour, text) pairs."""
    keys = [VGroup(Circle(0.11, fill_color=c, fill_opacity=1, stroke_width=0), label(s, size, SUBTLE)).arrange(RIGHT, buff=0.18)
            for c, s in items]
    return VGroup(*keys).arrange(RIGHT, buff=buff)


def checklist(items, size: float = TEXT_SIZE, buff: float = 0.3) -> VGroup:
    """Rows of a mark and a text. items: (text, state); state True is a tick, False an X, None a dot.

    Returns a VGroup of rows; a row is VGroup(mark, text).
    """
    rows = VGroup()
    for text, state in items:
        mark = tick(size=0.36) if state is True else xmark(size=0.3) if state is False else Circle(
            0.07, fill_color=FAINT, fill_opacity=1, stroke_width=0)
        rows.add(VGroup(mark, label(text, size, INK if state is not None else SUBTLE)).arrange(RIGHT, buff=0.3))
    rows.arrange(DOWN, buff=buff, aligned_edge=LEFT)
    for row in rows:
        row[1].align_to(rows[0][1], LEFT)
    return rows
