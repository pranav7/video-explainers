import os

import pytest


@pytest.fixture(autouse=True)
def in_tmp(tmp_path, monkeypatch):
    """Run each test in its own directory, so media/ files do not mix."""
    monkeypatch.chdir(tmp_path)
    os.environ.setdefault("PYTHONWARNINGS", "ignore")
