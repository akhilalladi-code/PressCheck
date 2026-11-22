# PressCheck

**A browser-accessible PDF print preflight powered by a Python/FastAPI and PyMuPDF backend, with a command-line edition for batch work.**

## Use it online

**Website:** https://akhilalladi-code.github.io/PressCheck/

The GitHub Pages frontend connects to the deployed Python API at https://presscheck-api-akhilalladi-tamq.onrender.com. It inspects PDF page boxes, trim size, bleed, embedded fonts and effective raster-image DPI. The hosted service currently accepts PDF files up to 25 MB on its free compute configuration.

### Hosted backend (Render)

The production Blueprint is connected to this repository's `main` branch and manages the service `presscheck-api-akhilalladi-tamq` in the Singapore region.

- **API base URL:** https://presscheck-api-akhilalladi-tamq.onrender.com
- **Health endpoint:** https://presscheck-api-akhilalladi-tamq.onrender.com/api/health
- **Health response:** JSON with `"status":"ok"` and `"engine":"python"`
- **Deployment configuration:** [render.yaml](render.yaml)
- **Render dashboard:** https://dashboard.render.com/web/srv-dc0g4i4s728c73a5n6kg

The frontend endpoint is configured in `site/config.js`. If the service is recreated and Render assigns a different hostname, update that file and the `PRESSCHECK_API_BASE_URL` used by the CI smoke test, then push to `main`.

### Free-tier behavior and limits

- Render's free web services sleep after 15 minutes without traffic; the first request after sleep can take around one minute to wake the service.
- The free service may restart at any time and has limited CPU and memory. The hosted API therefore caps PDFs at 25 MB.
- Render documents 750 free instance hours per workspace per calendar month. Usage, bandwidth and pipeline limits apply.
- This is suitable for a personal/hobby project, not a production service with uptime guarantees. See [Render's current free-instance limits](https://render.com/docs/free).

### Upload privacy

The hosted frontend sends the selected PDF over HTTPS to the PressCheck API for analysis. The API does not maintain a document library and closes the uploaded file after processing. Render free services have ephemeral filesystems, but do not upload confidential, regulated or sensitive documents to this public demo. Operational request metadata may be handled under Render's own service policies.

## Advanced local edition

The same Python engine can run locally without sending files to a cloud service.

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

## Built-in print profiles

| Profile | Trim size | Bleed target | Default image resolution |
|---|---:|---:|---:|
| A4 flyer | 210 × 297 mm | 3 mm | 300 DPI |
| A3 poster | 297 × 420 mm | 3 mm | 300 DPI |
| Business card | 90 × 54 mm | 3 mm | 300 DPI |
| Product label | 100 × 150 mm | 2 mm | 300 DPI |

These are starter specifications, not universal printer requirements. Confirm dimensions, bleed, safe area, color profile and export settings with your print vendor.

## Development and tests

    python -m pip install -e ".[dev]"
    ruff check . --select E4,E7,E9,F
    python -m compileall -q presscheck
    pytest -q

GitHub Actions runs the Python tests and validates/deploys the static frontend. The main-branch CI also performs a live API smoke test: it checks health and profiles, generates a disposable one-page PDF, uploads it to `/api/preflight`, and validates the returned report.

## Important disclaimer

PressCheck is an advisory tool, not a PDF/X validator or a substitute for your printer's approved prepress workflow. PDF page boxes do not prove that artwork visually extends through bleed. Color-space and output-intent compliance are not certified.

## License

MIT — Copyright (c) 2026 Akhil Alladi. See LICENSE.
