from __future__ import annotations

from pathlib import Path

import typer
import uvicorn

from nametag_generator.config import GeneratorConfig, LayoutConfig
from nametag_generator.errors import FontResolutionError, WorkbookValidationError
from nametag_generator.loaders.xlsx import load_attendees_from_xlsx
from nametag_generator.service import generate_pdf
from nametag_generator.web import create_app


app = typer.Typer(add_completion=False, help="Generate print-ready nametag PDFs.")


@app.command()
def generate(
    input_path: Path = typer.Argument(..., exists=True, readable=True),
    output_path: Path = typer.Option(
        Path("output/pdf/nametags.pdf"),
        "--output",
        "-o",
        help="Where to write the generated PDF.",
    ),
    card_width_mm: float = typer.Option(93.0, help="Card width in millimeters."),
    card_height_mm: float = typer.Option(122.0, help="Card height in millimeters."),
    sheet_name: str | None = typer.Option(None, help="Workbook sheet name."),
) -> None:
    try:
        attendees = load_attendees_from_xlsx(input_path, sheet_name=sheet_name)
        config = GeneratorConfig(
            layout=LayoutConfig(
                card_width_mm=card_width_mm,
                card_height_mm=card_height_mm,
            )
        )
        result = generate_pdf(attendees, config=config, output_path=output_path)
    except (WorkbookValidationError, FontResolutionError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(
        f"Generated {output_path} using font {result.font_path.name} "
        f"for {len(attendees)} attendees."
    )


@app.command()
def web(
    host: str = typer.Option("127.0.0.1", help="Host for the local web UI."),
    port: int = typer.Option(8000, help="Port for the local web UI."),
) -> None:
    uvicorn.run(create_app(), host=host, port=port)


def main() -> None:
    app()
