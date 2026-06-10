"""Stage 1 — Document loading.

Loads each source into memory in its rawest useful form. Cleaning happens
later (cleaning.py); these functions only read bytes off disk and, for the two
binary/structured formats (PDF, JSON), turn them into text/Python objects.

  .html -> raw HTML string        (tags stripped later)
  .pdf  -> extracted text string  (pdfplumber)
  .txt  -> raw string
  .json -> parsed Python object   (Reddit listing)
"""

import json
from pathlib import Path

import pdfplumber


def load_html(path: Path) -> str:
    return Path(path).read_text(encoding="utf-8", errors="ignore")


def load_txt(path: Path) -> str:
    return Path(path).read_text(encoding="utf-8", errors="ignore")


def load_pdf(path: Path) -> str:
    """Extract text page-by-page. pdfplumber does no OCR, but our parking PDF
    is digitally created, so every page yields text."""
    with pdfplumber.open(path) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    return "\n\n".join(pages)


def load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_raw(source: dict):
    """Dispatch on file extension. Returns a str for html/pdf/txt, or a parsed
    object for json."""
    ext = source["path"].suffix.lower()
    if ext == ".html":
        return load_html(source["path"])
    if ext == ".pdf":
        return load_pdf(source["path"])
    if ext == ".txt":
        return load_txt(source["path"])
    if ext == ".json":
        return load_json(source["path"])
    raise ValueError(f"Unsupported file type: {source['filename']}")