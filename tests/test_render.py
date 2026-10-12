import json
import subprocess
from pathlib import Path

from explainer.render import assemble, render, scenes_in

SCENES = '''
from explainer.kit import *


class One(ExplainerScene):
    title = "First chapter"

    def construct(self):
        self.say("Here is a pipeline.", appear(pipeline(["read", "rules", "result"], buff=1.5)))
        self.fade_all()


class Two(ExplainerScene):
    def construct(self):
        self.say("And here is a label.", FadeIn(label("hello")))
        self.fade_all()
'''


def probe(path: Path, *args) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-of", "json", *args, str(path)], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def test_render_joins_scenes_with_chapters_and_optional_captions(tmp_path, capsys):
    file = tmp_path / "video.py"
    file.write_text(SCENES)
    render(file, [], "l", 2)

    video = tmp_path / "video.mp4"
    streams = {s["codec_type"] for s in probe(video, "-show_streams")["streams"]}
    assert {"video", "audio"} <= streams and "subtitle" not in streams
    assert not (tmp_path / "video.srt").exists()
    chapters = probe(video, "-show_chapters")["chapters"]
    assert [c["tags"]["title"] for c in chapters] == ["First chapter", "Two"]
    assert "Layout check: no warnings" in capsys.readouterr().out

    assemble(file, ["One", "Two"], "l", captions=True)
    assert "subtitle" in {s["codec_type"] for s in probe(video, "-show_streams")["streams"]}
    assert "Here is a pipeline." in (tmp_path / "video.srt").read_text()


def test_silent_first_scene_keeps_the_audio(tmp_path):
    file = tmp_path / "video.py"
    file.write_text('''
from explainer.kit import *


class Card(ExplainerScene):
    def construct(self):
        self.play(appear(title("No narration here")))
        self.wait(0.5)
        self.fade_all()


class Talk(ExplainerScene):
    def construct(self):
        self.say("Now the narration starts.", appear(pipeline(["one", "two", "three"], buff=1.5)))
        self.fade_all()
''')
    render(file, [], "l", 2)
    streams = {s["codec_type"] for s in probe(tmp_path / "video.mp4", "-show_streams")["streams"]}
    assert "audio" in streams


def test_base_classes_are_not_scenes(tmp_path):
    file = tmp_path / "video.py"
    file.write_text('''
from explainer.kit import *


class Base(ExplainerScene):
    def heading(self, text):
        return title(text)


class One(Base):
    def construct(self):
        pass
''')
    assert scenes_in(file) == ["One"]


DISAPPEAR = '''
from explainer.kit import *


class S(ExplainerScene):
    def construct(self):
        seq = sequence(["A", "B", "C"], [(0, 1, "first"), (1, 2, "second")], width=9)
        self.play(appear(*seq[0]), *[Create(l) for l in seq[1]])
        for m in seq[2]:
            self.play(Create(m[0]), FadeIn(m[1]))
        self.play(disappear(seq))
        left = [m for m in self.mobjects if m.family_members_with_points()]
        assert not left, left
'''


def test_disappear_removes_a_group_added_part_by_part(tmp_path):
    import sys

    (tmp_path / "video.py").write_text(DISAPPEAR)
    result = subprocess.run([sys.executable, "-m", "manim", "render", "-ql", "--dry_run", "-v", "ERROR", "video.py", "S"],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout[-1500:] + result.stderr[-1500:]
