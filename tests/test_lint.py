from explainer.kit import *


def check(*mobjects, zoom=1.0, span=False):
    scene = ExplainerScene()
    scene.setup()
    scene.camera.frame.scale(1 / zoom)
    scene.add(*mobjects)
    scene._lint.check_span() if span else scene._lint.check()
    return "\n".join(scene._lint.lines)


def test_clean_layout_has_no_warnings():
    a, b = box("Planner", ORANGE).shift(LEFT * 3), box("Index", BLUE_C).shift(RIGHT * 3)
    arrow = connect(a, b)
    assert check(a, b, arrow, arrow_label(arrow, "searches"), table([["A", "B"], ["1", "2"]], BLUE_C).shift(DOWN * 2)) == ""


def test_off_frame():
    assert "past the frame edge" in check(label("far away").move_to(RIGHT * 8))


def test_zoomed_in_allows_off_frame():
    assert check(label("far away").move_to(RIGHT * 5), zoom=2) == ""


def test_text_on_text():
    a = label("overlap one")
    assert "overlaps" in check(a, label("overlap two").move_to(a).shift(RIGHT * 0.3))


def test_small_text():
    assert "font size 12" in check(label("tiny", 12))


def test_small_after_zoom_out():
    assert "font size" in check(label("fine at normal zoom", 24), zoom=0.5)


def test_arrow_through_text():
    assert "an arrow crosses" in check(Arrow(LEFT * 3, RIGHT * 3), label("in the way"))


def test_text_straddling_a_box():
    frame = Rectangle(width=2, height=1)
    assert "partly covered" in check(frame, label("half in").move_to(frame.get_right()))


def test_lint_ok_skips():
    far = label("far away").move_to(RIGHT * 8)
    far.lint_ok = True
    assert check(far) == ""


def test_highlight_around_part_of_an_equation_is_fine():
    eq = MathTex("a^2", "+", "b^2")
    assert check(eq, highlight(eq[0])) == ""


def test_small_content():
    assert "spans only" in check(box("a", SKY), box("b", MINT).shift(RIGHT), span=True)


def test_large_content_and_a_lone_object_pass():
    assert check(box("a", SKY).shift(LEFT * 4), box("b", MINT).shift(RIGHT * 4), span=True) == ""
    assert check(label("?", 96), span=True) == ""


def test_wait_placeholder_is_not_visible():
    from explainer.lint import visible

    assert not visible(Mobject())


def test_value_tracker_is_not_visible():
    from explainer.lint import visible

    assert not visible(ValueTracker(250))


def test_dashed_curved_and_elbow_arrows_through_text():
    words = label("in the way")
    assert "an arrow crosses" in check(connect(LEFT * 3, RIGHT * 3, dashed=True), words)
    a, b = Square(0.5).shift(LEFT * 3 + UP * 0.4), Square(0.5).shift(RIGHT * 3 + DOWN * 0.4)
    assert "an arrow crosses" in check(a, b, elbow(a, b), label("x" * 12).move_to(ORIGIN))


def test_one_headline_object_passes_span():
    assert check(stat(42, "agreed"), span=True) == ""
