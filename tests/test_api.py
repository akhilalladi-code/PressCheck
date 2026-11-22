import pymupdf as fitz
from fastapi.testclient import TestClient
from presscheck.api import app

client = TestClient(app)

def make_pdf():
    doc = fitz.open()
    doc.new_page(width=595.28, height=841.89)
    data = doc.tobytes()
    doc.close()
    return data

def test_health_and_profiles():
    assert client.get("/api/health").json()["status"] == "ok"
    assert len(client.get("/api/profiles").json()) == 4

def test_preflight_upload_success():
    response = client.post("/api/preflight", files={"file": ("sample.pdf", make_pdf(), "application/pdf")}, data={"profile": "a4-flyer", "min_dpi": "300"})
    assert response.status_code == 200
    assert response.json()["summary"]["pages"] == 1

def test_preflight_rejects_non_pdf_extension():
    response = client.post("/api/preflight", files={"file": ("sample.txt", b"hello", "text/plain")})
    assert response.status_code == 415
