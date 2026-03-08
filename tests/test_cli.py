from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from nametag_generator.cli import app


def test_cli_generates_pdf(tmp_path: Path) -> None:
    output_path = tmp_path / "nametags.pdf"
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "generate",
            "sample/attendees.sample.xlsx",
            "--output",
            str(output_path),
        ],
    )
    assert result.exit_code == 0
    assert output_path.exists()
