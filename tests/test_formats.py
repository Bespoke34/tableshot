"""Parametrized tests: every fixture × every output format."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tableshot.pipeline import run_extraction

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# All fixtures that should have at least 1 extractable table
TABLE_FIXTURES = [
    "simple_bordered.pdf",
    "multi_table.pdf",
    "single_row.pdf",
    "multi_page.pdf",
    "special_chars.pdf",
    "wide_table.pdf",
]

ALL_FORMATS = ["markdown", "csv", "json", "html"]


@pytest.mark.parametrize("fixture", TABLE_FIXTURES)
@pytest.mark.parametrize("fmt", ALL_FORMATS)
def test_extraction_produces_output(fixture: str, fmt: str):
    """Every fixture should produce non-empty output in every format."""
    pdf_path = str(FIXTURES_DIR / fixture)
    result = run_extraction(pdf_path, pages="all", fmt=fmt)
    assert result.total_tables >= 1, f"No tables found in {fixture}"
    for table in result.tables:
        assert table.data, f"Empty output for {fixture} in {fmt} format"
        assert len(table.data) > 0


@pytest.mark.parametrize("fixture", TABLE_FIXTURES)
def test_markdown_has_pipes_and_separator(fixture: str):
    """Markdown output should always have pipe-delimited rows and a separator."""
    pdf_path = str(FIXTURES_DIR / fixture)
    result = run_extraction(pdf_path, pages="all", fmt="markdown")
    for table in result.tables:
        lines = table.data.strip().split("\n")
        assert len(lines) >= 2, "Markdown needs at least header + separator"
        assert all(line.startswith("|") for line in lines)
        assert "---" in lines[1]


@pytest.mark.parametrize("fixture", TABLE_FIXTURES)
def test_csv_row_count_matches(fixture: str):
    """CSV should have the same number of rows as the table data."""
    pdf_path = str(FIXTURES_DIR / fixture)
    result = run_extraction(pdf_path, pages="all", fmt="csv")
    for table in result.tables:
        csv_lines = [line for line in table.data.strip().split("\n") if line.strip()]
        assert len(csv_lines) == table.rows


@pytest.mark.parametrize("fixture", TABLE_FIXTURES)
def test_json_parses_valid(fixture: str):
    """JSON output should always be valid JSON."""
    pdf_path = str(FIXTURES_DIR / fixture)
    result = run_extraction(pdf_path, pages="all", fmt="json")
    for table in result.tables:
        records = json.loads(table.data)
        assert isinstance(records, list)


@pytest.mark.parametrize("fixture", TABLE_FIXTURES)
def test_html_has_table_tags(fixture: str):
    """HTML output should have proper table structure."""
    pdf_path = str(FIXTURES_DIR / fixture)
    result = run_extraction(pdf_path, pages="all", fmt="html")
    for table in result.tables:
        assert "<table>" in table.data
        assert "</table>" in table.data
        assert "<thead>" in table.data
        assert "<th>" in table.data
