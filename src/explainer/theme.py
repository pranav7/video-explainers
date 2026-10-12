"""Colours, fonts and sizes shared by every kit helper.

Use the accent names in script.md palettes: SKY, MINT, AMBER, CORAL, VIOLET, AQUA,
ROSE, PEACH, LIME. They are tuned to read well on the background (BG).
"""

from __future__ import annotations

from functools import lru_cache

from manim import ManimColor, interpolate_color

# Neutrals, darkest to lightest.
BG = ManimColor("#0B0F14")  # frame background
SURFACE = ManimColor("#131A22")  # cards, panels, windows
RAISED = ManimColor("#1B2430")  # header rows, title bars, hover
LINE = ManimColor("#2B3542")  # neutral strokes, tracks, grid lines
FAINT = ManimColor("#5D6B7A")  # disabled, placeholders, de-emphasized text
SUBTLE = ManimColor("#9AA7B5")  # secondary text, neutral arrows
INK = ManimColor("#E8EEF4")  # primary text
MUTED = SUBTLE  # older name

# Accents.
SKY = ManimColor("#5EA8FF")
MINT = ManimColor("#3DD68C")
AMBER = ManimColor("#F5B83D")
CORAL = ManimColor("#FF6B6B")
VIOLET = ManimColor("#A98BFF")
AQUA = ManimColor("#2CCCE4")
ROSE = ManimColor("#F472B6")
PEACH = ManimColor("#FF9F5A")
LIME = ManimColor("#A6E05A")
ACCENTS = [SKY, MINT, AMBER, CORAL, VIOLET, AQUA, ROSE, PEACH, LIME]

# Sizes, in Manim font_size units and scene units.
TEXT_SIZE = 30
SMALL_SIZE = 24
TITLE_SIZE = 42
CODE_SIZE = 24
RADIUS = 0.16  # corner radius of cards and panels
STROKE = 2.5  # stroke width of outlines and connectors


@lru_cache
def _installed() -> set[str]:
    import manimpango

    return set(manimpango.list_fonts())


def _font(*names: str) -> str:
    """The first installed font of `names`. `explainer doctor` installs the first choice."""
    return next((n for n in names if n in _installed()), names[-1])


SANS = _font("Inter", "Helvetica Neue")
# The NL ("no ligatures") build: code keeps "<=" and "==" as the characters people type.
MONO = _font("JetBrains Mono NL", "JetBrains Mono", "Menlo")


def tint(color, amount: float = 0.16) -> ManimColor:
    """`color` mixed into the background: a solid fill that reads as a tint of the accent."""
    return interpolate_color(BG, ManimColor(color), amount)
