"""TableShot MCP Server — extract tables from PDFs into structured data."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field
from mcp.server.fastmcp import FastMCP

from tableshot.pipeline import run_extraction, run_list

mcp = FastMCP(
    "TableShot",
    instructions=(
        "TableShot extracts tables from PDF documents into clean, structured data. "
        "Use when the user needs to read, parse, or extract tabular data from any PDF "
        "— financial reports, invoices, research papers, bank statements, regulatory "
        "filings, spreadsheets saved as PDF, or any document with rows and columns. "
        "Outputs Markdown, CSV, JSON, or HTML. No API keys or configuration required."
    ),
)


@mcp.tool()
async def extract_tables(
    source: Annotated[str, Field(
        description="Absolute file path to a PDF document (e.g. '/home/user/report.pdf')."
    )],
    pages: Annotated[str, Field(
        default="all",
        description='Pages to scan. "all" for every page, "1" for a single page, "1-3" for a range, or "1,3,5" for specific pages.',
    )],
    format: Annotated[Literal["markdown", "csv", "json", "html"], Field(
        default="markdown",
        description="Output format for the extracted tables.",
    )] = "markdown",
) -> str:
    """Extract tables from a PDF and return them as structured data.

    Use when the user asks to read, parse, pull, or extract a table from a PDF.
    Detects table boundaries automatically — no coordinates or configuration needed.
    Preserves row/column structure, headers, and cell alignment.

    Returns formatted tables with page number, dimensions, and processing time.
    Returns a message if no tables are found.
    """
    try:
        result = run_extraction(source, pages=pages, fmt=format)
    except (FileNotFoundError, ValueError) as e:
        return f"Error: {e}"

    if result.total_tables == 0:
        return f"No tables detected in {result.source} (scanned {result.pages_scanned} page(s))."

    parts: list[str] = []
    for t in result.tables:
        header = f"## Table {t.table_index + 1} (Page {t.page}, {t.rows}×{t.cols})"
        parts.append(f"{header}\n\n{t.data}")

    footer = (
        f"\n\n---\n"
        f"*{result.total_tables} table(s) extracted from {result.source} "
        f"({result.pages_scanned} page(s), {result.processing_time_ms}ms, "
        f"backend: {result.backend})*"
    )
    parts.append(footer)

    return "\n\n".join(parts)


@mcp.tool()
async def list_tables(
    source: Annotated[str, Field(
        description="Absolute file path to a PDF document (e.g. '/home/user/report.pdf')."
    )],
    pages: Annotated[str, Field(
        default="all",
        description='Pages to scan. "all" for every page, "1" for a single page, "1-3" for a range, or "1,3,5" for specific pages.',
    )],
) -> str:
    """Scan a PDF and list all detected tables without extracting full content.

    Use before extract_tables to preview what tables exist in a document.
    Returns page number, row/column count, column headers, and a first-row preview for each table.
    """
    try:
        result = run_list(source, pages=pages)
    except (FileNotFoundError, ValueError) as e:
        return f"Error: {e}"

    if result.total_tables == 0:
        return f"No tables detected in {result.source} (scanned {result.pages_scanned} page(s))."

    lines: list[str] = [
        f"Found **{result.total_tables}** table(s) in {result.source}:\n"
    ]

    for t in result.tables:
        headers_str = ", ".join(t.headers) if t.headers else "(no headers detected)"
        preview_str = " | ".join(t.preview) if t.preview else ""
        lines.append(
            f"- **Table {t.table_index + 1}** on page {t.page}: "
            f"{t.rows} rows × {t.cols} cols\n"
            f"  Headers: {headers_str}"
        )
        if preview_str:
            lines.append(f"  Preview: {preview_str}")

    return "\n".join(lines)


def main():
    """Entry point for `tableshot` CLI and `python -m tableshot`."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
