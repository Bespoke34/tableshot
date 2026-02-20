"""Utility functions: page range parsing, text cleaning."""

from __future__ import annotations

import re
import unicodedata


def parse_page_range(pages: str, total_pages: int) -> list[int]:
    """Parse a page range string into a list of 0-indexed page numbers.

    Accepts:
        "all"   → all pages
        "1"     → [0]
        "1-3"   → [0, 1, 2]
        "1,3,5" → [0, 2, 4]
        "2-4,7" → [1, 2, 3, 6]

    Returns sorted, deduplicated list of 0-indexed page numbers.
    Raises ValueError for invalid input.
    """
    if not pages or pages.strip().lower() == "all":
        return list(range(total_pages))

    result: set[int] = set()
    for part in pages.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part and not part.startswith("-"):
            start_s, end_s = part.split("-", 1)
            start, end = int(start_s.strip()), int(end_s.strip())
            if start < 1 or end < 1:
                raise ValueError(f"Page numbers must be >= 1, got '{part}'")
            if start > end:
                raise ValueError(f"Invalid range: {start} > {end}")
            for p in range(start, end + 1):
                if p > total_pages:
                    raise ValueError(f"Page {p} out of range (document has {total_pages} pages)")
                result.add(p - 1)
        else:
            p = int(part)
            if p < 1:
                raise ValueError(f"Page numbers must be >= 1, got {p}")
            if p > total_pages:
                raise ValueError(f"Page {p} out of range (document has {total_pages} pages)")
            result.add(p - 1)

    return sorted(result)


# Unicode characters that should be replaced with ASCII equivalents
_UNICODE_REPLACEMENTS = {
    "\u2018": "'",   # left single quote
    "\u2019": "'",   # right single quote
    "\u201c": '"',   # left double quote
    "\u201d": '"',   # right double quote
    "\u2013": "-",   # en dash
    "\u2014": "-",   # em dash
    "\u2026": "...", # ellipsis
    "\u00a0": " ",   # non-breaking space
    "\u200b": "",    # zero-width space
    "\u200c": "",    # zero-width non-joiner
    "\u200d": "",    # zero-width joiner
    "\ufeff": "",    # BOM / zero-width no-break space
    "\u00ad": "",    # soft hyphen
}

_UNICODE_RE = re.compile("|".join(re.escape(k) for k in _UNICODE_REPLACEMENTS))


def clean_cell(value: str | None) -> str:
    """Clean a single cell value from pdfplumber output.

    - Converts None to empty string
    - Normalizes unicode (smart quotes, dashes, zero-width chars)
    - Collapses internal whitespace
    - Strips leading/trailing whitespace
    - Preserves number formatting ($1,234.56)
    """
    if value is None:
        return ""
    text = str(value)
    # Replace known unicode characters
    text = _UNICODE_RE.sub(lambda m: _UNICODE_REPLACEMENTS[m.group()], text)
    # Normalize remaining unicode to NFC form
    text = unicodedata.normalize("NFC", text)
    # Replace newlines within a cell with spaces
    text = text.replace("\n", " ").replace("\r", " ")
    # Collapse internal whitespace, strip edges
    return " ".join(text.split()).strip()


def pad_row(row: list[str], target_cols: int) -> list[str]:
    """Pad a row with empty strings to match target column count."""
    if len(row) >= target_cols:
        return row[:target_cols]
    return row + [""] * (target_cols - len(row))
