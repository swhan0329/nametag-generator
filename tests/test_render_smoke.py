from __future__ import annotations

from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from nametag_generator.config import GeneratorConfig
from nametag_generator.loaders.xlsx import load_attendees_from_xlsx
from nametag_generator.service import generate_pdf


def test_generate_pdf_from_sample_workbook() -> None:
    sample_workbook = Path("sample/attendees.sample.xlsx")
    attendees = load_attendees_from_xlsx(sample_workbook)
    result = generate_pdf(attendees, config=GeneratorConfig())
    reader = PdfReader(BytesIO(result.pdf_bytes))
    assert len(reader.pages) >= 1
    page = reader.pages[0]
    assert round(float(page.mediabox.width) * 25.4 / 72, 2) == 210.0
