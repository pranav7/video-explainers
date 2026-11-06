# Video Explainers as Skill for AI Coding Agents

Ask your coding agent for a narrated explainer video. Manim draws the visuals;
Qwen3-TTS through MLX clones a bundled narrator voice with natural intonation.
Kokoro is also available. Speech synthesis, word alignment, and rendering run locally,
without a hosted speech API.

## Example

https://github.com/user-attachments/assets/b8f9ecf4-8385-432d-8297-880810db78fd

The agent wrote the [script](examples/binary-search/script.md) and
[scenes](examples/binary-search/video.py). The
[voice and motion example](examples/voice-and-motion/script.md) shows connected
narration, word-triggered motion, and a pronunciation dictionary.

## Install

The setup command supports macOS with [Homebrew](https://brew.sh) and
[uv](https://docs.astral.sh/uv/). Qwen narration requires Apple Silicon.

```bash
git clone https://github.com/pranav7/video-explainers.git ~/video-explainers
ln -s ~/video-explainers/bin/explainer ~/.local/bin/explainer
explainer doctor
```

`doctor` installs dependencies, downloads pinned Qwen speech and word-aligner
weights, and checks speech and LaTeX. Use `explainer models` to download weights
separately. Setup requires network access; after
setup, use cached models with `EXPLAINER_OFFLINE=1`.

For a Kokoro setup, select it explicitly with `EXPLAINER_ENGINE=kokoro`.
Kokoro also supports non-Apple-Silicon environments, with their native dependencies
installed separately from the macOS setup command.

## Use

For Claude Code, link the skill:

```bash
ln -s ~/video-explainers/skills/explain-video ~/.claude/skills/explain-video
```

Then ask: "Make an explainer video about how DNS works."

For Codex or another agent, supply `skills/explain-video/SKILL.md`, or ask it to run
`explainer guide`. The guide covers scripts, storyboards, previews, and quality checks.

Default voice: `Ellis`. Listen to a passage from your own script before a full render:

```bash
explainer say "One request, fifty orders." sample.wav
afplay sample.wav
```

`--speed` changes the tempo. To add a voice, see
[the voice folder](src/explainer/voices/README.md).

Use a `pronunciations.json` file in the video directory for recurring terms:

```json
{"SQL": "sequel", "API": "A P I"}
```

Inline aliases such as `[SQL](sequel)` change speech while captions retain `SQL`.
`--spoken` supplies a separate spoken version for a complete passage. Kokoro is
explicit: `explainer say "Hello." sample.wav --engine kokoro --voice af_heart`.

After setup, render offline from a video directory:

```bash
EXPLAINER_OFFLINE=1 explainer render video.py --captions
explainer frames video.mp4
EXPLAINER_OFFLINE=1 explainer render video.py -q h --captions
```

The final render is 1080p60, with chapter markers. `--captions` adds a subtitle track
and `video.srt`. Inspect motion and listen to narration as well as checking still frames.

## License

MIT. Dependencies and model weights have their own licenses. See
[CONTRIBUTING.md](CONTRIBUTING.md) for the list and development details.
