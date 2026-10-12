"""Text: labels, headings, monospace lines, and code with syntax colours."""

from __future__ import annotations

import html
import textwrap
from functools import lru_cache

from manim import DOWN, LEFT, RIGHT, UP, Circle, Line, MarkupText, Rectangle, RoundedRectangle, Text, VGroup

from explainer.theme import (
    AMBER,
    AQUA,
    CODE_SIZE,
    CORAL,
    FAINT,
    INK,
    LINE,
    MINT,
    MONO,
    RADIUS,
    RAISED,
    SANS,
    SKY,
    SUBTLE,
    SURFACE,
    TEXT_SIZE,
    TITLE_SIZE,
    VIOLET,
    tint,
)


@lru_cache
def _char_width(font: str, size: float) -> float:
    sample = "the quick brown fox jumps over a lazy dog"
    return Text(sample, font=font, font_size=size).width / len(sample)


def label(s: str, size: float = TEXT_SIZE, color=INK, width: float | None = None, weight: str = "NORMAL",
          font: str = SANS, **kw) -> Text:
    """Sans-serif text (Inter). With `width`, wraps onto lines no wider than `width` units.

    weight is "NORMAL", "MEDIUM", "SEMIBOLD" or "BOLD".
    """
    if width:
        chars = max(int(width / _char_width(font, size)), 1)
        s = "\n".join(textwrap.fill(p, chars, break_long_words=False, break_on_hyphens=False) or p for p in s.split("\n"))
    # Without ligatures each character is one glyph, so part() can find words by position.
    return Text(s, font=font, font_size=size, color=color, weight=weight, disable_ligatures=True, **kw)


def mono(s: str, size: float = CODE_SIZE, color=INK, **kw) -> Text:
    """Monospace text (JetBrains Mono), for code, file names, IDs and values."""
    return Text(s, font=MONO, font_size=size, color=color, disable_ligatures=True, **kw)


def title(s: str, color=INK, size: float = TITLE_SIZE) -> Text:
    """A semibold heading at the top of the frame."""
    return label(s, size, color, weight="SEMIBOLD").to_edge(UP, buff=0.55)


def part(t: Text, sub: str, occurrence: int = 1) -> VGroup:
    """The glyphs of `sub` inside a label() or mono() text, to colour, highlight or move them:
    highlight(part(t, "PO number")) or part(t, "PO").animate.set_color(AMBER)."""
    text = t.original_text
    start = -1
    for _ in range(occurrence):
        start = text.find(sub, start + 1)
        if start < 0:
            raise ValueError(f"{sub!r} (occurrence {occurrence}) is not in {text!r}")
    # Text draws no glyph for spaces and line breaks.
    skip, n = len("".join(text[:start].split())), len("".join(sub.split()))
    return VGroup(*t.submobjects[skip:skip + n])


def _indented(lines: list, char: float, buff: float) -> VGroup:
    """Arrange (mobject, indent) pairs as left-aligned lines, shifting each by its indent."""
    group = VGroup(*[m for m, _ in lines]).arrange(DOWN, aligned_edge=LEFT, buff=buff)
    for m, indent in lines:
        m.shift(RIGHT * char * indent)
    return group


def lines_of(spec, size: float = CODE_SIZE, color=INK, buff: float = 0.16) -> VGroup:
    """Monospace lines that keep their indentation, aligned left.

    `spec` is a string with newlines, or a list of strings and (string, colour) pairs.
    """
    items = spec.split("\n") if isinstance(spec, str) else spec
    items = [(i, color) if isinstance(i, str) else i for i in items]
    lines = []
    for s, c in items:
        body = s.lstrip(" ")
        # Text drops leading spaces, so indent by hand. A blank line is an invisible "x" of the same height.
        m = mono(body, size, c) if body else mono("x", size).set_opacity(0)
        lines.append((m, len(s) - len(body)))
    return _indented(lines, _char_width(MONO, size), buff)


def _token_color(token) -> str:
    from pygments.token import Comment, Keyword, Name, Number, Operator, String

    for kind, color in ((Comment, FAINT), (Keyword, VIOLET), (String, MINT), (Number, AMBER),
                        (Name.Function, SKY), (Name.Class, SKY), (Name.Builtin, AQUA), (Name.Decorator, AQUA),
                        (Operator, SUBTLE)):
        if token in kind:
            return color.to_hex()
    return INK.to_hex()


def window(content, heading: str | None = None, color=LINE, width: float | None = None, pad: float = 0.35) -> VGroup:
    """A rounded window frame with a title bar around `content`, like an editor or a terminal.

    [0] the frame (body, title bar, rule, dots, outline, heading), [1] `content`.
    """
    bar_h = 0.42
    head = mono(heading, 22, SUBTLE) if heading else None
    # The heading is centred in the title bar; leave the dots room on its left.
    w = max(content.width + 2 * pad, width or 0, 3.0, head.width + 1.6 if head else 0)
    h = content.height + 2 * pad + bar_h
    body = RoundedRectangle(corner_radius=RADIUS, width=w, height=h, fill_color=SURFACE, fill_opacity=1,
                            stroke_color=color, stroke_width=1.5)
    # The title bar follows the body's rounded top corners. One shape, so the layout check sees the
    # heading wholly inside it. Rectangle corners run UR, UL, DL, DR.
    inset = 0.02
    bar = Rectangle(width=w - 2 * inset, height=bar_h, fill_color=RAISED, fill_opacity=1, stroke_width=0)
    bar.round_corners([RADIUS - inset, RADIUS - inset, 0, 0])
    bar.align_to(body, UP).shift(DOWN * inset)
    rule = Line(bar.get_corner(DOWN + LEFT), bar.get_corner(DOWN + RIGHT), stroke_color=LINE, stroke_width=1)
    dots = VGroup(*[Circle(0.055, fill_color=c, fill_opacity=0.9, stroke_width=0) for c in (CORAL, AMBER, MINT)])
    dots.arrange(RIGHT, buff=0.1).move_to(bar).align_to(bar, LEFT).shift(RIGHT * 0.22)
    # The outline again, over the title bar, so the border stays one clean line.
    outline = body.copy().set_fill(opacity=0)
    chrome = VGroup(body, bar, rule, dots, outline)
    if head:
        chrome.add(head.move_to(bar))
    content.next_to(bar, DOWN, buff=pad).align_to(body, LEFT).shift(RIGHT * pad)
    # Above the line highlights that code_line() puts between the frame and the text.
    content.set_z_index(1)
    return VGroup(chrome, content)


def panel(spec, color=LINE, size: float = CODE_SIZE, heading: str | None = None, width: float | None = None) -> VGroup:
    """Plain monospace lines in a window frame (see lines_of for `spec`). [0] frame, [1] lines; [1][i] is line i."""
    return window(lines_of(spec, size), heading, color, width)


def code(src: str, language: str = "python", size: float = CODE_SIZE, heading: str | None = None,
         color=LINE, width: float | None = None) -> VGroup:
    """Syntax-coloured code in a window frame. [0] frame, [1] lines; [1][i] is line i.

    Point at a line with code_line(c, i).
    """
    from pygments import lex
    from pygments.lexers import get_lexer_by_name

    rows: list[list[tuple[str, str]]] = [[]]
    for token, value in lex(textwrap.dedent(src).strip("\n"), get_lexer_by_name(language)):
        for k, part in enumerate(value.split("\n")):
            if k:
                rows.append([])
            if part:
                rows[-1].append((part, _token_color(token)))
    while rows and not rows[-1]:  # the lexer ends the text with a newline
        rows.pop()
    lines = []
    for row in rows:
        text = "".join(p for p, _ in row)
        indent = len(text) - len(text.lstrip(" "))
        markup, skip = "", indent
        for part, hexcolor in row:
            cut = min(skip, len(part) - len(part.lstrip(" ")))
            part, skip = part[cut:], skip - cut
            if part:
                markup += f'<span foreground="{hexcolor}">{html.escape(part, quote=False)}</span>'
        m = MarkupText(markup, font=MONO, font_size=size) if markup else mono("x", size).set_opacity(0)
        lines.append((m, indent))
    c = window(_indented(lines, _char_width(MONO, size), 0.16), heading, color, width)
    c.source = ["".join(p for p, _ in row) for row in rows]
    c.settings = {"language": language, "size": size, "heading": heading, "color": color, "width": width}
    return c


def code_edit(old: VGroup, src: str):
    """Animate a code() window into new code, as a diff: kept lines move into place, removed
    lines fade out to the left, new lines fade in from the right.

    Returns (new window, animation). Play the animation. The new window takes the old one's place,
    with the same top-left corner, so kept lines do not move sideways. If the new code is wider,
    move the old window left first so the new one fits in the frame.
    """
    from difflib import SequenceMatcher

    from manim import AnimationGroup, FadeIn, FadeOut, Group, ReplacementTransform

    new = code(src, **old.settings)
    new.move_to(old.get_corner(UP + LEFT), aligned_edge=UP + LEFT)
    anims = [ReplacementTransform(old[0], new[0])]
    for op, i1, i2, j1, j2 in SequenceMatcher(None, old.source, new.source, autojunk=False).get_opcodes():
        if op == "equal":
            anims += [ReplacementTransform(old[1][i], new[1][j]) for i, j in zip(range(i1, i2), range(j1, j2))]
            continue
        anims += [FadeOut(old[1][i], shift=LEFT * 0.4) for i in range(i1, i2)]
        anims += [FadeIn(new[1][j], shift=LEFT * 0.4) for j in range(j1, j2)]
    # group=Group(): Manim would otherwise add the animated parts again on top of everything else.
    return new, AnimationGroup(*anims, group=Group())


def code_line(c: VGroup, i: int, color=AMBER) -> Rectangle:
    """A tinted bar behind line i of a code() or panel() window. Add it with FadeIn."""
    frame, line = c[0][0], c[1][i]
    bar = Rectangle(width=frame.width - 0.08, height=line.height + 0.14, fill_color=tint(color, 0.28),
                    fill_opacity=1, stroke_width=0).move_to([frame.get_center()[0], line.get_center()[1], 0])
    bar.set_z_index(0.5)
    return bar
