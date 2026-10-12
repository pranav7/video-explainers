# Contributing

This file is for people who change the toolkit. To use it, see the [README](README.md).

## Write a video by hand

Write `video.py`:

```python
from explainer.kit import *


class Lookup(ExplainerScene):
    title = "Asking for an address"

    def construct(self):
        laptop = box("Your laptop", SKY, icon_name="laptop")
        resolver = box("Resolver", VIOLET, icon_name="server")
        VGroup(laptop, resolver).arrange(RIGHT, buff=4)
        ask = connect(laptop, resolver, SKY)
        self.say("Your laptop asks a resolver for the address of a name.",
                 appear(laptop, resolver), GrowArrow(ask), at="resolver")
        self.say("The question travels as one small packet.", travel(ask, SKY, "example.com"))
        self.fade_all()
```

Then render it:

```bash
explainer render video.py          # 480p preview, with the layout check
explainer frames video.mp4         # contact sheets in media/frames/
explainer render video.py -q h     # 1080p60
```

## Commands

| Command | Effect |
| --- | --- |
| `explainer doctor` | Installs and tests every dependency |
| `explainer guide` | Prints the build steps and the API reference |
| `explainer render video.py [SCENE...] [-q l\|h] [--captions]` | Renders the scenes in parallel, joins them into `video.mp4` with chapter markers, and prints the layout check. `--captions` adds a caption track and `video.srt` |
| `explainer frames video.mp4 [SCENE...]` | Makes contact sheets, one tile for each line of narration |
| `explainer say TEXT OUT.wav`, `explainer voices` | Synthesizes speech, and samples of each voice |
| `explainer test` | Runs the tests |
| `explainer python ...` | Runs Python inside the environment |

## How it works

1. `explainer render` imports `video.py` to find the scenes, in the order of the file.
2. Each scene renders in its own `manim` process. A scene speaks each line with
   Kokoro. The audio and the word timestamps are cached, so a second render does not
   synthesize the line again.
3. After each animation, the scene runs the layout check. When the scene ends, it
   writes its warnings and the timing of each line.
4. ffmpeg joins the scenes into one video, with a chapter marker for each scene.

## Develop

| File | Contents |
| --- | --- |
| `bin/explainer` | The command. It sets up the environment, then runs the package |
| `src/explainer/theme.py` | Colours, fonts and sizes |
| `src/explainer/kit/` | The component kit: `text`, `shapes`, `diagrams`, `data`, `motion` and `icons` |
| `src/explainer/narration.py` | `ExplainerScene`: `say`, `narrate`, `fade_all`, `focus` |
| `src/explainer/lint.py` | The layout check |
| `src/explainer/tts.py` | Kokoro synthesis, with a cache |
| `src/explainer/render.py` | Parallel render, join, chapters, captions, contact sheets |
| `src/explainer/cli.py` | The command-line interface |
| `src/explainer/guide.md` | The build steps that `explainer guide` prints |
| `skills/explain-video/SKILL.md` | The skill for agents |

- To add a kit helper, write a function with a docstring in a module of `kit/`. The
  function shows in `explainer guide` automatically.
- For an animation of an on-screen group, return one animation of the whole group, not
  an `AnimationGroup` of its parts. Manim draws the animated parts again on top of
  the rest of the group.
- To add a layout check, add it to `Lint` in `lint.py`, with a test in
  `tests/test_lint.py` that shows the problem and a clean case.
- Run `explainer test` before you commit. The tests take approximately 20 seconds.

## Licenses of the dependencies

This project uses the MIT license. It uses these projects, which have their own licenses:

| Project | License | How it is used |
| --- | --- | --- |
| [Manim Community](https://github.com/ManimCommunity/manim) | MIT | Python dependency |
| [Kokoro](https://github.com/hexgrad/kokoro) and Kokoro-82M | Apache-2.0 | Python dependency, and a model downloaded on first use |
| [Lucide](https://lucide.dev) | ISC | Icons downloaded by `explainer doctor` |
| [Inter](https://rsms.me/inter/), [JetBrains Mono](https://www.jetbrains.com/lp/mono/) | SIL Open Font License | Fonts installed by `explainer doctor` |
| [espeak-ng](https://github.com/espeak-ng/espeak-ng) | GPL-3.0 | Installed from Homebrew. Not included in this repository |
