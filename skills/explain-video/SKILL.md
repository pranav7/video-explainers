---
name: explain-video
description: Use when the user asks for an explainer video, an animated explanation, a narrated video, a "3blue1brown style" or "3b1b style" video, or a Manim animation on any topic.
---

# Video explainer

Make a narrated, 3Blue1Brown-style explainer video on any topic. Visuals are Manim
(Community Edition). Narration is Kokoro-82M, a local text-to-speech model. It runs
on the machine with no API key. Each line of narration sets the timing of the
animation that goes with it.

The work has two parts:

1. You write `script.md`: each line of narration and what is on screen while it plays.
   You have the context, so you write the script.
2. A subagent builds the video from `script.md`. It writes the scenes, renders them,
   checks the layout, and makes the final render.

The build makes approximately 20 tool calls, and each call sends the full context
again. A new subagent has a small context, so the build is cheaper and faster there.
The subagent also runs in the background, so the user can continue to work with you.

The `explainer` command does the rest of the work. It must be on `PATH`. For setup,
see https://github.com/pranav7/explainer. Run `explainer -h` for the commands.

## 0. Setup (once per machine)

Run `explainer doctor`. It installs Homebrew packages, fonts, TinyTeX, a Python env and
the icons, then tests Kokoro and LaTeX. It is safe to run again. Run it if a command
fails on a missing dependency.

## 1. Plan

- **Where.** If the conversation is about a project that has its own folder for
  documents, put the video in a `videos/<slug>/` folder there. Otherwise use
  `~/Movies/explainers/<slug>/`.
- **Audience and length.** Ask only if the request does not make them clear. Default:
  a curious adult with no background in the topic, 2 to 4 minutes.
- **Length of the script.** Kokoro speaks approximately 170 words a minute, so a
  3-minute video has approximately 500 words of narration. Write one chapter for each
  30 to 45 seconds.

Pick the shape that fits the topic.

For a concept (an algorithm, an idea in maths or science):

1. Open on a concrete question or puzzle, not a definition.
2. Build intuition with one specific example that the viewer can see.
3. Generalize, and only then show the formula. The formula names what they already saw.
4. End on the key idea in one picture.

For a situation (a run that failed, an incident, a design, a catch-up on work):

1. Open on what happened, with the real numbers.
2. Show the mechanism that caused it, one step at a time.
3. Show what changes: the fix, the decision, or the next step.
4. End on one picture of the whole system with the change in place.

## 2. Write script.md

Write `script.md` in the video directory, in this format:

```markdown
# Why the orders page is slow

For engineers on the team. About 3 minutes.

## Palette

| Concept | Colour |
| --- | --- |
| The API server | SKY |
| The database | VIOLET |
| Slow, wasted work | CORAL |
| The fix | MINT |

## 1. Hook: Fifty orders, fifty queries

- "The orders page takes four seconds to load fifty orders."
  - A browser card with "4.1 s" in coral, and a list of 50 order tags.
- "The server asks the database once for each order."
  - An API server card and a database card. Packets travel between them, one per order.
```

Each chapter heading is `## <number>. <SceneName>: <chapter title>`. The builder makes
one scene class for each chapter. The chapter titles become chapter markers in the video.

The builder cannot see this conversation. Put every name, number, label, and value
that goes on screen into the script.

Narration is read aloud exactly as written:

- Write the spoken form: "x squared", "two pi r", "P O number", "v two".
  Do not put LaTeX, symbols, or code in narration.
- Write one sentence for each line, two at most. Each line is one visual change.
- If Kokoro mispronounces a word, give its phonemes inline: `[Kokoro](/kˈOkəɹO/)`.
- The default voice is `af_heart`. If the user cares about the voice, run
  `explainer voices` and let them listen (`afplay voice-samples/<name>.wav`).

Under each line, describe the picture, not a slide. Name the objects, what they show,
and what moves. Give each concept one colour from the palette.

Take palette colours from the kit's accents: SKY, MINT, AMBER, CORAL, VIOLET, AQUA, ROSE,
PEACH, LIME. The kit also has neutrals for things that are not a concept: SUBTLE,
FAINT, INK. The kit has cards, tags, tables, code windows, pipelines, sequence
diagrams, timelines, trees, callouts, charts, big numbers and Lucide icons. Describe
pictures that use them.

Show each number as it is. Do not ask for a number that counts up from zero.

## 3. Hand off the build

Start the builder as a subagent. If your instructions name an agent type or a model
for building work, use them. Give it this prompt:

```text
Build the explainer video for <directory>/script.md. Run `explainer guide` and
follow it. Report the video path, its duration, and each layout warning that you
left in place, with the reason.
```

If the user asked for captions, add "Render with --captions." to the prompt.

Tell the user that the video is in progress, then continue with other work. If you
cannot start a subagent, run `explainer guide` and do its steps yourself.

## 4. Deliver

When the builder reports, open `<directory>/video.mp4` (on macOS, `open`). Tell the
user:

- The file path and the duration.
- The video has chapter markers.
- Any problem that the builder left open.

Ask what to change. To make a change, send it to the same builder if your tools can
message it, because the builder keeps its context. Otherwise start a new builder
with the change. If the change affects the narration, edit `script.md` first.
