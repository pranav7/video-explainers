# Build an explainer video from script.md

You get a `script.md` file. It has a palette and chapters. Each chapter has lines of
narration, and under each line, a description of the picture. Build `video.mp4` in
the same directory. Run every command from that directory.

This guide and the API reference at its end are complete. Do not read the package
source.

## 1. Write video.py

Write one file, `video.py`. Do not name it `explainer.py`: that name hides the
`explainer` package.

- Start it with `from explainer.kit import *`. This import gives Manim, the scene
  API, and the kit helpers in the API reference that follows.
- Make one constant for each palette entry, for example `DOC = SKY`. Use the theme's
  accent colours. For neutral things, use `SUBTLE`, `FAINT` or `INK`, not an accent.
- Make one `ExplainerScene` subclass for each chapter, in the order of the chapters.
  Use the chapter's scene name as the class name, and its title as `title`.
- Make each narration line one `self.say(...)` call or one `with self.narrate(...)`
  block. Copy the narration text exactly.
- End each scene with `self.fade_all()`.

```python
from explainer.kit import *

APP, DB, SLOW = SKY, VIOLET, CORAL


class OneQueryPerRow(ExplainerScene):
    title = "One query for every row"

    def construct(self):
        app = box("API server", APP, icon_name="server").to_edge(LEFT, buff=1.2)
        db = box("Database", DB, icon_name="database").to_edge(RIGHT, buff=1.2)
        self.say("The page asks the server for a list of fifty orders.", appear(app, db), at="server")

        query = connect(app, db, APP)
        with self.narrate("Then the server asks the database once for each order: fifty round trips.") as t:
            self.play(GrowArrow(query), run_time=0.8)
            t.wait_until("fifty")
            self.play(LaggedStart(*[travel(query, APP) for _ in range(5)], lag_ratio=0.3),
                      run_time=t.remaining(1.5))
        cost = stat(50, "queries for one page", SLOW).next_to(query, DOWN, buff=0.8)
        self.say("Fifty queries, for one page.", appear(cost), Circumscribe(cost[0], color=SLOW))
        self.fade_all()
```

Use `self.say` for a beat with one group of animations. Use `with self.narrate(...)`
for a beat with animations at different words.

### Make it clear and engaging

- **Use the kit first.** Before you draw a shape by hand, look for a helper in the API
  reference: cards (`box`), tags (`pill`, `badge`), `table`, `code`, `pipeline`,
  `sequence`, `timeline`, `tree`, `callout`, `bars`, `stat`, `number`, `compare`, and Lucide icons
  (`icon`). The helpers share one look, so the video looks consistent.
- **Enter with `appear(...)`.** It fades in, rises slightly and settles, and staggers
  several objects. Use `disappear(...)` to remove objects mid-scene.
- **Show movement along a connector with `flow(arrow)`.**
- **Point the viewer with `self.focus(m)`.** It dims everything else. Undo it with
  `self.unfocus()`.

- **Fill the frame.** The frame is approximately 14.2 by 8 units. Make the main
  diagram 60 to 80 percent of the frame width. Use font size 24 or more for labels.
- **Change the picture on every line.** Something moves, appears, or changes colour
  while each line plays.
- **Point at what the narration names.** On the word, use `Indicate`, `Circumscribe`,
  `Flash`, or a colour change (`at="word"`, or `t.wait_until("word")`).
- **Zoom instead of redraw.** To show a detail, move the camera to it, and then back:
  `self.camera.frame.animate.scale(0.5).move_to(m)`, then `.scale(2).move_to(ORIGIN)`.
  Objects that you add while zoomed in look larger by the zoom factor, so scale them
  down by the same factor (`.scale(0.5)` for a zoom of 2).
- **Transform, do not cut.** Go from one state to the next with `Transform`,
  `ReplacementTransform`, and `TransformMatchingTex`. The viewer sees where each
  thing came from.
- **Show numbers as they are.** Put a figure on screen with `appear(number(45))` or
  `appear(stat(45, "sales"))`. Do not count up from zero: it looks awkward and adds
  nothing. When a value changes from one real state to another (2 rows, then 10), turn
  the old number into the new one with `Transform`.
- **Keep one idea on screen.** Fade out each object when the narration has finished
  with it.
- **One colour for each concept.** Use the palette for the whole video.
- **Draw, do not list.** Do not make title cards with bullet lists.
- **Split equations into parts** (`MathTex("a^2", "+", "b^2")`), so that you can colour
  and transform each part.
- **Lay out with `arrange` and `next_to`,** not with coordinates that you calculate.

`ExplainerScene` is a Manim `MovingCameraScene`, so `self.camera.frame` can pan and
zoom. For a scene with 3D, use `class X(NarrationMixin, ThreeDScene)`. The layout
check does not examine 3D scenes.

## 2. Preview

```bash
explainer render video.py
```

This command renders all scenes in parallel at 480p, joins them into `video.mp4`,
and prints the layout check. If a scene fails, the output shows the line in
`video.py` and the exception. Output from `print()` in `video.py` goes to
`media/logs/<Scene>.log`. All failures show in one run, so fix all of them
before the next run.

Fix each layout warning. If a warning is a false alarm, set `m.lint_ok = True` on that
mobject, and give the reason in your report.

## 3. Look at the video

```bash
explainer frames video.mp4
```

This command makes contact sheets in `media/frames/`. Each tile shows the picture at
the end of one narration line. Read each sheet, and look for these problems:

- A small diagram in a large empty frame.
- More than one idea on screen.
- A picture that does not match its line.
- A colour that is not in the palette.

To examine one moment at full size, run
`ffmpeg -ss <seconds> -i video.mp4 -frames:v 1 still.png`, and then read the still.

To render again after you fix a problem, name only the scenes that you changed:
`explainer render video.py SceneA SceneB`. The command joins the full video again.
Then run `explainer frames video.mp4 SceneA SceneB` to see only their tiles.

Do a maximum of two rounds of fixes. Then go to the final render, and report the
problems that remain.

## 4. Final render

```bash
explainer render video.py -q h
```

This command renders all scenes at 1080p60. The video has chapter markers. If the
request asks for captions, add `--captions`: the video then has a caption track, and
the captions are also in `video.srt`.

Report the video path, the duration, and each warning that you left in place.

## Common mistakes

| Mistake | Fix |
| --- | --- |
| Long animations with a fixed `run_time`, so speech and picture drift apart | Use `t.remaining()` and `t.wait_until()` |
| An object placed at calculated coordinates collides with another | Use `arrange` and `next_to`, and read the layout check |
| `MathTex` fails with a LaTeX error | Run `explainer doctor`. Check that the TeX string compiles |
| `Error processing file '/Users/runner/work/espeakng-loader/...'` | Kokoro was imported outside `explainer.tts`. Synthesize only through the scene API or `explainer say` |
| Import errors when you run `manim` or `python` directly | Use `explainer render`. It runs Manim inside the toolchain environment |
| A render at `-q h` on each round | Preview at the default quality. Render at `-q h` one time, at the end |
| Two animations on the same object in one `play` (for example `appear(chart)` and `GrowFromEdge(chart[0][2], LEFT)`, or `FadeIn(x)` and `Indicate(x)`) | The last one wins, or the object never appears. Animate different parts, or play them one after the other |
| Text inside a box disappears after an animation | `AnimationGroup` or `LaggedStart` of parts of an on-screen group (`box[0].animate...`) draws those parts again on top. Animate the whole group, or pass the part animations to `self.play` directly |
| `LaggedStartMap(GrowArrow, arrows)` fails with "object has no attribute 'hex'" | Use `LaggedStart(*[GrowArrow(a) for a in arrows])` |
| A number counts up from zero | Show the number with `appear()`. Use `Transform` for a real change of value |
| A number drawn with `Integer` or `DecimalNumber` shows in a serif font | Use `number()` |
