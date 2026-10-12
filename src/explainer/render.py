"""Render scenes in parallel, join them with chapters and captions, make contact sheets."""

from __future__ import annotations

import concurrent.futures as cf
import importlib.util
import inspect
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path

RES = {"l": "480p15", "m": "720p30", "h": "1080p60", "p": "1440p60", "k": "2160p60"}


def ffprobe(path: Path, entries: str, stream: str | None = None) -> str:
    cmd = ["ffprobe", "-v", "error", "-show_entries", entries, "-of", "csv=p=0", str(path)]
    if stream:
        cmd[1:1] = ["-select_streams", stream]
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout.strip()


def ffmpeg(*args) -> None:
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *map(str, args)], check=True)


def duration(path: Path) -> float:
    return float(ffprobe(path, "format=duration"))


def scenes_in(file: Path) -> list[str]:
    """The narrated scene classes defined in `file`, in source order."""
    from explainer.narration import NarrationMixin

    sys.path.insert(0, str(file.parent))
    spec = importlib.util.spec_from_file_location(file.stem, file)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        frames = [f"{file.name}:{f.lineno}: {f.line}" for f in traceback.extract_tb(e.__traceback__) if f.filename == str(file)]
        sys.exit("\n".join([f"error: {file.name} does not import", *frames, *traceback.format_exception_only(e)]).rstrip())

    from manim import Scene

    # Module globals keep the order in which the file defines them. A base class with no
    # construct() of its own is a helper, not a scene.
    scenes = [
        name for name, c in vars(module).items()
        if inspect.isclass(c) and issubclass(c, NarrationMixin) and c.__module__ == module.__name__
        and c.construct is not Scene.construct
    ]
    if not scenes:
        sys.exit(f"error: {file.name} defines no narrated scene (a subclass of ExplainerScene with a construct method)")
    return scenes


# ---------------------------------------------------------------- render


def render(file: Path, names: list[str], quality: str, jobs: int, captions: bool = False) -> None:
    if file.stem == "explainer":
        sys.exit(f"error: rename {file.name} (for example to video.py). The name hides the explainer package.")
    order = scenes_in(file)
    unknown = [n for n in names if n not in order]
    if unknown:
        sys.exit(f"error: no scene {', '.join(unknown)} in {file.name}. Scenes: {' '.join(order)}")
    media = file.parent / "media"
    videos = media / "videos" / file.stem / RES[quality]
    todo = list(dict.fromkeys(names or order))
    todo += [s for s in order if s not in todo and not (videos / f"{s}.mp4").exists()]

    logs = media / "logs"
    logs.mkdir(parents=True, exist_ok=True)

    def one(scene: str) -> tuple[str, int]:
        cmd = [sys.executable, "-m", "manim", "render", f"-q{quality}", "--disable_caching",
               "--progress_bar", "none", "-v", "WARNING", file.name, scene]
        # A crashed render can leave empty files in the scene's caches, which break every later render.
        for cache in ("texts", "Tex"):
            for f in (media / cache / scene).glob("*"):
                if f.is_file() and f.stat().st_size == 0:
                    f.unlink()
        # A wide console keeps each traceback frame's path on one line, for failure_summary.
        env = {**os.environ, "COLUMNS": "200", "EXPLAINER_SCENE": scene}
        with open(logs / f"{scene}.log", "w") as log:
            return scene, subprocess.run(cmd, cwd=file.parent, env=env, stdout=log, stderr=subprocess.STDOUT).returncode

    began = time.time()
    with cf.ThreadPoolExecutor(max(1, min(jobs, len(todo)))) as pool:
        results = list(pool.map(one, todo))
    # Parallel scenes can collide on a shared cache file (LaTeX, narration). Retry each failure once, alone.
    failed = [s for s, code in results if code]
    failed = [s for s in failed if one(s)[1]]
    for scene in failed:
        summary = failure_summary((logs / f"{scene}.log").read_text(), file.name)
        print(f"\n--- {scene} failed (full log: media/logs/{scene}.log)\n{summary}", file=sys.stderr)
    if failed:
        sys.exit(f"error: {len(failed)} of {len(todo)} scenes failed: {' '.join(failed)}")
    print(f"Rendered {len(todo)} scenes at {RES[quality]} in {time.time() - began:.0f}s: {' '.join(todo)}")

    out = assemble(file, order, quality, captions)

    lint = media / "lint" / file.stem
    warnings = [line for s in order if (lint / f"{s}.txt").exists() for line in (lint / f"{s}.txt").read_text().splitlines()]
    if warnings:
        print(f"\nLayout check, {len(warnings)} warnings:")
        print("\n".join(f"  {w}" for w in warnings))
    else:
        print("Layout check: no warnings")
    extra = f", captions in {out.with_suffix('.srt').name}" if captions else ""
    print(f"\n{out} ({duration(out):.0f}s, {len(order)} chapters{extra})")


def failure_summary(log: str, scene_file: str) -> str:
    """The frames of Manim's traceback that point into our files, and the exception."""
    lines = log.splitlines()
    ends = [i for i, line in enumerate(lines) if line.startswith("╰")]
    if not ends:
        return "\n".join(lines[-30:])
    ours = (f"{scene_file}:", "explainer/")
    kept = []
    for i, line in enumerate(lines[: ends[-1]]):
        if any(name in line for name in ours):
            kept.append(line.strip("│ "))
            # The highlighted source line follows the frame's path line.
            kept += [m.strip("│ ") for m in lines[i + 1 : i + 12] if "❱" in m][:1]
    return "\n".join(kept + [line for line in lines[ends[-1] + 1 :] if line.strip()])


# ---------------------------------------------------------------- join


def caption_cues(start: float, end: float, words: list[dict], max_chars: int = 42) -> list[tuple[float, float, str]]:
    """Split one narration line into caption cues, timed from Kokoro's word timestamps."""
    chunks, current = [], []
    for w in words:
        # Punctuation always stays with the words before it.
        if current and not _PUNCT.fullmatch(w["word"]) and len(_join(current + [w])) > max_chars:
            chunks.append(current)
            current = []
        current.append(w)
        if re.fullmatch(r"[.?!;:]", w["word"]) and len(_join(current)) > 20:
            chunks.append(current)
            current = []
    if current:
        chunks.append(current)
    cues = []
    for i, chunk in enumerate(chunks):
        a = start if i == 0 else start + chunk[0]["start"]
        b = end if i == len(chunks) - 1 else start + chunks[i + 1][0]["start"]
        cues.append((a, b, _join(chunk)))
    return cues


_PUNCT = re.compile(r"[^\w\s]+")
_OPENERS = {"(", "[", "{", "$", "\u201c", "\u2018"}


def _join(words: list[dict]) -> str:
    """Join Kokoro's tokens into text: no space before closing punctuation or after an opener."""
    text, glue, quote_open = "", True, False
    for w in words:
        token = w["word"]
        if token == '"':
            quote_open = not quote_open
            text += f" {token}" if quote_open and text else token
            glue = quote_open
        elif token in _OPENERS:
            text += f" {token}" if text else token
            glue = True
        elif _PUNCT.fullmatch(token):
            text += token
            glue = False
        else:
            text += token if glue or not text else f" {token}"
            glue = False
    return text


def _srt_time(t: float) -> str:
    ms = round(t * 1000)
    return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"


def assemble(file: Path, order: list[str], quality: str, captions: bool = False) -> Path:
    """Join the scenes into FILE.mp4 with chapters, and with captions (FILE.srt and a caption track)
    when asked. Write media/timeline/FILE.json."""
    media = file.parent / "media"
    res = RES[quality]
    parts = [media / "videos" / file.stem / res / f"{s}.mp4" for s in order]
    missing = [p.stem for p in parts if not p.exists()]
    if missing:
        sys.exit(f"error: no {res} render of {' '.join(missing)}; see media/logs/")

    timeline, chapters, offset = [], [], 0.0
    for scene, part in zip(order, parts):
        length = duration(part)
        beats_file = media / "beats" / file.stem / res / f"{scene}.json"
        beats = json.loads(beats_file.read_text()) if beats_file.exists() else {"title": scene, "beats": []}
        for i, b in enumerate(beats["beats"], 1):
            start = offset + b["start"]
            timeline.append({"scene": scene, "line": i, "start": round(start, 3),
                             "end": round(start + b["duration"], 3),
                             "settled": round(offset + b.get("settled", b["start"] + b["duration"]), 3),
                             "text": b["text"], "words": b["words"]})
        chapters.append((beats["title"], offset, offset + length))
        offset += length
    (media / "timeline").mkdir(parents=True, exist_ok=True)
    (media / "timeline" / f"{file.stem}.json").write_text(json.dumps(timeline, indent=1))

    srt = file.with_suffix(".srt")
    if captions:
        cues = [c for b in timeline for c in caption_cues(b["start"], b["end"], b["words"])]
        srt.write_text("".join(f"{i}\n{_srt_time(a)} --> {_srt_time(b)}\n{text}\n\n" for i, (a, b, text) in enumerate(cues, 1)))
    else:
        srt.unlink(missing_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        # The concat demuxer takes its streams from the first part, and Manim writes no audio
        # for a scene without narration. Give each silent part a silent track.
        for k, p in enumerate(parts):
            if not ffprobe(p, "stream=index", stream="a"):
                parts[k] = tmp / f"silent-{k}.mp4"
                ffmpeg("-i", p, "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-map", "0:v", "-map", "1:a",
                       "-c:v", "copy", "-c:a", "aac", "-shortest", parts[k])
        (tmp / "list.txt").write_text("".join(f"file '{p}'\n" for p in parts))
        meta = ";FFMETADATA1\n" + "".join(
            f"[CHAPTER]\nTIMEBASE=1/1000\nSTART={round(a * 1000)}\nEND={round(b * 1000)}\ntitle={name}\n"
            for name, a, b in chapters)
        (tmp / "chapters.txt").write_text(meta)
        joined = tmp / "joined.mp4"
        # A scene's audio ends at its last line, before its video ends. Copying the audio
        # leaves gaps at the joins that players skip over, so fill them with silence and
        # pad the end to the video length.
        ffmpeg("-f", "concat", "-safe", "0", "-i", tmp / "list.txt", "-c:v", "copy",
               "-af", "aresample=async=1:first_pts=0,apad", "-c:a", "aac", "-b:a", "192k", "-shortest", joined)
        out = file.with_suffix(".mp4")
        if captions:
            ffmpeg("-i", joined, "-i", srt, "-i", tmp / "chapters.txt", "-map", "0", "-map", "1",
                   "-map_metadata", "2", "-map_chapters", "2", "-c", "copy", "-c:s", "mov_text",
                   "-metadata:s:s:0", "language=eng", out)
        else:
            ffmpeg("-i", joined, "-i", tmp / "chapters.txt", "-map", "0", "-map_metadata", "1",
                   "-map_chapters", "1", "-c", "copy", out)

    if not ffprobe(out, "stream=index", stream="a"):
        sys.exit(f"error: {out} has no audio track")
    return out


# ---------------------------------------------------------------- frames


def frames(video: Path, names: list[str], per_sheet: int = 12, cols: int = 3, tile_w: int = 640) -> None:
    """Contact sheets with one tile per narration line, showing the picture as the line ends."""
    from PIL import Image, ImageDraw, ImageFont

    timeline_file = video.parent / "media" / "timeline" / f"{video.stem}.json"
    if timeline_file.exists():
        beats = [b for b in json.loads(timeline_file.read_text()) if not names or b["scene"] in names]
        # Just before the line's block ends: its animations have finished and the next line has not begun.
        shots = [(max(b["start"], b["settled"] - 0.05), f'{b["scene"]} {b["line"]}') for b in beats]
    else:
        total = duration(video)
        shots = [(total * i / 12, f"{total * i / 12:.0f}s") for i in range(12)]
    if not shots:
        sys.exit(f"error: no lines for scenes {' '.join(names)}")

    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
    except OSError:
        font = ImageFont.load_default()
    out_dir = video.parent / "media" / "frames"
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("sheet-*.png"):
        old.unlink()

    with tempfile.TemporaryDirectory() as tmp:
        tiles = []
        for i, (t, _) in enumerate(shots):
            path = Path(tmp) / f"{i}.png"
            ffmpeg("-ss", f"{t:.3f}", "-i", video, "-frames:v", "1", "-vf", f"scale={tile_w}:-2", path)
            tiles.append(Image.open(path).convert("RGB"))
        tile_h, strip = tiles[0].height, 30
        sheets = []
        for k in range(0, len(tiles), per_sheet):
            batch = list(zip(tiles[k:k + per_sheet], shots[k:k + per_sheet]))
            rows = (len(batch) + cols - 1) // cols
            sheet = Image.new("RGB", (cols * tile_w, rows * (tile_h + strip)), (40, 40, 40))
            draw = ImageDraw.Draw(sheet)
            for j, (tile, (t, name)) in enumerate(batch):
                x, y = j % cols * tile_w, j // cols * (tile_h + strip)
                draw.text((x + 8, y + 4), f"{name}   {t:.1f}s", fill=(230, 230, 230), font=font)
                sheet.paste(tile, (x, y + strip))
            path = out_dir / f"sheet-{k // per_sheet + 1}.png"
            sheet.save(path)
            sheets.append(path)
    print(f"{len(shots)} tiles, labelled <scene> <line number> <seconds>:")
    print("\n".join(str(p) for p in sheets))
