# PressCheck

**A browser-accessible PDF print preflight powered by a Python/FastAPI and PyMuPDF backend, with a command-line edition for batch work.**

## Use it online

**Website:** https://akhilalladi-code.github.io/PressCheck/

The GitHub Pages frontend connects to a separately hosted Python API. It inspects PDF page boxes, trim size, bleed, embedded fonts and effective raster-image DPI. The hosted service currently accepts PDF files up to 25 MB on its free compute configuration.

### First-time backend deployment (Render)

1. Create a free account at [Render](https://render.com/).
2. In the Render dashboard choose **New → Blueprint**.
3. Connect the GitHub repository `akhilalladi-code/PressCheck`.
4. Render detects the root `render.yaml`. Review the service named `presscheck-api-akhilalladi` and deploy it on the **Free** plan.
5. Wait for the first deploy to finish. The API address should be `https://presscheck-api-akhilalladi.onrender.com`.
6. Open `https://presscheck-api-akhilalladi.onrender.com/api/health`; it should return JSON with `"status":"ok"` and `"engine":"python"`.

The Pages frontend is configured to use that API URL in `site/config.js`. If Render assigns a different hostname, update that file to the actual `onrender.com` URL and commit the change. The Pages workflow will redeploy automatically.

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

GitHub Actions runs the Python tests and validates/deploys the static frontend.

## Important disclaimer

PressCheck is an advisory tool, not a PDF/X validator or a substitute for your printer's approved prepress workflow. PDF page boxes do not prove that artwork visually extends through bleed. Color-space and output-intent compliance are not certified.

## License

MIT — Copyright (c) 2026 Akhil Alladi. See LICENSE.
