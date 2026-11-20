"""Local-only HTTP interface for the PressCheck web UI."""
from pathlib import Path
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from .analyzer import analyze_pdf, PreflightError, MAX_FILE_BYTES
from .profiles import PROFILES

app = FastAPI(title="PressCheck", version="1.0.0", docs_url=None, redoc_url=None)
STATIC = Path(__file__).parent / "static"

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "PressCheck"}

@app.get("/api/profiles")
def profiles():
    return [{"id": p.id, "name": p.name, "width_mm": p.width_mm, "height_mm": p.height_mm, "bleed_mm": p.bleed_mm, "min_dpi": p.min_dpi} for p in PROFILES.values()]

@app.post("/api/preflight")
async def preflight(file: UploadFile = File(...), profile: str = Form("a4-flyer"), min_dpi: int | None = Form(None)):
    if not file.filename or Path(file.filename).suffix.lower() != ".pdf":
        raise HTTPException(415, "Upload a PDF file.")
    if min_dpi is not None and not 72 <= min_dpi <= 1200:
        raise HTTPException(422, "Minimum DPI must be between 72 and 1200.")
    data = await file.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise HTTPException(413, "File exceeds the 100 MB limit.")
    try:
        report = analyze_pdf(data, profile, min_dpi)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    report["file_name"] = Path(file.filename).name
    return report

@app.get("/{path:path}")
def web(path: str):
    candidate = (STATIC / path).resolve()
    if candidate.is_file() and STATIC.resolve() in candidate.parents:
        return FileResponse(candidate)
    return FileResponse(STATIC / "index.html")
