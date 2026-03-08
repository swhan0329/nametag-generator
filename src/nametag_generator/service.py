from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Sequence

from nametag_generator.config import GeneratorConfig
from nametag_generator.models import Attendee
from nametag_generator.render.fonts import resolve_font_path
from nametag_generator.render.pdf import build_page_images, build_pdf_bytes, write_pdf


@dataclass(slots=True)
class GenerationResult:
    output_path: Path | None
    pdf_bytes: bytes
    font_path: Path


def generate_pdf(
    attendees: Sequence[Attendee],
    config: GeneratorConfig | None = None,
    output_path: Path | None = None,
) -> GenerationResult:
    resolved_config = config or GeneratorConfig()
    font_path = resolve_font_path(resolved_config.font_candidates)
    pdf_bytes = build_pdf_bytes(
        attendees=attendees,
        layout=resolved_config.layout,
        theme=resolved_config.theme,
        font_path=font_path,
    )
    if output_path is not None:
        write_pdf(
            attendees=attendees,
            output_path=output_path,
            layout=resolved_config.layout,
            theme=resolved_config.theme,
            font_path=font_path,
        )
    return GenerationResult(
        output_path=output_path,
        pdf_bytes=pdf_bytes,
        font_path=font_path,
    )


def generate_preview_png(
    attendees: Sequence[Attendee],
    config: GeneratorConfig | None = None,
) -> bytes:
    resolved_config = config or GeneratorConfig()
    font_path = resolve_font_path(resolved_config.font_candidates)
    page_images = build_page_images(
        attendees=attendees,
        layout=resolved_config.layout,
        theme=resolved_config.theme,
        font_path=font_path,
    )
    buffer = BytesIO()
    page_images[0].save(buffer, format="PNG")
    return buffer.getvalue()
