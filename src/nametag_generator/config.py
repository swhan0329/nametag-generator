from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from nametag_generator.models import RoleStyle
from nametag_generator.themes.default import DEFAULT_FONT_CANDIDATES, DEFAULT_ROLE_STYLES


PAGE_SIZES_MM: dict[str, tuple[float, float]] = {
    "A4": (210.0, 297.0),
}


@dataclass(slots=True)
class PageConfig:
    width_mm: float = 210.0
    height_mm: float = 297.0
    dpi: int = 300


@dataclass(slots=True)
class LayoutConfig:
    card_width_mm: float = 93.0
    card_height_mm: float = 122.0
    left_margin_mm: float = 8.0
    right_margin_mm: float = 8.0
    top_margin_mm: float = 19.0
    bottom_margin_mm: float = 19.0
    column_gap_mm: float = 8.0
    row_gap_mm: float = 15.0
    page: PageConfig = field(default_factory=PageConfig)

    @classmethod
    def from_page_size(
        cls,
        page_size: str = "A4",
        **overrides: float | int,
    ) -> "LayoutConfig":
        width_mm, height_mm = PAGE_SIZES_MM[page_size.upper()]
        page = PageConfig(
            width_mm=float(overrides.pop("page_width_mm", width_mm)),
            height_mm=float(overrides.pop("page_height_mm", height_mm)),
            dpi=int(overrides.pop("dpi", 300)),
        )
        return cls(page=page, **overrides)


@dataclass(slots=True)
class ThemeConfig:
    role_styles: dict[str, RoleStyle] = field(
        default_factory=lambda: dict(DEFAULT_ROLE_STYLES)
    )


@dataclass(slots=True)
class GeneratorConfig:
    layout: LayoutConfig = field(default_factory=LayoutConfig)
    theme: ThemeConfig = field(default_factory=ThemeConfig)
    font_candidates: Sequence[Path | str] = field(
        default_factory=lambda: tuple(DEFAULT_FONT_CANDIDATES)
    )
