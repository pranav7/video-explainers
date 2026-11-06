"""A continuous search diagram for the local voice and motion comparison."""

from explainer.kit import *


class SkipWork(ExplainerScene):
    title = "Use order to skip work"

    def construct(self):
        step = 0.35

        def x(value):
            return (value - 16.5) * step

        def interval(lo, hi):
            return RoundedRectangle(
                width=(hi - lo) * step + 0.36,
                height=1.05,
                corner_radius=0.1,
                stroke_color=SKY,
                stroke_width=2.5,
                fill_opacity=0,
            ).move_to([x((lo + hi) / 2), 0, 0])

        marks = VGroup(*[
            Rectangle(width=0.24, height=0.65, fill_color=SKY,
                      fill_opacity=0.85, stroke_width=0).move_to([x(value), 0, 0])
            for value in range(1, 33)
        ])
        bounds = VGroup(
            mono("1", 26, SUBTLE).move_to([x(1), -0.95, 0]),
            mono("32", 26, SUBTLE).move_to([x(32), -0.95, 0]),
        )
        heading = label("FIND 23", 48, INK, weight="SEMIBOLD").move_to([-3.7, 2.6, 0])
        count = label("32 sorted values", 30, SUBTLE).move_to([3.3, 2.6, 0])
        active = interval(1, 32)
        cursor = RoundedRectangle(width=0.34, height=0.87, corner_radius=0.06,
                                  stroke_color=AMBER, stroke_width=3,
                                  fill_opacity=0).move_to(marks[15])
        current = mono("16", 34, AMBER).move_to([x(16), 1.05, 0])
        status = label("32 remain", 30, SUBTLE).move_to([1.1, -1.15, 0])
        trail = VGroup()

        def record(value, index):
            entry = mono(str(value), 34, MINT if value == 23 else SUBTLE)
            entry.move_to([-3.4 + index * 1.7, -2.15, 0])
            animations = [FadeIn(entry, shift=UP * 0.15)]
            trail.add(entry)
            if index:
                link = Arrow(trail[-2].get_right() + RIGHT * 0.16,
                             entry.get_left() + LEFT * 0.16,
                             buff=0, color=FAINT, stroke_width=2,
                             max_tip_length_to_length_ratio=0.18)
                animations.append(GrowArrow(link))
            return animations

        def compare(value, lo, hi, removed, index, caption):
            nonlocal status
            new_status = label(caption, 30, SUBTLE).move_to([1.1, -1.15, 0])
            animations = [
                cursor.animate.move_to(marks[value - 1]),
                Transform(current, mono(str(value), 34, AMBER).move_to([x(value), 1.05, 0])),
            ]
            self.play(*animations, run_time=0.45)
            if removed:
                self.play(
                    *[marks[i - 1].animate.shift(DOWN * 0.18).set_fill(FAINT, 0.2) for i in removed],
                    Transform(active, interval(lo, hi)),
                    *record(value, index),
                    FadeOut(status), FadeIn(new_status),
                    run_time=0.7,
                )
            status = new_status

        with self.narrate("Thirty-two sorted values. We want twenty-three. "
                          "Do we have to check every value?") as t:
            self.play(FadeIn(heading), FadeIn(count),
                      LaggedStart(*[GrowFromEdge(mark, DOWN) for mark in marks], lag_ratio=0.025),
                      FadeIn(bounds), FadeIn(status), run_time=1.1)
            t.wait_until("twenty-three")
            self.play(Indicate(heading, color=AMBER, scale_factor=1.06), run_time=0.5)
            t.wait_until("every")
            self.play(Create(active), run_time=0.65)

        with self.narrate("Start in the middle. Sixteen is too low, "
                          "so discard the entire lower half.") as t:
            self.play(Create(cursor), FadeIn(current), run_time=0.6)
            t.wait_until("discard")
            compare(16, 17, 32, range(1, 17), 0, "16 remain")
            self.play(self.camera.frame.animate.scale(0.88).move_to([0.4, 0, 0]), run_time=0.5)

        with self.narrate("Twenty-four is too high. Keep only the gap between them.") as t:
            compare(24, 17, 23, range(24, 33), 1, "7 remain")
            t.wait_until("gap")
            self.play(Indicate(active, scale_factor=1.03, color=SKY), run_time=0.65)

        with self.narrate("Twenty is too low. Twenty-two is still too low. "
                          "Try twenty-three. Found.") as t:
            compare(20, 21, 23, range(17, 21), 2, "3 remain")
            t.wait_until("twenty-two")
            compare(22, 23, 23, range(21, 23), 3, "1 remains")
            t.wait_until("twenty-three")
            self.play(cursor.animate.move_to(marks[22]),
                      Transform(current, mono("23", 34, AMBER).move_to([x(23), 1.05, 0])),
                      *record(23, 4), run_time=0.45)
            t.wait_until("found")
            self.play(marks[22].animate.set_fill(MINT, 1),
                      cursor.animate.set_stroke(MINT), active.animate.set_stroke(MINT),
                      current.animate.set_color(MINT), run_time=0.4)

        with self.narrate("Five comparisons. Binary search cuts the remaining range roughly in half. "
                          "Ordered indexes in SQL also use order to skip work.") as t:
            self.play(self.camera.frame.animate.scale(1 / 0.88).move_to(ORIGIN),
                      Transform(heading, label("5 comparisons", 48, MINT, weight="SEMIBOLD")
                                .move_to([-3.3, 2.6, 0])),
                      FadeOut(count), FadeOut(status), FadeOut(bounds), run_time=0.9)
            t.wait_until("half")
            self.play(LaggedStart(*[Indicate(entry, color=MINT, scale_factor=1.12) for entry in trail],
                                 lag_ratio=0.16), run_time=1.2)
            t.wait_until("SQL")
            takeaway = label("Use order to skip work", 34, INK, weight="MEDIUM").move_to([0, -3.1, 0])
            self.play(FadeIn(takeaway, shift=UP * 0.15), run_time=0.7)
        self.fade_all()
