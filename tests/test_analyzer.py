import fitz
import pytest

from presscheck.analyzer import MAX_FILE_BYTES, PreflightError, analyze_pdf


def pdf_bytes():
    doc = fitz.open()
    page = doc.new_page(width=210 * 72 / 25.4, height=297 * 72 / 25.4)
    page.insert_text((50, 50), "PressCheck test page")
    data = doc.tobytes()
    doc.close()
    return data


def test_analyze_valid_a4_pdf():
    report = analyze_pdf(pdf_bytes(), "a4-flyer")
    assert report["summary"]["pages"] == 1
    assert report["summary"]["errors"] == 0
    assert report["pages"][0]["width_mm"] == pytest.approx(210, abs=.1)


def test_reject_non_pdf_signature():
    with pytest.raises(PreflightError, match="valid PDF signature"):
        analyze_pdf(b"not a pdf")


def test_reject_oversized_upload():
    with pytest.raises(PreflightError, match="100 MB"):
        analyze_pdf(b"%PDF-" + b"x" * MAX_FILE_BYTES)


def test_unknown_profile_rejected():
    with pytest.raises(ValueError, match="Unknown profile"):
        analyze_pdf(pdf_bytes(), "unknown")


def test_report_includes_limitations_and_page_boxes():
    report = analyze_pdf(pdf_bytes(), "a4-flyer")
    assert report["pages"][0]["trim_box"]["width"] > 0
    assert report["limitations"]


def test_low_resolution_image_is_flagged():
    doc = fitz.open()
    page = doc.new_page(width=210 * 72 / 25.4, height=297 * 72 / 25.4)
    pixmap = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 100, 100), False)
    pixmap.clear_with(120)
    page.insert_image(fitz.Rect(40, 40, 184, 184), stream=pixmap.tobytes("png"))
    report = analyze_pdf(doc.tobytes(), "a4-flyer")
    doc.close()
    assert report["pages"][0]["images"][0]["effective_dpi"] == 50
    assert any(f["code"] == "low-resolution-image" for f in report["findings"])


def test_wrong_trim_size_is_an_error():
    doc = fitz.open()
    doc.new_page(width=595.28, height=841.89)
    report = analyze_pdf(doc.tobytes(), "a3-poster")
    doc.close()
    assert report["summary"]["errors"] == 1
    assert report["findings"][0]["code"] == "page-size"
