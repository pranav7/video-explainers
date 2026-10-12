# Video Explainers as Skill for AI Coding Agents

Super fast video explainers for AI agents, made locally on your machine. Ask your coding
agent to explain anything as a short, narrated video.

> The output format I am most bullish on is fully custom / bespoke explainer videos
> generated on any arbitrary topic.
>
> — Andrej Karpathy

As agents do more of the work, more of your work is to understand what they did. A
short video is often the fastest way to understand an idea, a system, or what went
wrong in a run. With this toolkit, your agent makes that video on your own computer.
It is free, and it needs no API keys.

## Example

https://github.com/user-attachments/assets/b8f9ecf4-8385-432d-8297-880810db78fd

The request was a short video that explains a simple, interesting concept. The agent
wrote the [script](examples/binary-search/script.md) and the
[scenes](examples/binary-search/video.py).

## Install

You need a Mac with [Homebrew](https://brew.sh) and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/pranav7/video-explainers.git ~/video-explainers
ln -s ~/video-explainers/bin/explainer ~/.local/bin/explainer   # or any directory on PATH
explainer doctor
```

`explainer doctor` installs everything that the videos need. It is safe to run again.

## Use

For Claude Code, link the skill:

```bash
ln -s ~/video-explainers/skills/explain-video ~/.claude/skills/explain-video
```

Then ask: "Make an explainer video about how DNS works."

For another agent, such as Codex, give it `skills/explain-video/SKILL.md`, or tell it to
run `explainer guide` and follow it.

## License

MIT. The toolkit installs other open-source projects, which have their own licenses.
For the list, and for how to change the toolkit, see [CONTRIBUTING.md](CONTRIBUTING.md).
