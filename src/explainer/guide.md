# Build an explainer video from script.md

You get a `script.md` file. It has a palette and chapters. Each chapter has narration
passages with a storyboard: objects, states, motion, and spoken cues. Build `video.mp4` in
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
- Copy each narration passage exactly into `self.say(...)` or `with self.narrate(...)`.
  Keep related sentences together so delivery stays connected. Use word cues for
  multiple visual changes within the passage.
- Keep related objects through the scene and transform their state. End the scene
  with `self.fade_all()` after its final picture has had time to register.

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

### Speech and pronunciation

Default narrator: the voice `Ellis`, made with Qwen3-TTS through MLX on Apple Silicon.
The model clones a bundled reference clip, so the clip sets the timbre, pace, and intonation.
Set the scene attributes `engine`, `voice`, and `speed` to match the script. The default speed is 1.3, and 1.0 is the voice's own pace.
`EXPLAINER_ENGINE` and `EXPLAINER_VOICE` set process defaults.
Kokoro is available with `engine = "kokoro"` and `voice = "af_heart"`.

Audition a representative passage, including difficult terms, before the render:

```bash
explainer say "The API sends one SQL query." audition.wav
afplay audition.wav
```

Keep the audition's voice and speed in the final video. Check the
rendered narration against the script. Forced alignment can assign timestamps to
incorrect speech, so a clean timing report does not verify spoken content. Local
transcription can flag content errors; listening is needed to judge delivery.
Report any review you cannot perform.

Use `pronunciations.json` in the video directory for recurring terms:

```json
{"SQL": "sequel", "API": "A P I"}
```

`EXPLAINER_PRONUNCIATIONS` selects another dictionary file. An inline alias such as
`[SQL](sequel)` changes speech while captions retain `SQL`. For a passage-specific
correction, use `with self.narrate("The API responds.", spoken="The A P I responds.")`.
Captions keep the display text. Kokoro's inline phoneme syntax is specific to that engine.

Use connected passages of two or three related sentences, with several visual
cues. The local aligner supplies word timestamps for `t.wait_until(...)`. Speech
and alignment do not require a hosted service. Run `explainer models` after setup
to prefetch pinned Qwen and aligner weights. Then
`EXPLAINER_OFFLINE=1 explainer render video.py` uses cached models only.

### Make it clear and engaging

- **Show the mechanism.** Prefer a concrete example that visibly changes. A
  sequence of labels or cards rarely explains how something works.
- **Choose the visual language.** Use geometry, plots, simulations, code, diagrams,
  or illustrations to fit the subject. Kit helpers are optional building blocks.
- **Preserve continuity.** Transform existing objects as their meaning changes.
  Use `Transform`, `ReplacementTransform`, or `TransformMatchingTex`. A new
  statement does not require a fresh screen.
- **Give motion a purpose.** Show cause and effect, movement, comparison, or a
  change in attention. Alternate construction, transformation, and short holds.
  Avoid repetitive entrances and motion added only to satisfy a check.
- **Cue the narrated idea.** Use `t.wait_until("word")` for a reveal, highlight,
  or transition. `self.focus(m)` can dim unrelated objects; undo with `unfocus()`.
- **Use the camera for a reason.** Pan or zoom to reveal a detail, then restore
  context. For example, `self.camera.frame.animate.scale(0.5).move_to(m)`.
  Objects added while zoomed in need the corresponding scale adjustment.
- **Fill the frame.** The frame is approximately 14.2 by 8 units. Make the main
  diagram 60 to 80 percent of the width. Use font size 24 or more for labels.
- **Keep attention clear.** Limit the scene to one active idea. Remove obsolete
  objects while keeping references needed to understand the change.
- **Use one colour per concept.** Keep the script's palette throughout the video.
- **Show actual values.** Display figures directly. Animate from one real value
  to another when the value changes; do not count an isolated statistic from zero.
- **Split equations into parts** (`MathTex("a^2", "+", "b^2")`) for meaningful transforms.
- **Lay out with `arrange` and `next_to`.** Custom coordinates suit geometry and
  motion paths; check their placement and collisions in the preview.

`ExplainerScene` is a Manim `MovingCameraScene`, so `self.camera.frame` can pan and
zoom. For a scene with 3D, use `class X(NarrationMixin, ThreeDScene)`. The layout
check does not examine 3D scenes.

## 2. Preview

```bash
explainer render video.py
```

This command renders scenes at 480p, joins them into `video.mp4`, and prints the
layout check. Default Qwen runs render scenes serially to limit GPU memory use.
Kokoro runs can render scenes in parallel. If a scene fails, the output shows the line in
`video.py` and the exception. Output from `print()` in `video.py` goes to
`media/logs/<Scene>.log`. All failures show in one run, so fix all of them
before the next run.

Fix each layout warning. If a warning is a false alarm, set `m.lint_ok = True` on that
mobject, and give the reason in your report.

## 3. Review the video and audio

```bash
explainer frames video.mp4
```

This command makes contact sheets in `media/frames/`. Each tile shows the picture at
the end of one narration passage. Read each sheet for layout problems:

- A small diagram in a large empty frame.
- More than one idea on screen.
- A picture that does not match its line.
- A colour that is not in the palette.

To examine one moment at full size, run
`ffmpeg -ss <seconds> -i video.mp4 -frames:v 1 still.png`, and then read the still.

To render again after you fix a problem, name only the scenes that you changed:
`explainer render video.py SceneA SceneB`. The command joins the full video again.
Then run `explainer frames video.mp4 SceneA SceneB` to see only their tiles.

Still frames cannot reveal rushed transitions, awkward holds, voice artifacts, or
speech that does not match the motion. Play the preview and listen. On macOS, use
`open video.mp4`; use `afplay audition.wav` for a voice sample. To isolate a motion
sequence, extract a short clip:

```bash
ffmpeg -ss 10 -i video.mp4 -t 6 -c:v libx264 -c:a aac review.mp4
```

Check these conditions before the final render:

- Labels remain readable through movement and camera changes.
- Important changes happen on their spoken cues, without narration overlap.
- Objects retain a clear identity through transitions.
- Names, acronyms, numbers, and equations sound correct.
- Delivery has natural phrasing and appropriate pauses, without clipped words.
- Layout warnings are fixed or documented as justified false positives.

Fix demonstrated problems and review affected sections again. Stop when these
conditions pass, or report a concrete unresolved limitation. Do not claim a
listening or motion review if the available tools only inspected still frames.

## 4. Final render

```bash
explainer render video.py -q h
```

This command renders all scenes at 1080p60. The video has chapter markers. If the
request asks for captions, add `--captions`: the video then has a caption track, and
the captions are also in `video.srt`.

Report the video path, duration, narrator, and each unresolved quality problem.
Include any limitation on playback, listening, or offline verification.

## Common mistakes

| Mistake | Fix |
| --- | --- |
| Long animations with a fixed `run_time`, so speech and picture drift apart | Use `t.remaining()` and `t.wait_until()` |
| A late word cue or animations that finish after speech | Shorten the preceding animation, or give the spoken passage a natural pause. Recheck the timing warnings |
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
