from __future__ import annotations

from pathlib import Path

import pytest
from openpyxl import Workbook

from nametag_generator.errors import WorkbookValidationError
from nametag_generator.loaders.xlsx import load_attendees_from_xlsx


def _write_workbook(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(headers)
    for row in rows:
        worksheet.append(row)
    workbook.save(path)


def test_load_attendees_success(tmp_path: Path) -> None:
    workbook_path = tmp_path / "attendees.xlsx"
    _write_workbook(
        workbook_path,
        ["name", "organization", "role", "title"],
        [
            ["Han Seowoo", "B Garage", "HOST", "AI Engineer"],
            ["Jiyoung Lee", "Nota AI", "ATTENDEE", ""],
        ],
    )
    attendees = load_attendees_from_xlsx(workbook_path)
    assert len(attendees) == 2
    assert attendees[0].name == "Han Seowoo"
    assert attendees[1].role == "ATTENDEE"


def test_missing_required_column_raises(tmp_path: Path) -> None:
    workbook_path = tmp_path / "invalid.xlsx"
    _write_workbook(
        workbook_path,
        ["name", "role", "title"],
        [["Han Seowoo", "B Garage", "AI Engineer"]],
    )
    with pytest.raises(WorkbookValidationError):
        load_attendees_from_xlsx(workbook_path)


def test_missing_role_column_defaults_to_none(tmp_path: Path) -> None:
    workbook_path = tmp_path / "attendees-no-role.xlsx"
    _write_workbook(
        workbook_path,
        ["name", "organization", "title"],
        [["Han Seowoo", "B Garage", "AI Engineer"]],
    )
    attendees = load_attendees_from_xlsx(workbook_path)
    assert len(attendees) == 1
    assert attendees[0].role is None
