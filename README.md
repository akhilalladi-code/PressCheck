# PressCheck

**A browser-based PDF page-size checker plus an advanced local Python preflight toolkit for designers and print-production teams.**

## Use it online — no installation

**[Launch PressCheck](https://akhilalladi-code.github.io/PressCheck/)**

The hosted GitHub Pages edition runs in your browser. Select a PDF, choose a print profile, inspect page dimensions and image paint operations, and export a JSON, CSV or HTML report. PDF bytes are processed in the browser and are not sent to a PressCheck server.

The hosted edition uses Mozilla PDF.js. It checks PDF readability, page dimensions and image paint operations. It does **not** reliably inspect TrimBox/BleedBox, font embedding, effective image DPI, color spaces, output intent or PDF/X compliance. Do not treat a green result as print certification.

## Hosted edition

- No Python, terminal, account or installation required.
- A4 flyer, A3 poster, business-card and product-label page-size profiles, plus custom inspect-only mode.
- Page-by-page dimensions and size mismatch findings.
- Browser-side PDF processing; files are not uploaded to a backend.
- JSON, CSV and standalone HTML exports.
- Responsive interface for desktop and mobile browsers.

## Advanced local edition

The repository also contains a Python/FastAPI edition for deeper preflight checks:

- MediaBox, TrimBox and BleedBox inspection.
- Font embedding checks.
- Effective raster-image DPI estimates.
- Batch folder inspection and command-line exit codes.
- JSON reports and per-page findings.

### Requirements

- Python 3.11 or newer.

### Install and run

    git clone https://github.com/akhilalladi-code/PressCheck.git
    cd PressCheck
    python -m venv .venv
    # macOS / Linux
    source .venv/bin/activate
    # Windows PowerShell
    .venv/Scripts/Activate.ps1
    python -m pip install -e .
    python -m uvicorn presscheck.api:app --host 127.0.0.1 --port 8765

Open **http://127.0.0.1:8765**. Keep the service bound to loopback; do not expose this unauthenticated API publicly.

### CLI

    presscheck artwork.pdf --profile a4-flyer
    presscheck ./print-files --profile a3-poster --min-dpi 250 --json report.json
    presscheck artwork.pdf --profile business-card --fail-on-warning

Exit code 0 means no errors were found (and no warnings when --fail-on-warning is used); exit code 1 means a file failed a check.

## Built-in local profiles

| Profile | Trim size | Bleed target | Default image resolution |
|---|---:|---:|---:|
| A4 flyer | 210 × 297 mm | 3 mm | 300 DPI |
| A3 poster | 297 × 420 mm | 3 mm | 300 DPI |
| Business card | 90 × 54 mm | 3 mm | 300 DPI |
| Product label | 100 × 150 mm | 2 mm | 300 DPI |

These are starter specifications, not universal printer requirements. Confirm dimensions, bleed, safe area, color profile and export settings with your print vendor.

## Development and tests

    python -m pip install -e '.[dev]'
    ruff check . --select E4,E7,E9,F
    python -m compileall -q presscheck
    pytest -q

GitHub Actions validates the Python package and tests. A separate workflow validates the static browser app and deploys it to GitHub Pages when files under site/ change.

## Privacy and security

- Hosted mode processes PDF bytes in the browser and does not upload them to a PressCheck API.
- The hosted PDF.js library is loaded from cdnjs; using the site therefore requires an internet connection.
- Local API mode is intended for single-user use and binds to 127.0.0.1.
- Local API uploads are limited to 100 MB and are held in memory for analysis.
- Do not expose the local API to a public network without authentication, request limits and a reviewed threat model.

## Important disclaimer

PressCheck is an advisory tool, not a PDF/X validator or a substitute for your printer's approved prepress workflow. PDF page boxes do not prove that artwork visually extends through bleed. Always request and follow your printer's current PDF export specification.

## License

MIT — Copyright (c) 2026 Akhil Alladi. See LICENSE.
