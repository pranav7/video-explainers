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
| `explainer doctor` | Installs the macOS toolchain and checks local speech and LaTeX |
| `explainer models` | Downloads pinned Qwen speech and word-aligner weights |
| `explainer guide` | Prints the build steps and the API reference |
| `explainer render video.py [SCENE...] [-q l\|h] [--captions]` | Renders scenes, joins them into `video.mp4` with chapter markers, and prints the layout check. `--captions` adds a caption track and `video.srt` |
| `explainer frames video.mp4 [SCENE...]` | Makes contact sheets, one tile for each narration passage |
| `explainer say TEXT OUT.wav [--engine qwen\|kokoro] [--voice NAME] [--spoken TEXT]` | Synthesizes a passage, with an optional spoken spelling, into a stereo WAV file |
| `explainer voices [DIR] [--engine qwen\|kokoro] [--text TEXT]` | Writes a sample for each narrator using the supplied text |
| `explainer test` | Runs the tests |
| `explainer python ...` | Runs Python inside the environment |

## How it works

1. `explainer render` imports `video.py` to find the scenes, in the order of the file.
2. Each scene renders in its own `manim` process. The default Qwen run renders
   scenes serially to limit resident GPU models. Kokoro runs can render in parallel.
3. A scene synthesizes connected narration passages. Qwen supplies speech, and a
   local forced aligner supplies word timestamps. Kokoro supplies its own timing.
   Cached audio and timing are reused when text and speech settings match.
4. After each animation, the scene checks layout. At the end, it writes warnings
   and passage timing.
5. ffmpeg joins scenes with chapter markers and optional captions.

## Speech configuration

Qwen narration requires Apple Silicon. The Qwen3-TTS Base model clones the default
voice, `Ellis`, from a reference clip in `src/explainer/voices`. The clip sets the
timbre, pace, and intonation. Set `EXPLAINER_ENGINE` and `EXPLAINER_VOICE` for a run,
or the scene attributes `engine`, `voice`, and `speed`. For example:

```bash
EXPLAINER_ENGINE=kokoro EXPLAINER_VOICE=bf_emma explainer render video.py
```

Use `pronunciations.json` for recurring spoken spellings, or select another file
with `EXPLAINER_PRONUNCIATIONS`. Inline `[SQL](sequel)` aliases preserve readable
captions. `self.narrate(text, spoken=...)` can override the speech for one passage.
Use word cues within a passage rather than splitting every sentence into separate
synthesis calls. See `explainer guide` for examples and quality checks.

Run `explainer models` once to prefetch pinned Qwen and aligner weights. Set
`EXPLAINER_OFFLINE=1` afterward for cached-model inference. An uncached model fails
instead of using a hosted speech service. The macOS setup command downloads other
dependencies, fonts, and icons separately.

## Develop

| File | Contents |
| --- | --- |
| `bin/explainer` | The command. It sets up the environment, then runs the package |
| `src/explainer/theme.py` | Colours, fonts and sizes |
| `src/explainer/kit/` | The component kit: `text`, `shapes`, `diagrams`, `data`, `motion` and `icons` |
| `src/explainer/narration.py` | `ExplainerScene`: `say`, `narrate`, `fade_all`, `focus` |
| `src/explainer/lint.py` | The layout check |
| `src/explainer/tts.py` | Local Qwen/Kokoro speech, pronunciation text, alignment, and cache |
| `src/explainer/render.py` | Render scheduling, join, chapters, captions, contact sheets |
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
- Run `explainer test` before committing. Validate speech and a complete render
  after changes to models, word timing, or Manim dependencies.

## Licenses of the dependencies

This project uses the MIT license. It uses these projects, which have their own licenses:

| Project | License | How it is used |
| --- | --- | --- |
| [Manim Community](https://github.com/ManimCommunity/manim) | MIT | Python dependency |
| [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS) | Apache-2.0 | Local narration weights, downloaded by `explainer models` |
| [Qwen3-ForcedAligner](https://github.com/QwenLM/Qwen3-ASR) | Apache-2.0 | Local word-alignment weights, downloaded by `explainer models` |
| [MLX-Audio](https://github.com/Neywa-Labs/mlx-audio) and [MLX](https://github.com/ml-explore/mlx) | MIT | Apple Silicon inference dependencies |
| [Kokoro](https://github.com/hexgrad/kokoro) and Kokoro-82M | Apache-2.0 | Alternative local narration, downloaded on first use |
| [Lucide](https://lucide.dev) | ISC | Icons downloaded by `explainer doctor` |
| [Inter](https://rsms.me/inter/), [JetBrains Mono](https://www.jetbrains.com/lp/mono/) | SIL Open Font License | Fonts installed by `explainer doctor` |
| [espeak-ng](https://github.com/espeak-ng/espeak-ng) | GPL-3.0 | Installed from Homebrew. Not included in this repository |
