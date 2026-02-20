"""Default backend: table extraction using pdfplumber's built-in detection."""

from __future__ import annotations

from dataclasses import dataclass, field

import pdfplumber

from tableshot.utils import clean_cell, pad_row


@dataclass
class Table:
    """A single extracted table."""

    page: int  # 1-indexed page number
    table_index: int  # 0-indexed table on that page
    data: list[list[str]]  # cleaned rows (first row = headers)
    headers: list[str] = field(default_factory=list)

    @property
    def rows(self) -> int:
        return len(self.data)

    @property
    def cols(self) -> int:
        return len(self.data[0]) if self.data else 0


# Default settings optimized for bordered tables
TABLE_SETTINGS: dict = {
    "vertical_strategy": "lines",
    "horizontal_strategy": "lines",
    "snap_tolerance": 3,
    "join_tolerance": 3,
    "edge_min_length": 3,
    "min_words_vertical": 3,
    "min_words_horizontal": 1,
}

# Fallback for borderless tables
BORDERLESS_SETTINGS: dict = {
    "vertical_strategy": "text",
    "horizontal_strategy": "text",
    "snap_tolerance": 5,
    "join_tolerance": 5,
}


def _clean_table(raw_table: list[list[str | None]]) -> list[list[str]]:
    """Clean all cell values and normalize column counts (pad ragged rows)."""
    if not raw_table:
        return []
    # Determine max column count
    max_cols = max(len(row) for row in raw_table)
    return [pad_row([clean_cell(cell) for cell in row], max_cols) for row in raw_table]


def _extract_from_page(
    page: pdfplumber.page.Page,
    page_num: int,
) -> list[Table]:
    """Extract tables from a single page with smart fallback.

    1. Try line-based detection (bordered tables)
    2. If nothing found, retry with text-based detection (borderless)
    """
    tables: list[Table] = []

    # First pass: line-based (bordered)
    raw_tables = page.extract_tables(TABLE_SETTINGS)

    # Fallback: text-based (borderless)
    if not raw_tables:
        raw_tables = page.extract_tables(BORDERLESS_SETTINGS)

    for idx, raw_table in enumerate(raw_tables):
        if not raw_table or not any(any(cell for cell in row) for row in raw_table):
            continue  # skip empty tables

        cleaned = _clean_table(raw_table)

        # Skip tables that are only a header row with no data
        # (single-row tables are still kept — they may be intentional)
        if not cleaned:
            continue

        tables.append(Table(
            page=page_num,
            table_index=idx,
            data=cleaned,
            headers=cleaned[0] if cleaned else [],
        ))

    return tables


def extract_tables(pdf: pdfplumber.PDF, page_indices: list[int]) -> list[Table]:
    """Extract tables from specified pages of an open PDF.

    Args:
        pdf: An open pdfplumber.PDF.
        page_indices: 0-indexed page numbers to scan.

    Returns:
        List of Table objects found across the specified pages.
    """
    all_tables: list[Table] = []
    for page_idx in page_indices:
        page = pdf.pages[page_idx]
        page_tables = _extract_from_page(page, page_num=page_idx + 1)
        all_tables.extend(page_tables)
    return all_tables
