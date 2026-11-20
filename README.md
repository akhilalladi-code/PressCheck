# PressCheck

**Local-first PDF print preflight for designers and production teams.** Inspect trim size, bleed, embedded fonts and effective image resolution before sending artwork to a printer. PDF files are processed by a local Python service; they are not uploaded to a third-party cloud.

> PressCheck is an advisory preflight tool. It does not certify PDF/X compliance, color-management conformance or visual artwork coverage. Always follow the print provider's specification.

## Features

- Inspect PDF page count, trim dimensions, MediaBox, TrimBox and BleedBox.
- Compare trim dimensions against A4 flyer, A3 poster, business card and product-label profiles.
- Flag missing/insufficient bleed, unembedded fonts and images below the selected effective-DPI threshold.
- Review findings and per-page details in a responsive browser interface.
- Export findings as JSON or CSV and save a standalone HTML report.
- Run batch checks from the CLI, including CI-friendly exit codes and JSON output.
- Keep processing local; no account, database, external API key or cloud upload is required.

## Requirements

- Python 3.11 or newer.
- macOS, Windows or Linux.

## Install and run

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell
.venv\\Scripts\\Activate.ps1
python -m pip install -e .
python -m uvicorn presscheck.api:app --host 127.0.0.1 --port 8765
```

Open **http://127.0.0.1:8765**. Keep the server bound to loopback; do not expose this unauthenticated local service to a public network.

## CLI

```bash
presscheck artwork.pdf --profile a4-flyer
presscheck ./print-files --profile a3-poster --min-dpi 250 --json report.json
presscheck artwork.pdf --profile business-card --fail-on-warning
```

Exit codes: `0` when no errors are found (and no warnings when `--fail-on-warning` is set), `1` when a file fails a check. Invalid input or missing files are reported to stderr.

## Built-in profiles

| Profile | Trim size | Bleed | Default image resolution |
|---|---:|---:|---:|
| A4 flyer | 210 × 297 mm | 3 mm | 300 DPI |
| A3 poster | 297 × 420 mm | 3 mm | 300 DPI |
| Business card | 90 × 54 mm | 3 mm | 300 DPI |
| Product label | 100 × 150 mm | 2 mm | 300 DPI |

These are starter specifications, not universal printer requirements. Confirm dimensions, bleed, safe area, color profile and export settings with your print vendor.

## What is checked

- **Page geometry:** compares TrimBox dimensions to the selected profile within its tolerance.
- **Bleed:** compares BleedBox and TrimBox dimensions. A box alone cannot prove that background artwork reaches the bleed edge.
- **Fonts:** reports fonts returned by the PDF parser that do not appear embedded.
- **Images:** estimates effective DPI from image pixel dimensions and placement bounds. Vector artwork is not raster-DPI checked.

Color-space and output-intent inspection is not certified in this release. Password-protected PDFs are rejected. Files are limited to 100 MB per inspection.

## Development and tests

```bash
python -m pip install -e '.[dev]'
ruff check .
python -m compileall -q presscheck
pytest -q
```

GitHub Actions runs lint, bytecode compilation and tests on pushes and pull requests to `main`.

## Security and privacy

- The service is intended for single-user local use and binds to `127.0.0.1`.
- PDF bytes are read into memory for analysis and are not persisted by the API.
- Upload size is capped at 100 MB; file extension and PDF signature are checked.
- No secrets or environment variables are required.
- Do not bind the service to `0.0.0.0` or deploy it publicly without authentication, request limits and a reviewed threat model.

## License

MIT — Copyright (c) 2026 Akhil Alladi. See [LICENSE](LICENSE).
