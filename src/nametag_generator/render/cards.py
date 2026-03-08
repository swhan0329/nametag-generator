from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont

from nametag_generator.config import LayoutConfig, ThemeConfig
from nametag_generator.models import Attendee
from nametag_generator.render.layout import mm_to_px
from nametag_generator.themes.default import resolve_role_style


@dataclass(slots=True)
class CardMetrics:
    width_px: int
    height_px: int
    content_width_px: int
    center_x_px: int
    role_band_height_px: int


def _load_font(font_path: Path, size_px: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(font_path), size_px)


def _text_size(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
) -> tuple[int, int]:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return right - left, bottom - top


def _fit_single_line(
    draw: ImageDraw.ImageDraw,
    text: str,
    font_path: Path,
    max_width: int,
    start_size: int,
    min_size: int,
) -> ImageFont.FreeTypeFont:
    size = start_size
    while size > min_size:
        font = _load_font(font_path, size)
        width, _ = _text_size(draw, text, font)
        if width <= max_width:
            return font
        size -= 2
    return _load_font(font_path, min_size)


def _wrap_tokens(text: str) -> tuple[list[str], str]:
    if " " in text:
        return [part for part in text.split() if part], " "
    return list(text), ""


def _ellipsize(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> str:
    candidate = text
    while candidate:
        width, _ = _text_size(draw, f"{candidate}...", font)
        if width <= max_width:
            return f"{candidate}..."
        candidate = candidate[:-1]
    return "..."


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
    max_lines: int,
) -> list[str]:
    if not text:
        return []

    tokens, separator = _wrap_tokens(text)
    lines: list[str] = []
    current = ""

    for token in tokens:
        candidate = token if not current else f"{current}{separator}{token}"
        width, _ = _text_size(draw, candidate, font)
        if width <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
            current = token
        else:
            if separator == " ":
                return _wrap_text(draw, token, font, max_width, max_lines)
            lines.append(_ellipsize(draw, token, font, max_width))
            current = ""
        if len(lines) == max_lines:
            return lines

    if current:
        lines.append(current)
    if len(lines) <= max_lines:
        return lines
    kept = lines[: max_lines - 1]
    kept.append(_ellipsize(draw, separator.join(lines[max_lines - 1 :]), font, max_width))
    return kept


def _fit_info_lines(
    draw: ImageDraw.ImageDraw,
    font_path: Path,
    title: str | None,
    organization: str | None,
    max_width: int,
    max_total_lines: int,
) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    blocks = [value for value in [title, organization] if value]
    for size in range(92, 40, -2):
        font = _load_font(font_path, size)
        lines: list[str] = []
        valid = True
        for block in blocks:
            wrapped = _wrap_text(draw, block, font, max_width, 2)
            if len(wrapped) > 2:
                valid = False
                break
            lines.extend(wrapped)
        if valid and len(lines) <= max_total_lines:
            return font, lines
    fallback = _load_font(font_path, 40)
    fallback_lines: list[str] = []
    for block in blocks:
        fallback_lines.extend(_wrap_text(draw, block, fallback, max_width, 2)[:2])
    return fallback, fallback_lines[:max_total_lines]


def _format_organization(organization: str | None) -> str | None:
    if not organization:
        return None
    return organization if organization.startswith("@") else f"@{organization}"


def _draw_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    center_x: int,
    y: int,
    font: ImageFont.FreeTypeFont,
    fill: str,
) -> int:
    width, height = _text_size(draw, text, font)
    draw.text((center_x - width / 2, y), text, font=font, fill=fill)
    return height


def _draw_centered_lines(
    draw: ImageDraw.ImageDraw,
    lines: Iterable[str],
    center_x: int,
    start_y: int,
    font: ImageFont.FreeTypeFont,
    fill: str,
    line_gap: int,
) -> None:
    y = start_y
    for line in lines:
        height = _draw_centered_text(draw, line, center_x, y, font, fill)
        y += height + line_gap


def build_card_metrics(layout: LayoutConfig, has_role_bar: bool) -> CardMetrics:
    width_px = mm_to_px(layout.card_width_mm, layout.page.dpi)
    height_px = mm_to_px(layout.card_height_mm, layout.page.dpi)
    role_band_height_px = mm_to_px(24.0, layout.page.dpi) if has_role_bar else 0
    content_width_px = width_px - mm_to_px(16.0, layout.page.dpi)
    center_x_px = width_px // 2
    return CardMetrics(
        width_px=width_px,
        height_px=height_px,
        content_width_px=content_width_px,
        center_x_px=center_x_px,
        role_band_height_px=role_band_height_px,
    )


def render_card(
    attendee: Attendee,
    layout: LayoutConfig,
    theme: ThemeConfig,
    font_path: Path,
) -> Image.Image:
    role_style = resolve_role_style(attendee.role, theme.role_styles)
    metrics = build_card_metrics(layout, role_style is not None and role_style.show_bar)
    card = Image.new("RGB", (metrics.width_px, metrics.height_px), "white")
    draw = ImageDraw.Draw(card)
    draw.rectangle(
        (0, 0, metrics.width_px - 1, metrics.height_px - 1),
        outline="#767676",
        width=3,
    )

    name_font = _fit_single_line(
        draw,
        attendee.name,
        font_path,
        max_width=metrics.content_width_px,
        start_size=240,
        min_size=132,
    )
    name_height = _text_size(draw, attendee.name, name_font)[1]

    info_font, info_lines = _fit_info_lines(
        draw,
        font_path,
        attendee.title,
        _format_organization(attendee.organization),
        max_width=metrics.content_width_px,
        max_total_lines=4,
    )
    info_line_height = _text_size(draw, "Ag", info_font)[1]
    line_gap = max(6, info_font.size // 10)
    total_info_height = len(info_lines) * info_line_height + max(
        0, len(info_lines) - 1
    ) * line_gap
    name_gap = mm_to_px(10.0, layout.page.dpi)
    total_group_height = name_height + (name_gap if info_lines else 0) + total_info_height

    if role_style is not None and role_style.show_bar:
        band_top = metrics.height_px - metrics.role_band_height_px
        available_top = mm_to_px(10.0, layout.page.dpi)
        available_bottom = band_top - mm_to_px(10.0, layout.page.dpi)
        draw.rectangle(
            (0, band_top, metrics.width_px, metrics.height_px),
            fill=role_style.background_color,
        )
        role_font = _fit_single_line(
            draw,
            role_style.label,
            font_path,
            max_width=metrics.width_px - mm_to_px(12.0, layout.page.dpi),
            start_size=186,
            min_size=112,
        )
        role_height = _text_size(draw, role_style.label, role_font)[1]
        role_y = band_top + (metrics.role_band_height_px - role_height) // 2 - mm_to_px(
            3.0, layout.page.dpi
        )
        _draw_centered_text(
            draw,
            role_style.label,
            metrics.center_x_px,
            role_y,
            role_font,
            role_style.text_color,
        )
    else:
        available_top = mm_to_px(10.0, layout.page.dpi)
        available_bottom = metrics.height_px - mm_to_px(10.0, layout.page.dpi)

    available_height = available_bottom - available_top
    group_top = available_top + max(0, (available_height - total_group_height) // 2)
    name_y = group_top
    info_top = name_y + name_height + (name_gap if info_lines else 0)

    _draw_centered_text(draw, attendee.name, metrics.center_x_px, name_y, name_font, "#000000")
    _draw_centered_lines(
        draw,
        info_lines,
        metrics.center_x_px,
        info_top,
        info_font,
        "#000000",
        line_gap,
    )
    return card
