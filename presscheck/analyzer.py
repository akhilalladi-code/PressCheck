"""PDF inspection engine. Findings are advisory and never claim PDF/X certification."""
from __future__ import annotations
from pathlib import Path
from typing import Any
import fitz
from .profiles import PrintProfile, get_profile, PT_PER_MM

MAX_FILE_BYTES = 100 * 1024 * 1024

class PreflightError(ValueError):
    """Raised when an uploaded document cannot be inspected safely."""

def _mm(points: float) -> float:
    return points / PT_PER_MM

def analyze_pdf(source: str | Path | bytes, profile_id: str = "a4-flyer", min_dpi: int | None = None) -> dict[str, Any]:
    profile = get_profile(profile_id)
    if isinstance(source, bytes):
        if len(source) > MAX_FILE_BYTES:
            raise PreflightError("File exceeds the 100 MB inspection limit.")
        if not source.startswith(b"%PDF-"):
            raise PreflightError("The uploaded file does not have a valid PDF signature.")
        payload: Any = source
    else:
        path = Path(source)
        if not path.is_file():
            raise PreflightError("PDF file does not exist.")
        if path.stat().st_size > MAX_FILE_BYTES:
            raise PreflightError("File exceeds the 100 MB inspection limit.")
        payload = str(path)
    try:
        doc = fitz.open(stream=payload, filetype="pdf") if isinstance(payload, bytes) else fitz.open(payload)
        if doc.is_encrypted:
            raise PreflightError("This PDF is password-protected. Unlock it before inspection.")
        if doc.page_count == 0:
            raise PreflightError("The PDF contains no pages.")
        pages: list[dict[str, Any]] = []
        findings: list[dict[str, Any]] = []
        seen_fonts: dict[str, bool] = {}
        image_count = 0
        for index, page in enumerate(doc):
            number = index + 1
            media, trim, bleed_box = page.mediabox, page.trimbox, page.bleedbox
            width_mm, height_mm = _mm(trim.width), _mm(trim.height)
            rotated = page.rotation in (90, 270)
            expected_w, expected_h = (profile.height_mm, profile.width_mm) if rotated else (profile.width_mm, profile.height_mm)
            if abs(width_mm - expected_w) > profile.tolerance_mm or abs(height_mm - expected_h) > profile.tolerance_mm:
                findings.append(_finding("page-size", "error", f"Page {number}: trim size is {width_mm:.1f} × {height_mm:.1f} mm; expected {expected_w:g} × {expected_h:g} mm.", number, "Export using the selected trim size or choose the matching profile."))
            bleed_w = max(0.0, (bleed_box.width - trim.width) / 2 / PT_PER_MM)
            bleed_h = max(0.0, (bleed_box.height - trim.height) / 2 / PT_PER_MM)
            actual_bleed = min(bleed_w, bleed_h)
            if actual_bleed + 0.1 < profile.bleed_mm:
                findings.append(_finding("bleed", "warning", f"Page {number}: detected bleed is approximately {actual_bleed:.1f} mm; profile requires {profile.bleed_mm:g} mm.", number, "Extend artwork beyond the trim edge and export a BleedBox with the required bleed."))
            page_fonts = []
            for font in page.get_fonts(full=True):
                xref = int(font[0])
                name = str(font[3] or font[2] or "Unknown font")
                embedded = False
                if xref > 0:
                    try:
                        embedded = bool(doc.extract_font(xref)[3])
                    except Exception:
                        embedded = False
                seen_fonts[name] = seen_fonts.get(name, True) and embedded
                page_fonts.append({"name": name, "embedded": embedded})
                if not embedded:
                    findings.append(_finding("font-not-embedded", "warning", f"Page {number}: font '{name}' may not be embedded.", number, "Embed or outline the font before sending the PDF to print."))
            page_images = []
            for info in page.get_image_info(xrefs=True):
                image_count += 1
                width, height = int(info.get("width", 0)), int(info.get("height", 0))
                dpi = 0.0
                bbox = info.get("bbox")
                if bbox and width and height:
                    rect = fitz.Rect(bbox)
                    dpi_x = width * 72 / rect.width if rect.width else 0
                    dpi_y = height * 72 / rect.height if rect.height else 0
                    dpi = min(dpi_x, dpi_y)
                page_images.append({"width_px": width, "height_px": height, "effective_dpi": round(dpi) if dpi else None})
                threshold = min_dpi or profile.min_dpi
                if dpi and dpi < threshold:
                    findings.append(_finding("low-resolution-image", "warning", f"Page {number}: an image is approximately {dpi:.0f} DPI; minimum is {threshold} DPI.", number, "Replace it with a higher-resolution source or reduce its printed size."))
            pages.append({"page": number, "width_mm": round(width_mm, 2), "height_mm": round(height_mm, 2), "rotation": page.rotation, "media_box": _rect(media), "trim_box": _rect(trim), "bleed_box": _rect(bleed_box), "bleed_mm": round(actual_bleed, 2), "fonts": page_fonts, "images": page_images})
        metadata = doc.metadata or {}
        page_count = doc.page_count
        doc.close()
    except PreflightError:
        raise
    except Exception as exc:
        raise PreflightError(f"Could not read this PDF: {exc}") from exc
    if not any(f["code"] == "bleed" for f in findings):
        findings.append(_finding("bleed-present", "info", "The selected bleed requirement was detected on every page.", None, "Confirm that background artwork actually extends through the bleed area."))
    if not any(f["code"] == "font-not-embedded" for f in findings):
        findings.append(_finding("fonts-embedded", "info", "No unembedded fonts were detected.", None, "Check the printer's font requirements before release."))
    counts = {level: sum(1 for f in findings if f["severity"] == level) for level in ("error", "warning", "info")}
    return {"file_name": Path(source).name if not isinstance(source, bytes) else "uploaded.pdf", "profile": {"id": profile.id, "name": profile.name, "width_mm": profile.width_mm, "height_mm": profile.height_mm, "bleed_mm": profile.bleed_mm, "min_dpi": min_dpi or profile.min_dpi}, "summary": {"pages": page_count, "images": image_count, "fonts": len(seen_fonts), "errors": counts["error"], "warnings": counts["warning"], "info": counts["info"], "status": "needs-attention" if counts["error"] or counts["warning"] else "passed"}, "metadata": {"title": metadata.get("title") or "", "author": metadata.get("author") or "", "creator": metadata.get("creator") or "", "producer": metadata.get("producer") or ""}, "pages": pages, "findings": findings, "limitations": ["This is an advisory preflight, not PDF/X validation or a substitute for a printer's approved workflow.", "Color-space and output-intent compliance are not certified by this version.", "Bleed presence is inferred from PDF page boxes; visual artwork coverage must be reviewed separately."]}

def _rect(rect: fitz.Rect) -> dict[str, float]:
    return {"x0": round(rect.x0, 2), "y0": round(rect.y0, 2), "x1": round(rect.x1, 2), "y1": round(rect.y1, 2), "width": round(rect.width, 2), "height": round(rect.height, 2)}

def _finding(code: str, severity: str, message: str, page: int | None, recommendation: str) -> dict[str, Any]:
    return {"code": code, "severity": severity, "message": message, "page": page, "recommendation": recommendation}
