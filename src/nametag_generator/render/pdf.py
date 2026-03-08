from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Sequence

from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from nametag_generator.config import LayoutConfig, ThemeConfig
from nametag_generator.models import Attendee
from nametag_generator.render.cards import render_card
from nametag_generator.render.layout import compute_slots, mm_to_px


def _mm_to_points(value_mm: float) -> float:
    return value_mm * 72.0 / 25.4


def build_page_images(
    attendees: Sequence[Attendee],
    layout: LayoutConfig,
    theme: ThemeConfig,
    font_path: Path,
) -> list[Image.Image]:
    page_width_px = mm_to_px(layout.page.width_mm, layout.page.dpi)
    page_height_px = mm_to_px(layout.page.height_mm, layout.page.dpi)
    slots = compute_slots(len(attendees), layout)
    page_images: list[Image.Image] = []

    slot_groups: dict[int, list[tuple[Attendee, int, int]]] = {}
    for attendee, slot in zip(attendees, slots, strict=True):
        slot_groups.setdefault(slot.page_index, []).append((attendee, slot.x_px, slot.y_px))

    for page_index in range(max(slot_groups.keys(), default=-1) + 1):
        page = Image.new("RGB", (page_width_px, page_height_px), "white")
        for attendee, x_px, y_px in slot_groups.get(page_index, []):
            page.paste(render_card(attendee, layout, theme, font_path), (x_px, y_px))
        page_images.append(page)
    return page_images or [Image.new("RGB", (page_width_px, page_height_px), "white")]


def build_pdf_bytes(
    attendees: Sequence[Attendee],
    layout: LayoutConfig,
    theme: ThemeConfig,
    font_path: Path,
) -> bytes:
    page_images = build_page_images(attendees, layout, theme, font_path)
    pdf_buffer = BytesIO()
    page_size_points = (
        _mm_to_points(layout.page.width_mm),
        _mm_to_points(layout.page.height_mm),
    )
    pdf = canvas.Canvas(pdf_buffer, pagesize=page_size_points)
    pdf.setTitle("Nametag Generator Sample Output")
    for page_image in page_images:
        page_buffer = BytesIO()
        page_image.save(page_buffer, format="PNG")
        page_buffer.seek(0)
        pdf.drawImage(
            ImageReader(page_buffer),
            0,
            0,
            width=page_size_points[0],
            height=page_size_points[1],
        )
        pdf.showPage()
    pdf.save()
    return pdf_buffer.getvalue()


def write_pdf(
    attendees: Sequence[Attendee],
    output_path: Path,
    layout: LayoutConfig,
    theme: ThemeConfig,
    font_path: Path,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(build_pdf_bytes(attendees, layout, theme, font_path))
    return output_path
