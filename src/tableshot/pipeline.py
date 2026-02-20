"""Orchestrates the table extraction pipeline."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from tableshot.backends.pdfplumber_backend import extract_tables
from tableshot.formatter import format_table
from tableshot.input_handler import get_total_pages, load_pdf
from tableshot.utils import parse_page_range


@dataclass
class TableResult:
    """A single table with its formatted output."""

    page: int
    table_index: int
    rows: int
    cols: int
    headers: list[str]
    data: str  # formatted output


@dataclass
class ExtractionResult:
    """Complete result of a table extraction run."""

    source: str
    tables: list[TableResult]
    total_tables: int
    pages_scanned: int
    processing_time_ms: float
    backend: str = "pdfplumber"


def _source_label(source: str) -> str:
    """Human-readable label for the source (filename or URL)."""
    if source.startswith(("http://", "https://")):
        return source.split("/")[-1] or source
    return Path(source).name


def run_extraction(source: str, pages: str = "all", fmt: str = "markdown") -> ExtractionResult:
    """Run the full extraction pipeline.

    Args:
        source: Path to PDF file or HTTP(S) URL.
        pages: Page range string ("all", "1", "1-3", "1,3,5").
        fmt: Output format ("markdown", "csv", "json", "html").

    Returns:
        ExtractionResult with formatted tables.
    """
    start = time.perf_counter()

    pdf, temp_path = load_pdf(source)
    try:
        total_pages = get_total_pages(pdf)
        page_indices = parse_page_range(pages, total_pages)
        raw_tables = extract_tables(pdf, page_indices)
    finally:
        pdf.close()
        if temp_path:
            temp_path.unlink(missing_ok=True)

    results: list[TableResult] = []
    for table in raw_tables:
        formatted = format_table(table, fmt)
        results.append(TableResult(
            page=table.page,
            table_index=table.table_index,
            rows=table.rows,
            cols=table.cols,
            headers=table.headers,
            data=formatted,
        ))

    elapsed_ms = (time.perf_counter() - start) * 1000

    return ExtractionResult(
        source=_source_label(source),
        tables=results,
        total_tables=len(results),
        pages_scanned=len(page_indices),
        processing_time_ms=round(elapsed_ms, 1),
    )


@dataclass
class TableSummary:
    """Summary info for a single table (used by list_tables)."""

    page: int
    table_index: int
    rows: int
    cols: int
    headers: list[str]
    preview: list[str]  # first data row as preview


@dataclass
class ListResult:
    """Result of scanning for tables."""

    source: str
    tables: list[TableSummary]
    total_tables: int
    pages_scanned: int


def run_list(source: str, pages: str = "all") -> ListResult:
    """Scan a PDF and list all detected tables with metadata.

    Args:
        source: Path to PDF file or HTTP(S) URL.
        pages: Page range string.

    Returns:
        ListResult with table summaries.
    """
    pdf, temp_path = load_pdf(source)
    try:
        total_pages = get_total_pages(pdf)
        page_indices = parse_page_range(pages, total_pages)
        raw_tables = extract_tables(pdf, page_indices)
    finally:
        pdf.close()
        if temp_path:
            temp_path.unlink(missing_ok=True)

    summaries: list[TableSummary] = []
    for table in raw_tables:
        preview = table.data[1] if len(table.data) > 1 else []
        summaries.append(TableSummary(
            page=table.page,
            table_index=table.table_index,
            rows=table.rows,
            cols=table.cols,
            headers=table.headers,
            preview=preview,
        ))

    return ListResult(
        source=_source_label(source),
        tables=summaries,
        total_tables=len(summaries),
        pages_scanned=len(page_indices),
    )
