"""Input normalization: load PDF files and images (local or URL) for table extraction."""

from __future__ import annotations

import tempfile
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

import pdfplumber

from tableshot.backends.ml_backend import IMAGE_EXTENSIONS


def _is_url(source: str) -> bool:
    """Check if source looks like a URL."""
    try:
        parsed = urlparse(source)
        return parsed.scheme in ("http", "https")
    except Exception:
        return False


def is_image_source(source: str) -> bool:
    """Check if source points to an image file (by extension)."""
    if _is_url(source):
        path_part = urlparse(source).path
        return Path(path_part).suffix.lower() in IMAGE_EXTENSIONS
    return Path(source).suffix.lower() in IMAGE_EXTENSIONS


def _download_to_temp(url: str) -> Path:
    """Download a URL to a temporary file.

    Returns the path to the temp file. Caller must delete it when done.
    """
    # Preserve original extension for type detection
    parsed_path = urlparse(url).path
    suffix = Path(parsed_path).suffix or ".pdf"
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp_path = Path(tmp.name)
    tmp.close()  # Close before writing — required on Windows
    try:
        urllib.request.urlretrieve(url, str(tmp_path))
    except Exception as e:
        tmp_path.unlink(missing_ok=True)
        raise ValueError(f"Failed to download '{url}': {e}") from e
    return tmp_path


def load_image(source: str):
    """Load an image from a local path or URL.

    Args:
        source: File path or HTTP(S) URL to an image.

    Returns:
        Tuple of (PIL Image, temp_path_or_None).

    Raises:
        FileNotFoundError: If a local file does not exist.
        ValueError: If file can't be opened as an image.
    """
    from PIL import Image

    temp_path: Path | None = None

    if _is_url(source):
        temp_path = _download_to_temp(source)
        img_path = temp_path
    else:
        img_path = Path(source).resolve()
        if not img_path.exists():
            raise FileNotFoundError(f"File not found: {source}")

    try:
        image = Image.open(str(img_path)).convert("RGB")
    except Exception as e:
        if temp_path:
            temp_path.unlink(missing_ok=True)
        raise ValueError(f"Failed to open image '{source}': {e}") from e

    return image, temp_path


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


def has_text_layer(pdf: pdfplumber.PDF, page_idx: int) -> bool:
    """Check if a PDF page has an extractable text layer.

    Returns True if the page has meaningful text content,
    False if it's likely a scanned image with no text layer.
    """
    page = pdf.pages[page_idx]
    text = page.extract_text() or ""
    # A page with a text layer typically has at least a few words
    return len(text.strip()) > 20
