"""Shapes: cards, tags, folders, tables, icons and marks."""

from __future__ import annotations

from functools import lru_cache

from manim import (
    DL,
    DOWN,
    DR,
    LEFT,
    RIGHT,
    UL,
    UP,
    UR,
    CapStyleType,
    Circle,
    Line,
    Polygon,
    Rectangle,
    RoundedRectangle,
    SurroundingRectangle,
    SVGMobject,
    Text,
    VGroup,
    VMobject,
)

from explainer.kit.icons import icon_path
from explainer.kit.text import label, mono
from explainer.theme import (
    AMBER,
    BG,
    CODE_SIZE,
    CORAL,
    INK,
    LINE,
    MINT,
    MONO,
    RADIUS,
    RAISED,
    SANS,
    SKY,
    SMALL_SIZE,
    STROKE,
    SUBTLE,
    SURFACE,
    tint,
)


@lru_cache
def _svg(name: str) -> SVGMobject:
    return SVGMobject(str(icon_path(name)))


def icon(name: str, color=SKY, height: float = 0.6) -> SVGMobject:
    """A Lucide line icon by name: "database", "bot", "file-text", "folder", "search", "server",
    "user", "users", "mail", "lock", "clock", "calendar", "settings", "terminal", "cloud", "globe",
    "zap", "git-branch", "message-square", "chart-column", "table", "sheet", "filter", "link", "cpu",
    "shield", "triangle-alert", "circle-check", "circle-x". Any name at https://lucide.dev/icons works.
    """
    m = _svg(name).copy().scale_to_fit_height(height)
    return m.set_fill(opacity=0).set_stroke(color, width=max(1.5, 4 * height), opacity=1)


def box(text: str, color, size: float = 28, sub: str | None = None, icon_name: str | None = None,
        width: float | None = None, height: float | None = None, text_color=INK, font: str = SANS) -> VGroup:
    """A card: rounded, tinted, with a semibold label. For a component, an actor or a step.

    `sub` adds a smaller second line. `icon_name` puts a Lucide icon before the text.
    [0] is the frame, [1] the content (text, or icon and text).
    """
    words = label(text, size, text_color, weight="SEMIBOLD", font=font)
    if sub:
        words = VGroup(words, label(sub, size * 0.75, SUBTLE, font=font)).arrange(DOWN, buff=0.12)
    content = words
    if icon_name:
        content = VGroup(icon(icon_name, color, height=max(words.height, 0.45)), words).arrange(RIGHT, buff=0.25)
    frame = RoundedRectangle(
        corner_radius=RADIUS,
        width=max(content.width + 0.7, width or 0),
        height=max(content.height + 0.5, height or 0),
        fill_color=tint(color, 0.16), fill_opacity=1, stroke_color=color, stroke_width=STROKE,
    )
    if content.width > frame.width - 0.3:
        content.scale_to_fit_width(frame.width - 0.3)
    return VGroup(frame, content.move_to(frame))


def pill(text: str, color, size: float = SMALL_SIZE - 2, filled: bool = False, font: str = SANS) -> VGroup:
    """A small rounded tag: a status, a row ID, a value. [0] frame, [1] text.

    filled=True makes a solid tag with dark text, for the one status that matters most.
    """
    words = label(text, size, BG if filled else color, weight="MEDIUM", font=font)
    h = words.height + 0.28
    frame = RoundedRectangle(
        corner_radius=h / 2, width=words.width + 0.5, height=h,
        fill_color=color if filled else tint(color, 0.18), fill_opacity=1, stroke_color=color, stroke_width=1.5,
    )
    return VGroup(frame, words.move_to(frame))


def badge(text, color=SKY, size: float = 24) -> VGroup:
    """A solid circle with a number or letter: step markers 1, 2, 3. [0] circle, [1] text."""
    words = label(str(text), size, BG, weight="BOLD")
    circle = Circle(radius=max(words.width, words.height) / 2 + 0.14, fill_color=color, fill_opacity=1, stroke_width=0)
    return VGroup(circle, words.move_to(circle))


def folder(name: str, color, lines=(), width: float = 4.8, height: float = 2.5, size: float = 26) -> VGroup:
    """A folder with a name and lines of contents (strings or (string, colour) pairs).

    [0] body, [1] tab, [2] name, [3] the content lines.
    """
    body = RoundedRectangle(corner_radius=RADIUS, width=width, height=height, fill_color=tint(color, 0.1),
                            fill_opacity=1, stroke_color=color, stroke_width=STROKE)
    tab = RoundedRectangle(corner_radius=0.08, width=min(1.5, width * 0.35), height=0.36, fill_color=tint(color, 0.3),
                           fill_opacity=1, stroke_color=color, stroke_width=STROKE)
    tab.next_to(body, UP, buff=-0.08).align_to(body, LEFT).shift(RIGHT * 0.25)
    tab.set_z_index(body.z_index - 0.1)
    head = label(name, size, color, weight="SEMIBOLD").move_to(body.get_top() + DOWN * 0.45)
    items = [(i, INK) if isinstance(i, str) else i for i in lines]
    subs = VGroup(*[label(s, size * 0.85, c) for s, c in items]).arrange(DOWN, buff=0.16)
    subs.next_to(head, DOWN, buff=0.3)
    for part in (head, subs):
        if part.width > width - 0.4:
            part.scale_to_fit_width(width - 0.4)
    return VGroup(body, tab, head, subs)


def table(rows, color=SKY, size: float = CODE_SIZE, header: bool = True, font: str = MONO, pad: float = 0.4) -> VGroup:
    """A grid of cells. `rows` is a list of rows. A cell is a string or a (string, colour) pair.

    Returns a VGroup of rows: table[r][c] is one cell, a VGroup(frame, text). With `header`,
    row 0 is tinted and bold. Body rows alternate two dark shades. Column width fits the widest cell.
    """
    rows = [[(c, INK) if isinstance(c, str) else c for c in row] for row in rows]
    texts = [
        [Text(s or " ", font=font, font_size=size, color=color if header and r == 0 else c,
              weight="BOLD" if header and r == 0 else "NORMAL", disable_ligatures=True) for s, c in row]
        for r, row in enumerate(rows)
    ]
    widths = [max(row[i].width for row in texts if i < len(row)) + pad for i in range(max(map(len, texts)))]
    height = max(t.height for row in texts for t in row) + pad * 0.7
    grid = VGroup()
    for r, row in enumerate(texts):
        fill = tint(color, 0.2) if header and r == 0 else (SURFACE if r % 2 else RAISED)
        line = VGroup()
        for c, t in enumerate(row):
            frame = Rectangle(width=widths[c], height=height, fill_color=fill, fill_opacity=1,
                              stroke_color=LINE, stroke_width=1.2)
            line.add(VGroup(frame, t.move_to(frame)))
        grid.add(line.arrange(RIGHT, buff=0))
    return grid.arrange(DOWN, buff=0, aligned_edge=LEFT)


def squares(n: int, cols: int, color, side: float = 0.36, fill: float = 0.3, buff: float = 0.1) -> VGroup:
    """n rounded squares in rows of `cols`: one per item, to show a count you can recolour
    with s.animate.set_fill(colour, 0.8).set_stroke(colour)."""
    group = VGroup(*[RoundedRectangle(corner_radius=side * 0.2, width=side, height=side, stroke_color=color,
                                      stroke_width=2, fill_color=color, fill_opacity=fill) for _ in range(n)])
    return group.arrange_in_grid(cols=cols, buff=buff)


def bubble(text: str, color=AMBER, width: float = 4.5, size: float = SMALL_SIZE) -> VGroup:
    """A comment or speech bubble with wrapped text and a tail. [0] frame (bubble and tail), [1] text."""
    words = label(text, size, INK, width=width - 0.6)
    body = RoundedRectangle(corner_radius=0.2, width=width, height=words.height + 0.55, fill_color=tint(color, 0.16),
                            fill_opacity=1, stroke_color=color, stroke_width=2)
    corner = body.get_corner(DL) + RIGHT * 0.45
    tail = Polygon(corner + UP * 0.02, corner + RIGHT * 0.4 + UP * 0.02, corner + DOWN * 0.3 + RIGHT * 0.05,
                   fill_color=tint(color, 0.16), fill_opacity=1, stroke_color=color, stroke_width=2)
    tail.set_z_index(body.z_index - 0.1)
    return VGroup(VGroup(body, tail), words.move_to(body))


def _round(m: VMobject) -> VMobject:
    return m.set_cap_style(CapStyleType.ROUND)


def tick(color=MINT, size: float = 0.4) -> VMobject:
    """A check mark."""
    return _round(VMobject(stroke_color=color, stroke_width=6).set_points_as_corners(
        [LEFT * size * 0.5, DOWN * size * 0.4 + LEFT * size * 0.1, UP * size * 0.5 + RIGHT * size * 0.5]))


def xmark(color=CORAL, size: float = 0.4) -> VGroup:
    """An X mark. To cross out an object instead, use strike(m) or Manim's Cross(m)."""
    d = size / 2
    return VGroup(*[_round(Line(a * d, b * d, stroke_color=color, stroke_width=6)) for a, b in ((UL, DR), (UR, DL))])


def highlight(m, color=AMBER, buff: float = 0.12) -> SurroundingRectangle:
    """A rounded outline around m, to point at it. Draw it with Create."""
    return SurroundingRectangle(m, color=color, buff=buff, corner_radius=0.1, stroke_width=3)


def strike(m, color=CORAL) -> Line:
    """A line through m, to show it is wrong or removed. Draw it with Create."""
    return _round(Line(m.get_left() + LEFT * 0.1, m.get_right() + RIGHT * 0.1, stroke_color=color, stroke_width=4))


def recolor(m: VGroup, color):
    """Animate a box() or pill() to a new colour, to change its status (pending to done, for example)."""
    from manim import Transform

    # One Transform of the whole group: an AnimationGroup of its parts would redraw the frame over the text.
    target = m.copy()
    frame, words = target[0], target[1]
    old = frame.get_stroke_color()
    frame.set_fill(color if frame.get_fill_color() == old else tint(color, 0.16)).set_stroke(color)
    for part in words.family_members_with_points():
        if part.get_stroke_opacity() > 0 and part.get_stroke_color() == old:
            part.set_stroke(color)  # icon strokes
        if part.get_fill_opacity() > 0 and part.get_fill_color() == old:
            part.set_fill(color)  # a pill's text
    return Transform(m, target)


def glow(m, color=None) -> VGroup:
    """A soft halo behind m (or behind its frame, for a box), to mark the active element. Add it with FadeIn.

    Use it on one element at a time.
    """
    target = m[0] if isinstance(m, VGroup) and len(m) and isinstance(m[0], (Rectangle, Circle)) else m
    c = color or target.get_stroke_color()
    layers = VGroup(*[target.copy().set_fill(opacity=0).set_stroke(c, width=w, opacity=o)
                      for w, o in ((8, 0.2), (15, 0.1), (24, 0.05))])
    return layers.set_z_index(target.z_index - 1)
