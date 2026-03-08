# UI Notes

The v1 UI is intentionally thin. It is a local FastAPI app that:

- serves a single upload form
- accepts an `.xlsx`
- calls the shared Python generation service
- returns a generated PDF

This keeps the rendering logic in one place while leaving room to replace the first UI later with a richer frontend.

## Current Contract

- `GET /` renders the upload page
- `POST /generate` accepts:
  - `workbook`
  - `card_width_mm`
  - `card_height_mm`

The UI adapter is the only layer that handles upload and temporary files. Layout math and PDF generation stay in `src/nametag_generator/`.
