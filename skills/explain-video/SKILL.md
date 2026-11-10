---
name: explain-video
description: Use when the user asks for an explainer video, an animated explanation, a narrated video, a "3blue1brown style" or "3b1b style" video, or a Manim animation on any topic.
---

# Video explainer

Make a narrated explainer with Manim Community and local speech synthesis. The
preferred narrator is Qwen3-TTS through MLX on Apple Silicon. Kokoro remains
available. Speech synthesis, word alignment, and rendering run on the machine.
Setup downloads packages, models, fonts, and icons. No hosted speech API is needed.

Write `script.md`, then delegate the build to a builder with that file and
`explainer guide`. Include the context the builder needs; it cannot see this
conversation. If delegation is unavailable, follow the guide yourself.

The `explainer` command must be on `PATH`. For installation, see
https://github.com/pranav7/video-explainers. Run `explainer -h` for commands.

## Setup

Run `explainer doctor` for a missing dependency. It installs and checks the macOS
toolchain. Run `explainer models` to prefetch pinned Qwen and aligner weights.
Qwen requires Apple Silicon; select Kokoro explicitly for other environments.
After the models are downloaded, use `EXPLAINER_OFFLINE=1` to prevent model
downloads during synthesis and rendering. An uncached model must fail with
an actionable error rather than use a hosted service.

## Plan

- Put project videos in its documents folder under `videos/<slug>/`. Otherwise use
  `~/Movies/explainers/<slug>/`.
- Infer audience and length from the request. Default: a curious adult, 2 to 4 minutes.
- Start with a concrete question, puzzle, or incident. Show one example, reveal
  the mechanism, then generalize. End with one picture of the key idea or change.
- Storyboard before coding. For each passage, specify the objects, their state,
  what changes, and the word that cues the change. Use actual names and numbers.
- Choose visual treatment for the subject: geometry, a simulation, a diagram,
  a chart, code, or an illustration. The kit supplies useful parts, not a required
  card layout. Preserve objects as the explanation develops.

## Write script.md

Use chapters named `## <number>. <SceneName>: <chapter title>`. Each becomes a scene
and a chapter marker. Include the audience, length, concept palette, and voice
before the chapters.

```markdown
# Why the orders page is slow

For engineers. About 3 minutes.
Voice: Ellis. Default speed.

## Palette

| Concept | Colour |
| --- | --- |
| Requests | SKY |
| Database | VIOLET |
| Wasted work | CORAL |
| Fix | MINT |

## 1. Hook: Fifty trips for one page

- "Fifty orders, fifty database trips. Watch the requests queue up while the page waits."
  - A stream of fifty order dots moves toward the database, one at a time.
  - On "queue", the waiting dots accumulate. A coral label reads "50 trips".
- "Now send one request for the whole set. The same orders arrive together."
  - Keep the orders and database in place. Collapse the requests into one bundle.
  - On "together", the bundle opens into the same fifty orders. Label: "1 trip".
```

Write connected passages of two or three sentences when they share one thought.
A passage can have several visual cues. Do not force a new synthesis call for each
sentence. Estimate length from the first audio sample, because the voice sets the pace.

Keep spoken text conversational. Spell out equations and code for speech. Use a
local `pronunciations.json` object for recurring terms, for example
`{"SQL": "sequel", "API": "A P I"}`. This changes speech without changing readable
captions. Inline aliases such as `[SQL](sequel)` also preserve readable captions.
For a single passage, the builder can pass `spoken=` separately from its display
text. Kokoro phoneme markup is specific to Kokoro; do not send it to Qwen.

Default voice: `Ellis`. Audition a representative passage before the full render,
including names, numbers, and technical terms:

```bash
explainer say "The API sends one SQL query." audition.wav
```

Use `explainer voices voice-samples --engine qwen --text "<representative passage>"`
for a comparison. On macOS, listen with `afplay`. Respect an established voice
preference. If none exists, use the default and report it without blocking the build.
Kokoro is explicit: `--engine kokoro --voice af_heart`.

Use the same voice and speed for the audition and the finished video.
The voice clones a reference clip, so the clip sets its intonation and pace.
Check a full representative passage. Word alignment estimates timing; it does not
verify spoken content or natural delivery. Check the rendered audio separately
against the script. Local transcription can flag omissions, repetitions, and wrong
words, but listening is needed to judge delivery. State any unavailable review.

Use one colour per concept. Kit accents: SKY, MINT, AMBER, CORAL, VIOLET, AQUA, ROSE,
PEACH, LIME. Neutrals: SUBTLE, FAINT, INK. Draw the mechanism rather than bullet lists.
Show actual numbers directly. Animate changes between real states.

## Build

Give the builder this prompt:

```text
Build <directory>/script.md into video.mp4. Run `explainer guide` and follow it.
Check a speech sample, then preview and review motion, audio, and layout. Keep
speech synthesis and rendering local. Report the path, duration, voice, and any
remaining pronunciation, synchronization, or layout problems with their reasons.
```

If requested, add "Render with --captions." Tell the user that the build is in
progress. Keep the same builder for revisions when available.

## Deliver

Open `<directory>/video.mp4` on macOS with `open`. Report its path, duration,
chapter markers, voice, and remaining problems. If narration changes, update
`script.md` before rebuilding. Never label a still-frame check as a motion or
listening review. If playback or listening is unavailable, state that limitation.
