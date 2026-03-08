from __future__ import annotations

from dataclasses import dataclass
from math import floor

from nametag_generator.config import LayoutConfig


@dataclass(slots=True)
class Slot:
    page_index: int
    slot_index: int
    x_px: int
    y_px: int


def mm_to_px(mm_value: float, dpi: int) -> int:
    return round(mm_value * dpi / 25.4)


def effective_card_size_mm(layout: LayoutConfig) -> tuple[float, float]:
    page_width_px = mm_to_px(layout.page.width_mm, layout.page.dpi)
    page_height_px = mm_to_px(layout.page.height_mm, layout.page.dpi)
    card_width_px = mm_to_px(layout.card_width_mm, layout.page.dpi)
    card_height_px = mm_to_px(layout.card_height_mm, layout.page.dpi)
    return (
        card_width_px / page_width_px * layout.page.width_mm,
        card_height_px / page_height_px * layout.page.height_mm,
    )


def cards_per_row(layout: LayoutConfig) -> int:
    available_width = (
        layout.page.width_mm - layout.left_margin_mm - layout.right_margin_mm
    )
    count = floor(
        (available_width + layout.column_gap_mm)
        / (layout.card_width_mm + layout.column_gap_mm)
    )
    if count < 1:
        raise ValueError("Card width and margins do not fit on the page.")
    return count


def cards_per_column(layout: LayoutConfig) -> int:
    available_height = (
        layout.page.height_mm - layout.top_margin_mm - layout.bottom_margin_mm
    )
    count = floor(
        (available_height + layout.row_gap_mm)
        / (layout.card_height_mm + layout.row_gap_mm)
    )
    if count < 1:
        raise ValueError("Card height and margins do not fit on the page.")
    return count


def cards_per_page(layout: LayoutConfig) -> int:
    return cards_per_row(layout) * cards_per_column(layout)


def compute_slots(item_count: int, layout: LayoutConfig) -> list[Slot]:
    row_count = cards_per_row(layout)
    column_count = cards_per_column(layout)
    slots_per_page = row_count * column_count
    dpi = layout.page.dpi

    left_margin_px = mm_to_px(layout.left_margin_mm, dpi)
    top_margin_px = mm_to_px(layout.top_margin_mm, dpi)
    card_width_px = mm_to_px(layout.card_width_mm, dpi)
    card_height_px = mm_to_px(layout.card_height_mm, dpi)
    column_gap_px = mm_to_px(layout.column_gap_mm, dpi)
    row_gap_px = mm_to_px(layout.row_gap_mm, dpi)

    slots: list[Slot] = []
    for index in range(item_count):
        page_index = index // slots_per_page
        slot_index = index % slots_per_page
        row = slot_index // row_count
        column = slot_index % row_count
        slots.append(
            Slot(
                page_index=page_index,
                slot_index=slot_index,
                x_px=left_margin_px + column * (card_width_px + column_gap_px),
                y_px=top_margin_px + row * (card_height_px + row_gap_px),
            )
        )
    return slots
