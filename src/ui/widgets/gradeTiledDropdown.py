"""Specialized tiled dropdown for selecting letter grades (S, A+, A, ...)."""

from __future__ import annotations

from services.score_converter import ScoreConverter
from ui.widgets.tiledDropdown import TiledDropdown


class GradeTiledDropdown(TiledDropdown):
    """Tiled dropdown pre-configured for rating letter grades.

    Presents the ratEA letter grades as tiled rows:

    ::

        [ S ]
        [ A+ ] [ A ] [ A- ]
        [ B+ ] [ B ] [ B- ]
        [ C+ ] [ C ] [ C- ]
        [ D+ ] [ D ] [ D- ]
        [ F ]

    Each tile shows its grade meaning as a tooltip on hover.
    """

    GRADE_ROWS: list[list[str]] = [
        ["S"],
        ["A+", "A", "A-"],
        ["B+", "B", "B-"],
        ["C+", "C", "C-"],
        ["D+", "D", "D-"],
        ["F"],
    ]

    def __init__(
        self,
        **kwargs,
    ):
        """Construct a grade tiled dropdown.

        ``rows`` and ``tooltip_fn`` are fixed by this subclass. All other
        ``TiledDropdown`` keyword arguments are accepted unchanged.
        """
        kwargs.setdefault("rows", self.GRADE_ROWS)
        kwargs.setdefault("tooltip_fn", ScoreConverter.get_grade_meaning)
        super().__init__(**kwargs)