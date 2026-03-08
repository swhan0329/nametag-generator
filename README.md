# Nametag Generator

Open-source generator for print-ready A4 nametag PDFs from `.xlsx` input.

Release: `0.1.0`

`Nametag Generator` is built for event operators who want a lightweight way to go from a spreadsheet to a physically accurate PDF without opening a design tool. It includes:

- a shared Python rendering core
- a CLI for batch generation
- a local web UI for upload, preview, and export
- public-safe sample data
- millimeter-based layout math for real badge inserts

## Highlights

- Real-size output for badge inserts such as `93mm × 122mm`
- CLI and web UI both use the same rendering engine
- English-first UI with full-page Korean toggle
- Expandable role-style controls:
  default `SPEAKER + STAFF`, expandable up to 6 rows
- Public-safe sample workbook with fictional U.S. names and companies

## Release 0.1.0

Included in `0.1.0`:

- shared package structure under `src/nametag_generator/`
- CLI PDF generation
- local web UI with browser preview
- role label/color editing
- dynamic role rows up to 6
- sample workbook and sample PDF
- automated tests for loader, layout, rendering, CLI, and UI

See [CHANGELOG.md](CHANGELOG.md) for release notes.

## Input Schema

Required columns:

- `name`
- `organization`

Optional columns:

- `role`
- `title`

Typical role values:

- `ATTENDEE` or blank: no role bar
- `HOST`
- `SPEAKER`
- `STAFF`

If `role` is blank or missing entirely, the nametag is generated without a role bar.

## Quick Start

```bash
python3 -m pip install -e ".[dev]"
python3 -m nametag_generator generate sample/attendees.sample.xlsx --output sample/badges.sample.pdf
```

## CLI

Generate a PDF from a workbook:

```bash
python3 -m nametag_generator generate sample/attendees.sample.xlsx --output output/pdf/nametags.pdf
```

You can also run the installed command after `pip install -e .`:

```bash
nametag-generator generate sample/attendees.sample.xlsx --output output/pdf/nametags.pdf
```

## Local Web UI

Run the local app:

```bash
PYTHONPATH=src python3 -m nametag_generator web --host 127.0.0.1 --port 8123
```

Open [http://127.0.0.1:8123](http://127.0.0.1:8123).

The web UI supports:

- workbook upload
- browser preview before export
- English/Korean page toggle
- role label/color editing
- expandable role rows up to 6
- sample workbook and sample PDF download

## Physical Print Size

The default insert size is `93mm × 122mm`.

To confirm physical output:

1. Export the PDF
2. Print at `100%` or `Actual Size`
3. Measure one card with a ruler
4. Confirm it matches `93mm × 122mm`

## Sample Files

Public-safe sample assets:

- [attendees.sample.xlsx](sample/attendees.sample.xlsx)
- [badges.sample.pdf](sample/badges.sample.pdf)

The sample file uses fictional U.S. names and companies so the repository can be shared safely.

## Project Layout

```text
sample/                     Dummy workbook and sample output
src/nametag_generator/      Shared loader, layout, render, CLI, and web UI code
tests/                      Loader, layout, rendering, CLI, and UI tests
ui/                         UI notes
```

## Development

Run the current regression suite:

```bash
python3 -m pytest tests/test_web_ui.py tests/test_cli.py tests/test_render_smoke.py tests/test_loader.py -q
```

## License

MIT. See [LICENSE](LICENSE).
