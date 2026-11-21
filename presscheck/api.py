"""FastAPI interface for PressCheck's hosted and local editions."""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .analyzer import MAX_FILE_BYTES, analyze_pdf
from .profiles import PROFILES

app = FastAPI(title="PressCheck", version="1.1.0", docs_url=None, redoc_url=None)
STATIC = Path(__file__).parent / "static"

_allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "PRESSCHECK_ALLOWED_ORIGINS",
        "http://127.0.0.1:8765,http://localhost:8765",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
    max_age=600,
)


@app.middleware("http")
async def prevent_api_caching(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "PressCheck", "engine": "python"}


@app.get("/api/profiles")
def profiles():
    return [
        {
            "id": p.id,
            "name": p.name,
            "width_mm": p.width_mm,
            "height_mm": p.height_mm,
            "bleed_mm": p.bleed_mm,
            "min_dpi": p.min_dpi,
        }
        for p in PROFILES.values()
    ]


@app.post("/api/preflight")
async def preflight(
    file: UploadFile = File(...),
    profile: str = Form("a4-flyer"),
    min_dpi: int | None = Form(None),
):
    if not file.filename or Path(file.filename).suffix.lower() != ".pdf":
        await file.close()
        raise HTTPException(415, "Upload a PDF file.")
    if min_dpi is not None and not 72 <= min_dpi <= 1200:
        await file.close()
        raise HTTPException(422, "Minimum DPI must be between 72 and 1200.")

    try:
        data = await file.read(MAX_FILE_BYTES + 1)
        if len(data) > MAX_FILE_BYTES:
            limit_mb = MAX_FILE_BYTES // (1024 * 1024)
            raise HTTPException(413, f"File exceeds the {limit_mb} MB upload limit.")
        try:
            report = analyze_pdf(data, profile, min_dpi)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        report["file_name"] = Path(file.filename).name
        return report
    finally:
        await file.close()


@app.get("/{path:path}")
def web(path: str):
    candidate = (STATIC / path).resolve()
    if candidate.is_file() and STATIC.resolve() in candidate.parents:
        return FileResponse(candidate)
    return FileResponse(STATIC / "index.html")
