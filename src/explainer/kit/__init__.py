"""Building blocks for explainer scenes.

`from explainer.kit import *` gives all of Manim, the scene API (ExplainerScene,
NarrationMixin), the theme (colours, fonts) and the helpers in the modules below. Each
helper returns a plain Manim mobject, so .next_to(), .animate, Transform and the rest
work as usual.
"""

from manim import *  # noqa: F403

from explainer.kit.data import *  # noqa: F403
from explainer.kit.diagrams import *  # noqa: F403
from explainer.kit.motion import *  # noqa: F403
from explainer.kit.shapes import *  # noqa: F403
from explainer.kit.text import *  # noqa: F403
from explainer.theme import *  # noqa: F403
from explainer.narration import ExplainerScene, NarrationMixin  # noqa: F401

# The order in which `explainer guide` lists the helpers.
MODULES = ["text", "shapes", "diagrams", "data", "motion"]


def fit(m, width: float = 12.8, height: float = 7.0):
    """Scale m down, never up, until it fits inside width x height."""
    if m.width > width:
        m.scale_to_fit_width(width)
    if m.height > height:
        m.scale_to_fit_height(height)
    return m
