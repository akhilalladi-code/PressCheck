"""Smoke-test the deployed PressCheck API from CI without storing a PDF."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid

import pymupdf as fitz

DEFAULT_API_BASE = "https://presscheck-api-akhilalladi-tamq.onrender.com"
API_BASE = os.getenv("PRESSCHECK_API_BASE_URL", DEFAULT_API_BASE).rstrip("/")
RETRIES = 10


def get_json(path: str, *, origin: str | None = None) -> tuple[dict | list, object]:
    headers = {"Accept": "application/json"}
    if origin:
        headers["Origin"] = origin
    request = urllib.request.Request(API_BASE + path, headers=headers)
    with urllib.request.urlopen(request, timeout=12) as response:
        payload = json.loads(response.read().decode("utf-8"))
        return payload, response.headers


def wait_for_health() -> None:
    last_error: Exception | None = None
    for attempt in range(1, RETRIES + 1):
        try:
            health, headers = get_json("/api/health", origin="https://akhilalladi-code.github.io")
            if health.get("status") != "ok" or health.get("engine") != "python":
                raise RuntimeError(f"Unexpected health response: {health!r}")
            allowed_origin = headers.get("access-control-allow-origin")
            if allowed_origin != "https://akhilalladi-code.github.io":
                raise RuntimeError(f"Unexpected CORS allow-origin header: {allowed_origin!r}")
            print(f"API health and CORS passed on attempt {attempt}.")
            return
        except Exception as exc:  # noqa: BLE001 - report network/HTTP failures and retry
            last_error = exc
            print(f"API not ready (attempt {attempt}/{RETRIES}): {exc}", flush=True)
            if attempt < RETRIES:
                time.sleep(10)
    raise RuntimeError(f"PressCheck API did not become healthy: {last_error}")


def make_sample_pdf() -> bytes:
    document = fitz.open()
    document.new_page(width=210 * 72 / 25.4, height=297 * 72 / 25.4)
    document.set_metadata({"title": "PressCheck CI smoke test", "author": "PressCheck CI"})
    data = document.tobytes()
    document.close()
    return data


def upload_sample_pdf() -> dict:
    boundary = "----PressCheckSmoke" + uuid.uuid4().hex
    pdf = make_sample_pdf()
    parts = [
        (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="file"; filename="presscheck-smoke.pdf"\r\n'
            "Content-Type: application/pdf\r\n\r\n"
        ).encode("utf-8"),
        pdf,
        (
            f"\r\n--{boundary}\r\n"
            'Content-Disposition: form-data; name="profile"\r\n\r\n'
            "a4-flyer"
            f"\r\n--{boundary}\r\n"
            'Content-Disposition: form-data; name="min_dpi"\r\n\r\n'
            "300"
            f"\r\n--{boundary}--\r\n"
        ).encode("utf-8"),
    ]
    body = b"".join(parts)
    request = urllib.request.Request(
        API_BASE + "/api/preflight",
        data=body,
        headers={
            "Accept": "application/json",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Origin": "https://akhilalladi-code.github.io",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            report = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"PDF preflight returned HTTP {exc.code}: {detail}") from exc

    summary = report.get("summary", {})
    if report.get("file_name") != "presscheck-smoke.pdf":
        raise RuntimeError("API response did not preserve the uploaded filename.")
    if report.get("profile", {}).get("id") != "a4-flyer":
        raise RuntimeError("API response did not use the requested A4 flyer profile.")
    if summary.get("pages") != 1 or len(report.get("pages", [])) != 1:
        raise RuntimeError(f"Expected one analyzed page, got summary={summary!r}.")
    if not isinstance(report.get("findings"), list):
        raise RuntimeError("API response is missing the findings list.")
    print(
        "PDF upload and analysis passed: "
        f"{summary.get('pages')} page, {summary.get('errors')} errors, "
        f"{summary.get('warnings')} warnings."
    )
    return report


def main() -> int:
    print(f"Checking deployed PressCheck API: {API_BASE}")
    try:
        wait_for_health()
        profiles, _ = get_json("/api/profiles")
        if not isinstance(profiles, list) or len(profiles) != 4:
            raise RuntimeError(f"Expected four print profiles, received {profiles!r}.")
        print("Print profiles endpoint passed (4 profiles).")
        upload_sample_pdf()
    except Exception as exc:  # noqa: BLE001 - concise CI failure
        print(f"Backend smoke test failed: {exc}", file=sys.stderr)
        return 1
    print("PressCheck deployed API smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
