"""Command-line entry point for batch PDF preflight."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from .analyzer import analyze_pdf, PreflightError
from .profiles import PROFILES

def main() -> None:
    parser = argparse.ArgumentParser(prog="presscheck", description="Inspect PDFs for common print-production risks.")
    parser.add_argument("paths", nargs="+", help="PDF file(s) or directories to scan")
    parser.add_argument("--profile", choices=PROFILES, default="a4-flyer")
    parser.add_argument("--min-dpi", type=int)
    parser.add_argument("--json", dest="json_path", help="Write a machine-readable report to this path")
    parser.add_argument("--fail-on-warning", action="store_true", help="Return exit code 1 when warnings are found")
    args = parser.parse_args()
    files: list[Path] = []
    for item in args.paths:
        path = Path(item)
        if path.is_dir():
            files.extend(sorted(path.rglob("*.pdf")))
        elif path.is_file():
            files.append(path)
        else:
            print(f"Not found: {path}", file=sys.stderr)
    if not files:
        parser.error("No PDF files found.")
    reports, failed = [], False
    for path in files:
        try:
            report = analyze_pdf(path, args.profile, args.min_dpi)
            reports.append(report)
            summary = report["summary"]
            print(f"{path}: {summary['status']} · {summary['pages']} pages · {summary['errors']} errors · {summary['warnings']} warnings")
            failed |= bool(summary["errors"] or (args.fail_on_warning and summary["warnings"]))
        except PreflightError as exc:
            print(f"{path}: ERROR · {exc}", file=sys.stderr)
            failed = True
    if args.json_path:
        Path(args.json_path).write_text(json.dumps({"reports": reports}, indent=2), encoding="utf-8")
    raise SystemExit(1 if failed else 0)

if __name__ == "__main__":
    main()
