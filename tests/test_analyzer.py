import fitz
import pytest
from presscheck.analyzer import analyze_pdf, PreflightError, MAX_FILE_BYTES

def pdf_bytes():
    doc = fitz.open()
    page = doc.new_page(width=210*72/25.4, height=297*72/25.4)
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
