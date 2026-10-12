"""Lucide line icons (ISC license, https://lucide.dev/icons). `explainer doctor` downloads them."""

from __future__ import annotations

import difflib
import io
import os
import shutil
import tarfile
import tempfile
import urllib.request
from pathlib import Path

LUCIDE_VERSION = "1.47.0"
ICON_DIR = Path(os.environ.get("EXPLAINER_ICONS", f"~/.cache/explainer/lucide-{LUCIDE_VERSION}")).expanduser()
# Names the first version of the kit used.
ALIASES = {"doc": "file-text", "db": "database", "person": "user"}


def fetch_icons() -> Path:
    """Download the pinned Lucide release into ICON_DIR, once."""
    if ICON_DIR.exists():
        return ICON_DIR
    url = f"https://registry.npmjs.org/lucide-static/-/lucide-static-{LUCIDE_VERSION}.tgz"
    with urllib.request.urlopen(url, timeout=60) as response:
        archive = tarfile.open(fileobj=io.BytesIO(response.read()), mode="r:gz")
    with tempfile.TemporaryDirectory(dir=ICON_DIR.parent if ICON_DIR.parent.exists() else None) as tmp:
        for member in archive.getmembers():
            if member.isfile() and member.name.startswith("package/icons/") and member.name.endswith(".svg"):
                member.name = Path(member.name).name
                archive.extract(member, tmp, filter="data")
        ICON_DIR.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(tmp, ICON_DIR)
    return ICON_DIR


def icon_path(name: str) -> Path:
    name = ALIASES.get(name, name)
    path = ICON_DIR / f"{name}.svg"
    if path.exists():
        return path
    if not ICON_DIR.exists():
        raise RuntimeError("Lucide icons are not downloaded. Run `explainer doctor`.")
    close = difflib.get_close_matches(name, [p.stem for p in ICON_DIR.glob("*.svg")], n=6, cutoff=0.5)
    raise ValueError(f"no Lucide icon {name!r}. Close names: {', '.join(close) or 'none'}. All: https://lucide.dev/icons")
