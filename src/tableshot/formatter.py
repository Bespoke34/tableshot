"""Output formatting: convert extracted tables to Markdown, CSV, JSON, HTML."""

from __future__ import annotations

import csv
import io
import json

from tableshot.backends.pdfplumber_backend import Table


def format_markdown(table: Table) -> str:
    """Format a table as a GitHub-flavored Markdown table."""
    if not table.data:
        return ""

    # Calculate column widths for alignment
    col_widths = [0] * table.cols
    for row in table.data:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(_escape_md(cell)))

    # Minimum width of 3 for separator
    col_widths = [max(w, 3) for w in col_widths]

    lines: list[str] = []

    # Header row
    header = table.data[0]
    header_cells = [_escape_md(cell).ljust(col_widths[i]) for i, cell in enumerate(header)]
    lines.append("| " + " | ".join(header_cells) + " |")

    # Separator
    sep_cells = ["-" * col_widths[i] for i in range(table.cols)]
    lines.append("| " + " | ".join(sep_cells) + " |")

    # Data rows
    for row in table.data[1:]:
        data_cells = [_escape_md(cell).ljust(col_widths[i]) for i, cell in enumerate(row)]
        lines.append("| " + " | ".join(data_cells) + " |")

    return "\n".join(lines)


def _escape_md(value: str) -> str:
    """Escape pipe characters in markdown cell values."""
    return value.replace("|", "\\|")


def format_csv(table: Table) -> str:
    """Format a table as RFC 4180 CSV."""
    if not table.data:
        return ""
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    for row in table.data:
        writer.writerow(row)
    return output.getvalue().rstrip("\n")


def format_json(table: Table) -> str:
    """Format a table as JSON array of objects (headers as keys)."""
    if not table.data or len(table.data) < 2:
        return "[]"

    headers = table.data[0]
    records = []
    for row in table.data[1:]:
        record = {}
        for i, header in enumerate(headers):
            key = header if header else f"col_{i}"
            record[key] = row[i] if i < len(row) else ""
        records.append(record)

    return json.dumps(records, indent=2, ensure_ascii=False)


def format_html(table: Table) -> str:
    """Format a table as clean HTML."""
    if not table.data:
        return ""

    lines: list[str] = ["<table>"]

    # Header
    if table.data:
        lines.append("  <thead>")
        lines.append("    <tr>")
        for cell in table.data[0]:
            lines.append(f"      <th>{_escape_html(cell)}</th>")
        lines.append("    </tr>")
        lines.append("  </thead>")

    # Body
    if len(table.data) > 1:
        lines.append("  <tbody>")
        for row in table.data[1:]:
            lines.append("    <tr>")
            for cell in row:
                lines.append(f"      <td>{_escape_html(cell)}</td>")
            lines.append("    </tr>")
        lines.append("  </tbody>")

    lines.append("</table>")
    return "\n".join(lines)


def _escape_html(value: str) -> str:
    """Escape HTML special characters."""
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


FORMATTERS = {
    "markdown": format_markdown,
    "csv": format_csv,
    "json": format_json,
    "html": format_html,
}


def format_table(table: Table, fmt: str) -> str:
    """Format a table in the requested format.

    Args:
        table: Extracted Table object.
        fmt: One of "markdown", "csv", "json", "html".

    Returns:
        Formatted string.

    Raises:
        ValueError: If format is not recognized.
    """
    formatter = FORMATTERS.get(fmt)
    if formatter is None:
        raise ValueError(f"Unknown format '{fmt}'. Choose from: {', '.join(FORMATTERS)}")
    return formatter(table)
