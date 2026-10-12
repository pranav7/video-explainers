import numpy as np
import pytest

from explainer.kit import *


def test_theme_fonts_installed():
    assert SANS == "Inter" and MONO == "JetBrains Mono NL"  # `explainer doctor` installs them


def test_lines_of_keeps_indentation():
    lines = lines_of("def f():\n    return 1\n\nend")
    assert len(lines) == 4
    assert lines[1].get_left()[0] > lines[0].get_left()[0] + 0.3
    assert lines[3].get_left()[0] == pytest.approx(lines[0].get_left()[0], abs=0.01)
    assert lines[2].get_fill_opacity() == 0  # a blank line holds its place but does not show


def test_code_colours_tokens_and_keeps_indentation():
    c = code("def f(x):\n    return x + 1\n")
    lines = c[1]
    assert len(lines) == 2
    assert lines[1].get_left()[0] > lines[0].get_left()[0] + 0.3
    colours = {sm.get_fill_color().to_hex() for sm in lines[0].family_members_with_points()}
    assert len(colours) > 1  # "def" and "f" have different colours
    bar = code_line(c, 1)
    assert bar.get_center()[1] == pytest.approx(lines[1].get_center()[1], abs=0.01)


def test_table_cells():
    t = table([["A", "B"], ["1", ("2", CORAL)]], SKY)
    assert len(t) == 2 and len(t[1]) == 2
    assert t[0][0][0].get_fill_color() == tint(SKY, 0.2)  # header row is tinted
    assert t[1][1][1][0].get_fill_color() == ManimColor(CORAL)  # the glyphs carry the colour
    assert t[0][1].get_center()[0] == pytest.approx(t[1][1].get_center()[0], abs=0.01)  # columns line up


def test_connect_meets_the_edges():
    a, b = Square(2).shift(LEFT * 3), Square(2).shift(RIGHT * 3)
    arrow = connect(a, b, buff=0)
    assert np.allclose(arrow.get_start(), [-2, 0, 0], atol=0.05)
    assert np.allclose(arrow.get_end(), [2, 0, 0], atol=0.05)


def test_connect_dashed_curved_and_points():
    assert connect(LEFT, RIGHT, dashed=True).get_length() > 1.5
    assert connect(Square().shift(LEFT * 3), Square().shift(RIGHT * 3), curve=0.6).height > 0.3


def test_elbow_goes_vertical_when_b_is_below():
    a, b = Square(1).shift(UP * 2 + LEFT * 3), Square(1).shift(DOWN * 2 + RIGHT * 3)
    e = elbow(a, b)
    assert np.allclose(e.get_start(), a.get_bottom(), atol=0.01)
    assert np.linalg.norm(e.get_end() - b.get_top()) < 0.3


def test_box_fits_its_text_and_width():
    b = box("Planner", PEACH, sub="picks a folder", icon_name="bot", width=4)
    assert b[0].width == pytest.approx(4)
    assert b[1].width < b[0].width


def test_icon_by_name_and_close_match_error():
    assert icon("database").height == pytest.approx(0.6)
    with pytest.raises(ValueError, match="database"):
        icon("databse")


def test_sequence_places_messages_between_lifelines():
    s = sequence(["A", "B", "C"], [("A", "C", "ask"), ("C", "C", "think"), (2, 0, "answer")])
    actors, lifelines, messages = s
    assert len(messages) == 3
    first = messages[0][0]
    assert first.get_start()[0] == pytest.approx(lifelines[0].get_center()[0], abs=0.15)
    assert first.get_end()[0] == pytest.approx(lifelines[2].get_center()[0], abs=0.15)
    assert messages[1][0].get_center()[1] < first.get_center()[1]  # later messages sit lower


def test_tree_lays_out_top_down():
    t = tree([("root", "a"), ("root", "b"), ("a", "c")])
    assert t.node("root").get_center()[1] > t.node("a").get_center()[1] > t.node("c").get_center()[1]


def test_number_uses_the_kit_font():
    n = number(208)
    assert isinstance(n[0], Text) and len(n) == 3


def test_every_helper_builds():
    a, b = box("A", SKY), box("B", MINT).shift(RIGHT * 4)
    arrow = connect(a, b)
    parts = [
        label("wrapped text that is long", width=3), mono("x = 1"), title("Heading"),
        pill("PENDING", AMBER), pill("FAIL", CORAL, filled=True), badge(1), panel(["a", ("b", CORAL)], heading="file.py"),
        folder("invoices", SKY, ["61 files"]), squares(45, 9, VIOLET), bar(17, 20, MINT),
        bars([("found", 17), ("matched", 22, MINT)]), stat(2, "agreed"), legend([(MINT, "agreed"), (CORAL, "exception")]),
        checklist([("read", True), ("rule", False), ("write", None)]), bubble("a comment"), tick(), xmark(),
        highlight(a), strike(a), arrow_label(arrow, "searches"), pipeline(["read", "rules", "result"]),
        timeline([("9 Oct", "run one"), ("12 Oct", "run two")]), callout(a, "this one"), brace_label(a, "width"),
        compare(box("x", CORAL), box("y", MINT)), window(label("inside")),
    ]
    assert all(p.width > 0 for p in parts)
    assert label("wrapped text that is long", width=3).width <= 3.2
    assert appear(a, b) and disappear(a) and flow(arrow)


def test_fit_only_scales_down():
    big, small = Rectangle(width=20, height=2), Rectangle(width=2, height=2)
    assert fit(big).width == pytest.approx(12.8)
    assert fit(small).width == pytest.approx(2)


def test_code_edit_keeps_moves_and_adds_lines():
    from manim import AnimationGroup

    old = code("def f(x):\n    return x\n")
    new, anim = code_edit(old, "def f(x):\n    x = x + 1\n    return x\n")
    assert isinstance(anim, AnimationGroup)
    assert new.source == ["def f(x):", "    x = x + 1", "    return x"]
    assert new.get_corner(UL) == pytest.approx(old.get_corner(UL), abs=0.01)


def test_recolor_glow_travel():
    b, p = box("step", AMBER), pill("PENDING", AMBER)
    assert recolor(b, MINT) and recolor(p, MINT)
    assert len(glow(b)) == 3
    arrow = connect(LEFT * 2, RIGHT * 2)
    assert travel(arrow) and travel(arrow, text="order 88") and travel(connect(LEFT, RIGHT, dashed=True))


def test_part_finds_words_by_position():
    t = label("match by PO number, then by sales order")
    p = part(t, "PO number")
    assert len(p) == len("POnumber,") - 1
    assert p.get_left()[0] > t.get_left()[0] and p.get_right()[0] < t.get_right()[0]
    assert len(part(t, "by", occurrence=2)) == 2


def test_window_heading_clears_the_dots():
    w = panel(["x"], heading="a/long/file/name.py")
    dots, heading = w[0][3], w[0][5]
    assert heading.get_left()[0] > dots.get_right()[0]


def test_callout_stays_in_frame():
    near_edge = box("edge", SKY).to_edge(RIGHT, buff=0.2)
    note = callout(near_edge, "a note that would leave the frame", direction=RIGHT)
    assert note[2].get_right()[0] <= config.frame_width / 2


def test_long_sequence_message_wraps():
    s = sequence(["A", "B"], [("A", "B", "retry after 30 seconds, because the server is busy right now")], width=5)
    words = s[2][0][1]
    assert words.font_size >= 20 and words.width <= 5


def test_window_title_bar_stays_inside_the_rounded_body():
    w = panel(["x"], heading="terminal")
    body, bar = w[0][0], w[0][1]
    assert bar.get_left()[0] > body.get_left()[0] and bar.get_right()[0] < body.get_right()[0]
    assert len(bar.points) > 16  # the top corners are rounded
    scene = ExplainerScene()
    scene.setup()
    scene.add(w)
    scene._lint.check()
    assert scene._lint.lines == []


def test_label_wrap_keeps_line_breaks_and_words():
    t = label("line one\nline two", width=20)
    assert t.original_text == "line one\nline two"
    t = label("internationalization of things", width=1)
    assert "internationalization" in t.original_text


def test_flow_and_label_on_dashed_connectors():
    dashed = connect(LEFT * 2, RIGHT * 2, dashed=True)
    assert flow(dashed) and arrow_label(dashed, "maybe")


def test_edge_inputs_raise_clear_errors():
    with pytest.raises(ValueError, match="at least one"):
        timeline([])
    with pytest.raises(ValueError, match="at least one"):
        bars([])
    assert bars([("a", 0), ("b", 0)]) and bar(0, 0, MINT)


def test_numbers_show_with_separators():
    chart = bars([("start", 1_000_000), ("guess 4", 62_500)])
    assert [r[3].original_text for r in chart] == ["1,000,000", "62,500"]
    assert bar(17, 20, MINT)[2].original_text == "17 of 20"
