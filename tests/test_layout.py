from __future__ import annotations

from nametag_generator.config import LayoutConfig
from nametag_generator.render.layout import (
    cards_per_column,
    cards_per_page,
    cards_per_row,
    compute_slots,
    effective_card_size_mm,
)


def test_a4_layout_packs_four_cards() -> None:
    layout = LayoutConfig()
    assert cards_per_row(layout) == 2
    assert cards_per_column(layout) == 2
    assert cards_per_page(layout) == 4


def test_slot_coordinates_are_stable() -> None:
    layout = LayoutConfig()
    slots = compute_slots(5, layout)
    assert slots[0].page_index == 0
    assert slots[1].x_px > slots[0].x_px
    assert slots[2].y_px > slots[0].y_px
    assert slots[4].page_index == 1


def test_effective_card_size_is_nearly_exact() -> None:
    layout = LayoutConfig()
    width_mm, height_mm = effective_card_size_mm(layout)
    assert abs(width_mm - 93.0) < 0.05
    assert abs(height_mm - 122.0) < 0.05
