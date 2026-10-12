# video-explainers

Narrated, 3Blue1Brown-style explainer videos that AI coding agents can make.

Ask your agent for a video that explains something: an algorithm, an incident, a
design, a pull request. The agent writes a script. The `explainer` toolkit turns the
script into a narrated MP4:

- [Manim](https://www.manim.community/) draws the animation.
- [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) speaks the narration, on your
  machine, with no API key.
- Each line of speech sets the timing of its animation, to the word.

## What it gives an agent

- **Instructions that match the code.** `explainer guide` prints the build steps and an
  API reference that is generated from the code. Any agent that can run a command can
  follow it.
- **A component kit with one look.** Approximately 50 helpers: cards with icons, tags,
  tables, code windows with syntax colours and animated diffs, pipelines, sequence
  diagrams, timelines, trees, callouts, charts, big numbers, and the
  [Lucide](https://lucide.dev/icons) icon set. All of them use one dark theme with
  Inter and JetBrains Mono.
- **A layout check.** After each animation, the scene reports problems as text: objects
  past the frame edge, text on text, text half under a box, arrows through text, text
  too small to read, content too small for the frame, and pictures that stay still
  too long. An agent fixes its layout from these warnings without looking at every
  frame.
- **Fast renders.** Each scene renders in its own process. On a 12-core Apple Silicon
  Mac, a 3.5-minute video renders at 1080p60 in approximately 30 seconds.
- **Contact sheets.** `explainer frames` makes one tile for each line of narration, so
  an agent can review the whole video in a few images.

## Requirements

- macOS with [Homebrew](https://brew.sh). The toolkit is tested on Apple Silicon.
- [uv](https://docs.astral.sh/uv/).

## Install

```bash
git clone https://github.com/pranav7/video-explainers.git ~/video-explainers
ln -s ~/video-explainers/bin/explainer ~/.local/bin/explainer   # or any directory on PATH
explainer doctor
```

`explainer doctor` installs and tests everything that the toolkit needs. It is safe to
run again. It installs:

- Homebrew packages: pkgconf, cairo, pango, ffmpeg and espeak-ng.
- The fonts Inter and JetBrains Mono, from Homebrew.
- TinyTeX, into `~/Library/TinyTeX`, with no `sudo`.
- A Python 3.12 environment in `~/.cache/video-explainer/venv`, with the versions in
  `uv.lock`.
- The Lucide icons, into `~/.cache/explainer/`.

The first narration downloads the Kokoro model from Hugging Face.

## Use it with an agent

The skill in `skills/explain-video/SKILL.md` tells an agent how to plan a video, write
the script, and hand the build to a subagent.

For Claude Code, link the skill into your skills directory:

```bash
ln -s ~/video-explainers/skills/explain-video ~/.claude/skills/explain-video
```

Then ask for a video, for example: "Make an explainer video about how DNS resolution
works."

For another agent, give it the skill file, or tell it to run `explainer guide` and
follow it.

## Use it yourself

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

## Licenses

This project uses the MIT license. It uses these projects, which have their own licenses:

| Project | License | How it is used |
| --- | --- | --- |
| [Manim Community](https://github.com/ManimCommunity/manim) | MIT | Python dependency |
| [Kokoro](https://github.com/hexgrad/kokoro) and Kokoro-82M | Apache-2.0 | Python dependency, and a model downloaded on first use |
| [Lucide](https://lucide.dev) | ISC | Icons downloaded by `explainer doctor` |
| [Inter](https://rsms.me/inter/), [JetBrains Mono](https://www.jetbrains.com/lp/mono/) | SIL Open Font License | Fonts installed by `explainer doctor` |
| [espeak-ng](https://github.com/espeak-ng/espeak-ng) | GPL-3.0 | Installed from Homebrew. Not included in this repository |
