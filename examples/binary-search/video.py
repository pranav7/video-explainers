from explainer.kit import *
from manim import Intersection

RANGE, GUESS, OUT, ANSWER, RESULT = SKY, AMBER, FAINT, VIOLET, MINT

BAR_W, BAR_H, BAR_Y = 11.0, 0.7, 0.3
ZOOM, SHRINK = 0.6, 0.7


def x_of(value):
    """The x position of a value between 0 and 1,000,000 on the bar."""
    return -BAR_W / 2 + BAR_W * value / 1_000_000


def range_bar():
    bar = RoundedRectangle(width=BAR_W, height=BAR_H, corner_radius=BAR_H / 2)
    bar.set_fill(RANGE, 0.9).set_stroke(width=0).move_to(UP * BAR_Y)
    lo = mono("1", 28, SUBTLE).next_to(bar.get_left(), DOWN, buff=0.45)
    hi = mono("1,000,000", 28, SUBTLE).next_to(bar.get_right(), DOWN, buff=0.45)
    return bar, lo, hi


def ruled_out(bar, a, b):
    """The part of the bar from value a to value b, in the ruled-out colour."""
    cut = Rectangle(width=x_of(b) - x_of(a), height=BAR_H * 2).move_to([(x_of(a) + x_of(b)) / 2, BAR_Y, 0])
    return Intersection(bar, cut).set_fill(OUT, 1).set_stroke(width=0)


def marker(text, value):
    """An amber arrow that points down at a value, with its tag above."""
    tip = [x_of(value), BAR_Y + BAR_H / 2 + 0.08, 0]
    arrow = Arrow(tip + UP * 0.9, tip, buff=0, color=GUESS, stroke_width=6,
                  max_tip_length_to_length_ratio=0.35)
    tag = pill(text, GUESS, size=30, font=MONO).next_to(arrow, UP, buff=0.12)
    return VGroup(tag, arrow)


def reply(text, mark):
    tag = pill(text, ANSWER, size=30, filled=True).match_height(mark[0])
    return tag.next_to(mark[0], RIGHT, buff=0.25 * mark[0].height / 0.55)


class Hook(ExplainerScene):
    title = "Twenty guesses for a million"

    def construct(self):
        bar, lo, hi = range_bar()
        guesses = pill("20 guesses", GUESS, size=30, filled=True).next_to(bar, UP, buff=0.7)
        with self.narrate("Pick a number between one and a million. I can find it in twenty guesses.") as t:
            self.play(appear(bar, lo, hi), run_time=1.0)
            t.wait_until("twenty")
            self.play(appear(guesses), run_time=0.8)

        person = avatar("user", SUBTLE, size=1.1).move_to([-5.0, -2.8, 0])
        said = bubble("higher", ANSWER, size=34).next_to(person, RIGHT, buff=0.2).align_to(person, DOWN)
        with self.narrate("After each guess, you only tell me higher or lower.") as t:
            self.play(appear(person), run_time=0.6)
            t.wait_until("higher")
            self.play(appear(said), run_time=0.5)
            t.wait_until("lower")
            self.play(Transform(said[1], label("lower", 34, ANSWER).move_to(said[1])), run_time=0.4)
        self.fade_all()


class Halving(ExplainerScene):
    title = "Cut the range in half"

    def construct(self):
        bar, lo, hi = range_bar()
        mark = marker("500,000", 500_000)
        with self.narrate("My first guess is the middle: five hundred thousand.") as t:
            self.play(appear(bar, lo, hi), run_time=0.8)
            t.wait_until("middle")
            self.play(FadeIn(mark, shift=DOWN * 0.6), run_time=0.6)

        no = reply("lower", mark)
        right_half = ruled_out(bar, 500_000, 1_000_000)
        with self.narrate("Lower. In one guess, half of the numbers are gone.") as t:
            self.play(appear(no), run_time=0.5)
            t.wait_until("half")
            self.play(FadeIn(right_half), hi.animate.set_color(OUT), run_time=t.remaining(0.8))

        frame = self.camera.frame
        with self.narrate("Next, the middle of what is left: two hundred and fifty thousand.") as t:
            self.play(disappear(no), frame.animate.scale(ZOOM).move_to([x_of(250_000), BAR_Y + 0.4, 0]),
                      mark.animate.scale(SHRINK, about_point=mark[1].get_end()), run_time=1.0)
            t.wait_until("middle")
            self.play(mark.animate.shift(RIGHT * (x_of(250_000) - x_of(500_000))), run_time=0.8)
            t.wait_until("two")
            self.play(Transform(mark[0], pill("250,000", GUESS, size=30, font=MONO).match_height(mark[0]).move_to(mark[0])),
                      run_time=0.5)

        yes = reply("higher", mark)
        left_quarter = ruled_out(bar, 0, 250_000)
        left = brace_label(Line([x_of(250_000), BAR_Y - BAR_H / 2, 0], [x_of(500_000), BAR_Y - BAR_H / 2, 0]),
                           "a quarter is left", color=RANGE, size=30)
        with self.narrate("Higher. Half of what was left is gone again.") as t:
            self.play(appear(yes), run_time=0.5)
            t.wait_until("half")
            self.play(FadeIn(left_quarter), lo.animate.set_color(OUT), run_time=0.7)
            t.wait_until("gone")
            self.play(frame.animate.scale(1 / ZOOM).move_to(ORIGIN), disappear(yes),
                      mark.animate.scale(1 / SHRINK, about_point=mark[1].get_end()), run_time=1.0)
            self.play(appear(left), run_time=t.remaining(0.5))
        self.fade_all()


def halving_chart():
    sizes = [("start", 1_000_000), ("guess 1", 500_000), ("guess 2", 250_000),
             ("guess 3", 125_000), ("guess 4", 62_500)]
    chart = bars(sizes, RANGE, width=8.5, height=0.5, size=34)
    # bars() prints large values in scientific notation, so write them with commas.
    for row, (_, value) in zip(chart, sizes):
        text = label(f"{value:,}", 34, RANGE, weight="SEMIBOLD")
        text.next_to(row[1], RIGHT, buff=0.3)
        row.remove(row[3])
        row.add(text)
    return chart


class WhyTwenty(ExplainerScene):
    title = "Why twenty is enough"

    def construct(self):
        bar, lo, hi = range_bar()
        gone = VGroup(ruled_out(bar, 0, 250_000), ruled_out(bar, 500_000, 1_000_000))
        lo.set_color(OUT)
        hi.set_color(OUT)
        self.add(bar, gone, lo, hi)

        chart = halving_chart().arrange(DOWN, buff=0.45, aligned_edge=LEFT).move_to(ORIGIN)

        def grow(row):
            return AnimationGroup(appear(VGroup(row[0], row[1], row[3])), GrowFromEdge(row[2], LEFT))

        with self.narrate("Each guess halves the range. A million, five hundred thousand, "
                          "two hundred and fifty thousand, and so on.") as t:
            self.play(disappear(bar, gone, lo, hi), run_time=0.6)
            for i, word in enumerate(["million", "five", "two"]):
                t.wait_until(word)
                self.play(grow(chart[i]), run_time=0.6)
            t.wait_until("so")
            self.play(LaggedStart(*[grow(r) for r in chart[3:]], lag_ratio=0.4), run_time=t.remaining(0.8))

        twenty = stat(20, "guesses to reach one number", RESULT, size=150)
        self.say("After twenty halvings, one number is left.", disappear(chart), appear(twenty), at="twenty")

        with self.narrate("Double the range to two million, and it takes just one more guess.") as t:
            t.wait_until("one")
            self.play(Transform(twenty[0], number(21, RESULT, size=150).move_to(twenty[0])),
                      Transform(twenty[1], label("guesses for two million numbers", color=SUBTLE)
                                .match_height(twenty[1]).move_to(twenty[1])),
                      run_time=0.6)
            self.play(Circumscribe(twenty[0], color=RESULT), run_time=t.remaining(0.8))

        src = '''def binary_search(items, target):
    lo, hi = 0, len(items) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if items[mid] == target:
            return mid
        if items[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return None'''
        window_ = code(src, heading="binary_search.py", size=26)
        thirty = stat(30, "steps for a billion items", GUESS, size=120)
        VGroup(window_, thirty).arrange(RIGHT, buff=0.9)
        fit(VGroup(window_, thirty))
        VGroup(window_, thirty).move_to(ORIGIN)
        mid = code_line(window_, 3)
        with self.narrate("This is binary search. In a sorted list of a billion items, it needs only thirty steps.") as t:
            self.play(disappear(twenty), run_time=0.4)
            self.play(appear(window_), run_time=0.8)
            t.wait_until("sorted")
            self.play(FadeIn(mid), run_time=0.5)
            t.wait_until("thirty")
            self.play(appear(thirty), run_time=0.6)
        self.fade_all()
