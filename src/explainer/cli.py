"""The `explainer` command. Run `explainer -h`."""

from __future__ import annotations

import argparse
import ast
import inspect
import os
import tempfile
import textwrap
from importlib.resources import files
from pathlib import Path

from explainer.render import RES


def _signature(f, method: bool = False) -> str:
    """The parameter list as written in the source, so defaults show as names (color=MUTED)."""
    node = ast.parse(textwrap.dedent(inspect.getsource(inspect.unwrap(f)))).body[0]
    a = node.args
    params = a.posonlyargs + a.args
    defaults = [None] * (len(params) - len(a.defaults)) + a.defaults
    parts = [p.arg + (f"={ast.unparse(d)}" if d else "") for p, d in zip(params, defaults)]
    if a.vararg:
        parts.append(f"*{a.vararg.arg}")
    elif a.kwonlyargs:
        parts.append("*")
    parts += [k.arg + (f"={ast.unparse(d)}" if d else "") for k, d in zip(a.kwonlyargs, a.kw_defaults)]
    return f"({', '.join(parts[1:] if method else parts)})"


def _summary(f) -> str:
    return " ".join((inspect.getdoc(f) or "").split())


def api() -> str:
    """Reference for the theme, the kit and the scene API, built from the code."""
    import importlib

    from explainer import kit
    from explainer import theme
    from explainer.narration import Narration, NarrationMixin

    accents = ", ".join(f"`{n}`" for n in ("SKY", "MINT", "AMBER", "CORAL", "VIOLET", "AQUA", "ROSE", "PEACH", "LIME"))
    out = ["## API", "", "### Theme", "",
           f"- Accent colours, for palettes: {accents}.",
           "- Neutrals: `BG` (background), `SURFACE`, `RAISED`, `LINE`, `FAINT`, `SUBTLE` (secondary text), `INK` (text).",
           f"- Fonts: `SANS` ({theme.SANS}), `MONO` ({theme.MONO}). `tint(colour, amount)` mixes a colour into the background."]
    for name in kit.MODULES:
        module = importlib.import_module(f"explainer.kit.{name}")
        out += ["", f"### {name.capitalize()}", ""]
        for fname, f in vars(module).items():
            if inspect.isfunction(f) and f.__module__ == module.__name__ and not fname.startswith("_"):
                out.append(f"- `{fname}{_signature(f)}`: {_summary(f)}")
    out.append(f"- `fit{_signature(kit.fit)}`: {_summary(kit.fit)}")
    out += ["", "### Scene methods (class X(ExplainerScene))", ""]
    for name in ("say", "narrate", "fade_all", "focus", "unfocus"):
        out.append(f"- `self.{name}{_signature(getattr(NarrationMixin, name), method=True)}`: {_summary(getattr(NarrationMixin, name))}")
    out += ["- class attributes `title`, `voice`, `speed`: chapter title, Kokoro voice, speech speed.",
            "", "### The spoken line (with self.narrate(text) as t)", ""]
    for name in ("wait_until", "remaining", "time_of"):
        out.append(f"- `t.{name}{_signature(getattr(Narration, name), method=True)}`: {_summary(getattr(Narration, name))}")
    return "\n".join(out)


def smoke() -> None:
    """Download the icons, synthesize one word and compile one formula."""
    from manim import MathTex

    from explainer.kit.icons import fetch_icons
    from explainer.tts import synthesize

    print(f"Lucide icons in {fetch_icons()}")
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        synthesize("Ready.")
        MathTex(r"e^{i\pi}+1=0")
    print("Kokoro and LaTeX work")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="explainer", description="Narrated, 3Blue1Brown-style explainer videos.",
        epilog="The wrapper script also runs: explainer doctor (install and check every dependency), "
               "explainer test (run the tests), explainer python ARGS (python inside the env).")
    sub = parser.add_subparsers(dest="cmd", required=True, metavar="COMMAND")

    sub.add_parser("guide", help="print the build steps and the API reference")

    r = sub.add_parser("render", help="render scenes in parallel, join them into FILE.mp4 with chapters, run the layout check")
    r.add_argument("file", type=Path, metavar="FILE.py")
    r.add_argument("scenes", nargs="*", metavar="SCENE",
                   help="scenes to render (default: all). The others reuse their last render at this "
                        "quality; a scene with no render at this quality renders too.")
    r.add_argument("-q", dest="quality", default="l", choices=RES,
                   help="l = 480p15 preview (default), m = 720p30, h = 1080p60 final, p = 1440p60, k = 2160p60")
    r.add_argument("--captions", action="store_true", help="add a caption track and FILE.srt (default: off)")
    r.add_argument("-j", dest="jobs", type=int, default=max(2, (os.cpu_count() or 4) - 2), help="scenes rendered at once")

    f = sub.add_parser("frames", help="contact sheets, one tile per narration line, in media/frames/")
    f.add_argument("video", type=Path, metavar="VIDEO.mp4")
    f.add_argument("scenes", nargs="*", metavar="SCENE", help="only these scenes")

    s = sub.add_parser("say", help="synthesize TEXT into OUT.wav")
    s.add_argument("text")
    s.add_argument("out", type=Path)
    s.add_argument("--voice")
    s.add_argument("--speed", type=float)

    v = sub.add_parser("voices", help="write one sample per voice to DIR (default ./voice-samples)")
    v.add_argument("dir", type=Path, nargs="?", default=Path("voice-samples"))

    sub.add_parser("smoke", help="download the icons, check that Kokoro and LaTeX work")

    args = parser.parse_args()
    if args.cmd == "guide":
        print(files("explainer").joinpath("guide.md").read_text().rstrip() + "\n\n" + api())
    elif args.cmd == "render":
        from explainer.render import render

        render(args.file.resolve(), args.scenes, args.quality, args.jobs, args.captions)
    elif args.cmd == "frames":
        from explainer.render import frames

        frames(args.video.resolve(), args.scenes)
    elif args.cmd == "say":
        from explainer.tts import DEFAULT_SPEED, DEFAULT_VOICE, synthesize

        wav, meta = synthesize(args.text, args.voice or DEFAULT_VOICE, args.speed or DEFAULT_SPEED)
        args.out.write_bytes(wav.read_bytes())
        print(f"{args.out}  {meta['duration']:.1f}s")
    elif args.cmd == "voices":
        from explainer.tts import VOICES, synthesize

        args.dir.mkdir(parents=True, exist_ok=True)
        text = "A matrix is a way to move every point in the plane at once. Watch where these two arrows land."
        for voice in VOICES:
            wav, _ = synthesize(text, voice)
            (args.dir / f"{voice}.wav").write_bytes(wav.read_bytes())
        print(f"Listen with: afplay {args.dir}/<voice>.wav")
    elif args.cmd == "smoke":
        smoke()


if __name__ == "__main__":
    main()
