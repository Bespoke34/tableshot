"""Input normalization: load PDF files (local or URL) for table extraction."""

from __future__ import annotations

import tempfile
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

import pdfplumber


def _is_url(source: str) -> bool:
    """Check if source looks like a URL."""
    try:
        parsed = urlparse(source)
        return parsed.scheme in ("http", "https")
    except Exception:
        return False


def _download_to_temp(url: str) -> Path:
    """Download a URL to a temporary PDF file.

    Returns the path to the temp file. Caller must delete it when done.
    """
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp_path = Path(tmp.name)
    tmp.close()  # Close before writing — required on Windows
    try:
        urllib.request.urlretrieve(url, str(tmp_path))
    except Exception as e:
        tmp_path.unlink(missing_ok=True)
        raise ValueError(f"Failed to download '{url}': {e}") from e
    return tmp_path


def load_pdf(source: str) -> tuple[pdfplumber.PDF, Path | None]:
    """Open a PDF from a local path or URL.

    Args:
        source: File path or HTTP(S) URL to a PDF.

    Returns:
        Tuple of (open pdfplumber.PDF, temp_path_or_None).
        If temp_path is not None, caller must delete it after closing the PDF.

    Raises:
        FileNotFoundError: If a local file does not exist.
        ValueError: If the file is not a PDF or URL download fails.
    """
    temp_path: Path | None = None

    if _is_url(source):
        temp_path = _download_to_temp(source)
        pdf_path = temp_path
    else:
        pdf_path = Path(source).resolve()
        if not pdf_path.exists():
            raise FileNotFoundError(f"File not found: {source}")
        if pdf_path.suffix.lower() != ".pdf":
            raise ValueError(f"Expected a PDF file, got: {pdf_path.suffix}")

    try:
        pdf = pdfplumber.open(str(pdf_path))
    except Exception:
        if temp_path:
            temp_path.unlink(missing_ok=True)
        raise

    return pdf, temp_path


def get_total_pages(pdf: pdfplumber.PDF) -> int:
    """Return the number of pages in an open PDF."""
    return len(pdf.pages)
