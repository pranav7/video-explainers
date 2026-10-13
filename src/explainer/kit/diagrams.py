"""Diagrams: connectors, pipelines, sequence diagrams, timelines, trees, callouts."""

from __future__ import annotations

import numpy as np
from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    UR,
    Arrow,
    Brace,
    Circle,
    CurvedArrow,
    DashedLine,
    Dot,
    Graph,
    Line,
    Mobject,
    RoundedRectangle,
    StealthTip,
    TipableVMobject,
    VGroup,
)

from explainer.kit.shapes import box, pill
from explainer.kit.text import label, mono
from explainer.theme import AMBER, CORAL, INK, LINE, MINT, SKY, SMALL_SIZE, STROKE, SUBTLE

TIP = 0.2  # arrow tip length


def _point(m) -> np.ndarray:
    return m.get_center() if isinstance(m, Mobject) else np.array(m, dtype=float)


def _corner_radius(m: Mobject) -> float:
    """The corner radius of m's rounded frame: a RoundedRectangle in m that fills m's bounding box."""
    for part in m.get_family():
        if (isinstance(part, RoundedRectangle) and abs(part.width - m.width) < 0.05
                and abs(part.height - m.height) < 0.05):
            return float(part.corner_radius)
    return 0.0


def _edge_point(m, direction: np.ndarray) -> np.ndarray:
    """Where a ray from m's centre in `direction` leaves m's bounding box, following rounded
    corners if m has a rounded frame. A point stays itself."""
    if not isinstance(m, Mobject):
        return np.array(m, dtype=float)
    c, hw, hh = m.get_center(), m.width / 2, m.height / 2
    u = np.array([direction[0], direction[1], 0], dtype=float)
    u /= np.linalg.norm(u) or 1
    t = min(hw / abs(u[0]) if u[0] else np.inf, hh / abs(u[1]) if u[1] else np.inf)
    hit = u * t
    r = min(_corner_radius(m), hw, hh)
    if r and abs(hit[0]) > hw - r and abs(hit[1]) > hh - r:
        # The ray leaves through a rounded corner: meet the arc, not the bounding box corner.
        k = np.array([np.sign(hit[0]) * (hw - r), np.sign(hit[1]) * (hh - r), 0])
        b = np.dot(u, k)
        t = b + np.sqrt(max(b * b - np.dot(k, k) + r * r, 0))
        hit = u * t
    return c + hit


def connect(a, b, color=SUBTLE, buff: float = 0.12, dashed: bool = False, curve: float = 0, stroke: float = STROKE):
    """An arrow from the edge of a to the edge of b, along the line between their centres.

    a and b are mobjects or points. curve bends it (radians, 0.5 is a gentle arc; negative
    bends the other way). Draw a straight arrow with GrowArrow; dashed or curved ones with Create.
    """
    d = _point(b) - _point(a)
    start, end = _edge_point(a, d), _edge_point(b, -d)
    if curve:
        n = d / (np.linalg.norm(d) or 1)
        return CurvedArrow(start + n * buff, end - n * buff, angle=curve, color=color, stroke_width=stroke,
                           tip_shape=StealthTip, tip_length=TIP)
    if dashed:
        return DashedLine(start, end, buff=buff, color=color, stroke_width=stroke, dash_length=0.12).add_tip(
            tip_shape=StealthTip, tip_length=TIP)
    return Arrow(start, end, buff=buff, color=color, stroke_width=stroke, tip_shape=StealthTip, tip_length=TIP,
                 max_tip_length_to_length_ratio=0.3, max_stroke_width_to_length_ratio=10)


def arrow_label(arrow, text: str, size: float = SMALL_SIZE, color=None, side: int = 1):
    """A label beside the middle of `arrow`. side=1 puts it left of the direction of travel, -1 right."""
    d = arrow.get_end() - arrow.get_start()
    normal = np.array([-d[1], d[0], 0]) / (np.linalg.norm(d) or 1) * side
    words = label(text, size, color or arrow.get_color())
    # A dashed line has no points of its own: use the middle of its chord.
    middle = arrow.point_from_proportion(0.5) if len(arrow.points) else (arrow.get_start() + arrow.get_end()) / 2
    return words.next_to(middle, normal, buff=0.15)


def elbow(a, b, color=SUBTLE, stroke: float = STROKE, radius: float = 0.2) -> TipableVMobject:
    """A right-angled arrow with rounded corners: out of a, across at the halfway line, into b.

    Goes vertically when b is wholly below or above a, else horizontally. Draw it with Create.
    """
    d = b.get_center() - a.get_center()
    if b.get_top()[1] < a.get_bottom()[1] or b.get_bottom()[1] > a.get_top()[1]:
        s, e = (a.get_bottom(), b.get_top()) if d[1] < 0 else (a.get_top(), b.get_bottom())
        mid = (s[1] + e[1]) / 2
        corners = [s, np.array([s[0], mid, 0]), np.array([e[0], mid, 0]), e]
    else:
        s, e = (a.get_right(), b.get_left()) if d[0] > 0 else (a.get_left(), b.get_right())
        mid = (s[0] + e[0]) / 2
        corners = [s, np.array([mid, s[1], 0]), np.array([mid, e[1], 0]), e]
    path = TipableVMobject(stroke_color=color, stroke_width=stroke)
    path.start_new_path(corners[0])
    for prev, corner, nxt in zip(corners, corners[1:], corners[2:]):
        r = min(radius, np.linalg.norm(corner - prev) / 2, np.linalg.norm(nxt - corner) / 2)
        if r < 1e-3:
            continue
        before = corner - r * (corner - prev) / np.linalg.norm(corner - prev)
        after = corner + r * (nxt - corner) / np.linalg.norm(nxt - corner)
        path.add_line_to(before)
        path.add_cubic_bezier_curve_to(before + (corner - before) * 0.55, after + (corner - after) * 0.55, after)
    path.add_line_to(corners[-1] - (corners[-1] - corners[-2]) / (np.linalg.norm(corners[-1] - corners[-2]) or 1) * 0.06)
    return path.add_tip(tip_shape=StealthTip, tip_length=TIP)


def pipeline(steps, color=SKY, direction=RIGHT, buff: float = 1.0, size: float = 26, arrow_color=SUBTLE) -> VGroup:
    """Steps joined by arrows: a flow from left to right (or down with direction=DOWN).

    A step is a string (drawn as a box) or any mobject. [0] the steps, [1] the arrows.
    """
    nodes = VGroup(*[box(s, color, size) if isinstance(s, str) else s for s in steps]).arrange(direction, buff=buff)
    arrows = VGroup(*[connect(a, b, arrow_color) for a, b in zip(nodes, nodes[1:])])
    return VGroup(nodes, arrows)


def _loop(start, color, w: float = 0.6, h: float = 0.4) -> TipableVMobject:
    """A message from a lifeline back to itself: right, down, and back left, with rounded corners."""
    s = np.array(start, dtype=float)
    corners = [s, s + RIGHT * w, s + RIGHT * w + DOWN * h, s + DOWN * h + RIGHT * 0.06]
    path = TipableVMobject(stroke_color=color, stroke_width=STROKE)
    path.start_new_path(corners[0])
    for prev, corner, nxt in zip(corners, corners[1:], corners[2:]):
        before = corner - 0.12 * (corner - prev) / np.linalg.norm(corner - prev)
        after = corner + 0.12 * (nxt - corner) / np.linalg.norm(nxt - corner)
        path.add_line_to(before)
        path.add_cubic_bezier_curve_to(before + (corner - before) * 0.55, after + (corner - after) * 0.55, after)
    path.add_line_to(corners[-1])
    return path.add_tip(tip_shape=StealthTip, tip_length=0.16)


def sequence(actors, messages, width: float = 12, step: float = 0.85, size: float = SMALL_SIZE) -> VGroup:
    """A sequence diagram: actors across the top, a lifeline under each, messages between them.

    actors: names or (name, colour) pairs. messages: (from, to, text) with actor names or
    indexes; from == to draws a return to itself. [0] actors, [1] lifelines, [2] messages;
    [2][i] is VGroup(arrow, text). Show a message with Create(m[0]) and FadeIn(m[1]).
    """
    from explainer.theme import ACCENTS

    pairs = [(a, ACCENTS[i % len(ACCENTS)]) if isinstance(a, str) else a for i, a in enumerate(actors)]
    heads = VGroup(*[box(name, c, size + 2) for name, c in pairs])
    gap = width / max(len(heads) - 1, 1)
    for i, h in enumerate(heads):
        h.move_to(RIGHT * (i * gap - width / 2))
    names = [name for name, _ in pairs]
    depth = step * (len(messages) + 0.6)
    lifelines = VGroup(*[DashedLine(h.get_bottom(), h.get_bottom() + DOWN * depth, color=LINE, stroke_width=2,
                                    dash_length=0.1) for h in heads])
    arrows = VGroup()
    for k, (src, dst, text) in enumerate(messages):
        i = names.index(src) if isinstance(src, str) else src
        j = names.index(dst) if isinstance(dst, str) else dst
        y = heads[0].get_bottom()[1] - step * (k + 1)
        x0, x1 = lifelines[i].get_center()[0], lifelines[j].get_center()[0]
        color = pairs[i][1]
        if i == j:
            arrow = _loop([x0, y + 0.2, 0], color)
            words = label(text, size, INK, width=max(gap - 1.0, 2.0)).next_to(arrow, RIGHT, buff=0.15)
        else:
            arrow = Arrow([x0, y, 0], [x1, y, 0], buff=0.08, color=color, stroke_width=STROKE, tip_shape=StealthTip,
                          tip_length=TIP, max_tip_length_to_length_ratio=0.3, max_stroke_width_to_length_ratio=10)
            # Long text wraps onto more lines rather than shrinking.
            words = label(text, size, INK, width=abs(x1 - x0) - 0.3).next_to(arrow, UP, buff=0.08)
        arrows.add(VGroup(arrow, words))
    return VGroup(heads, lifelines, arrows)


def timeline(events, color=SKY, width: float = 11, size: float = SMALL_SIZE) -> VGroup:
    """Events in order along a line. events: (date, text) pairs.

    [0] the line, [1] the events; [1][i] is VGroup(dot, date, text).
    """
    if not events:
        raise ValueError("timeline() needs at least one (date, text) event")
    axis = Line(LEFT * width / 2, RIGHT * width / 2, stroke_color=LINE, stroke_width=3)
    gap = width / len(events)
    marks = VGroup()
    for i, (date, text) in enumerate(events):
        x = -width / 2 + gap * (i + 0.5)
        dot = Dot([x, 0, 0], radius=0.09, color=color).set_stroke(color, width=6, opacity=0.25, background=True)
        when = mono(date, size - 2, color).next_to(dot, UP, buff=0.25)
        what = label(text, size, INK, width=gap - 0.25).next_to(dot, DOWN, buff=0.25)
        marks.add(VGroup(dot, when, what))
    return VGroup(axis, marks)


def tree(edges, color=SKY, root=None, width: float = 10, height: float = 4.5, size: float = SMALL_SIZE) -> VGroup:
    """A tree of tags from (parent, child) pairs, laid out top-down from `root` (default: the first parent).

    [0] the edges, [1] the nodes. Find a node with t.node(name).
    """
    names = list(dict.fromkeys([n for e in edges for n in e]))
    layout = Graph(names, list(edges), layout="tree", root_vertex=root or edges[0][0])
    spots = {n: layout[n].get_center() for n in names}
    xs, ys = [p[0] for p in spots.values()], [p[1] for p in spots.values()]
    sx = width / ((max(xs) - min(xs)) or 1)
    sy = height / ((max(ys) - min(ys)) or 1)
    nodes = VGroup()
    by_name = {}
    for n in names:
        p = spots[n]
        tag = pill(str(n), color, size).move_to([(p[0] - (max(xs) + min(xs)) / 2) * sx, (p[1] - (max(ys) + min(ys)) / 2) * sy, 0])
        by_name[n] = tag
        nodes.add(tag)
    lines = VGroup(*[Line(by_name[a].get_bottom(), by_name[b].get_top(), stroke_color=LINE, stroke_width=2.5) for a, b in edges])
    group = VGroup(lines, nodes)
    group.node = by_name.__getitem__
    return group


def callout(target, text: str, color=AMBER, direction=UR, distance: float = 0.8, size: float = SMALL_SIZE,
            width: float | None = 4) -> VGroup:
    """A note with a leader line to the edge of `target`. The note sits `distance` units from that
    edge point in `direction` (UP, DR, LEFT...), moved back inside the frame if it would leave it.

    [0] line, [1] dot, [2] text.
    """
    from manim import config

    d = np.array(direction, dtype=float)
    anchor = _edge_point(target, d)
    words = label(text, size, color, width=width).next_to(anchor, d, buff=distance)
    hw, hh = config.frame_width / 2 - 0.3, config.frame_height / 2 - 0.3
    words.shift(RIGHT * (max(0, -hw - words.get_left()[0]) - max(0, words.get_right()[0] - hw))
                + UP * (max(0, -hh - words.get_bottom()[1]) - max(0, words.get_top()[1] - hh)))
    end = _edge_point(words, anchor - words.get_center())
    dot = Dot(anchor, radius=0.06, color=color)
    return VGroup(Line(anchor, end, stroke_color=color, stroke_width=2), dot, words)


def brace_label(m, text: str, direction=DOWN, color=SUBTLE, size: float = SMALL_SIZE) -> VGroup:
    """A brace along one side of m with a label at its tip. [0] brace, [1] text."""
    brace = Brace(m, direction, color=color, buff=0.15)
    words = label(text, size, color)
    brace.put_at_tip(words)
    return VGroup(brace, words)


def compare(left, right, titles=("Before", "After"), colors=(CORAL, MINT), gap: float = 1.4, size: float = 30) -> VGroup:
    """Two things side by side with headings and a divider. [0] left (heading, thing), [1] divider, [2] right."""
    sides = []
    for thing, name, c in ((left, titles[0], colors[0]), (right, titles[1], colors[1])):
        sides.append(VGroup(label(name, size, c, weight="SEMIBOLD"), thing).arrange(DOWN, buff=0.45))
    row = VGroup(sides[0], sides[1]).arrange(RIGHT, buff=gap * 2, aligned_edge=UP)
    divider = Line(UP, DOWN, stroke_color=LINE, stroke_width=2).stretch_to_fit_height(row.height + 0.4).move_to(row)
    divider.set_x((sides[0].get_right()[0] + sides[1].get_left()[0]) / 2)
    return VGroup(sides[0], divider, sides[1])
