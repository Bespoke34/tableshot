"""Orchestrates the table extraction pipeline."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from tableshot.backends.pdfplumber_backend import extract_tables
from tableshot.formatter import format_table
from tableshot.input_handler import (
    get_total_pages,
    has_text_layer,
    is_image_source,
    load_image,
    load_pdf,
)
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


def _run_image_extraction(source: str, fmt: str) -> ExtractionResult:
    """Extract tables from an image source using the ML backend.

    Args:
        source: Path or URL to an image file.
        fmt: Output format.

    Returns:
        ExtractionResult with formatted tables.
    """
    from tableshot.backends.ml_backend import extract_tables_from_image

    start = time.perf_counter()

    image, temp_path = load_image(source)
    try:
        raw_tables = extract_tables_from_image(image, page_num=1)
    finally:
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
        pages_scanned=1,
        processing_time_ms=round(elapsed_ms, 1),
        backend="table-transformer",
    )


def _should_use_ml(pdf, page_indices: list[int]) -> bool:
    """Determine if the ML backend should be used for a PDF.

    Returns True if the majority of pages lack a text layer (scanned PDF).
    """
    if not page_indices:
        return False
    pages_without_text = sum(
        1 for idx in page_indices if not has_text_layer(pdf, idx)
    )
    return pages_without_text > len(page_indices) / 2


def run_extraction(
    source: str,
    pages: str = "all",
    fmt: str = "markdown",
    backend: str = "auto",
) -> ExtractionResult:
    """Run the full extraction pipeline.

    Args:
        source: Path to PDF/image file or HTTP(S) URL.
        pages: Page range string ("all", "1", "1-3", "1,3,5").
        fmt: Output format ("markdown", "csv", "json", "html").
        backend: Backend to use — "auto", "pdfplumber", or "ml".
            "auto" uses pdfplumber for PDFs with text layers,
            ML for scanned PDFs and images.

    Returns:
        ExtractionResult with formatted tables.
    """
    # Image files always use ML backend
    if is_image_source(source):
        return _run_image_extraction(source, fmt)

    start = time.perf_counter()

    pdf, temp_path = load_pdf(source)
    pdf_path = str(Path(source).resolve()) if not source.startswith(("http://", "https://")) else str(temp_path)
    try:
        total_pages = get_total_pages(pdf)
        page_indices = parse_page_range(pages, total_pages)

        # Determine backend
        use_ml = False
        if backend == "ml":
            use_ml = True
        elif backend == "auto":
            use_ml = _should_use_ml(pdf, page_indices)

        if use_ml:
            from tableshot.backends.ml_backend import extract_tables_ml_pdf
            raw_tables = extract_tables_ml_pdf(pdf_path, pdf, page_indices)
            backend_name = "table-transformer"
        else:
            raw_tables = extract_tables(pdf, page_indices)
            backend_name = "pdfplumber"
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
        backend=backend_name,
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
