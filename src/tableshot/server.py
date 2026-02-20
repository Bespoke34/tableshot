"""TableShot MCP Server — extract tables from PDFs into structured data."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from tableshot.pipeline import run_extraction, run_list

mcp = FastMCP(
    "TableShot",
    instructions="Extract tables from PDFs into clean Markdown, CSV, JSON, or HTML.",
)


@mcp.tool()
async def extract_tables(
    source: str,
    pages: str = "all",
    format: str = "markdown",
) -> str:
    """Extract all tables from a PDF into structured data.

    Returns tables as clean Markdown, CSV, JSON, or HTML.
    Automatically detects table boundaries — no coordinates needed.

    Args:
        source: File path to a PDF document.
        pages: Which pages to scan. "all", "1", "1-3", or "1,3,5".
        format: Output format — "markdown", "csv", "json", or "html".

    Examples:
        extract_tables("/path/to/report.pdf")
        extract_tables("/path/to/report.pdf", pages="1-3", format="csv")
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
    source: str,
    pages: str = "all",
) -> str:
    """Quickly scan a document and list all detected tables.

    Shows page numbers, row/column counts, and a preview of headers.
    Use this before extract_tables to see what's available.

    Args:
        source: File path to a PDF document.
        pages: Which pages to scan. "all", "1", "1-3", or "1,3,5".
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
