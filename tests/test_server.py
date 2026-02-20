"""MCP server integration tests — call tool functions directly."""

from __future__ import annotations

from pathlib import Path

# Import the tool functions directly from server module
from tableshot.server import extract_tables, list_tables

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SIMPLE_PDF = str(FIXTURES_DIR / "simple_bordered.pdf")
MULTI_PDF = str(FIXTURES_DIR / "multi_table.pdf")
EMPTY_PAGE_PDF = str(FIXTURES_DIR / "empty_page.pdf")


class TestExtractTablesTool:
    async def test_basic_extraction(self):
        result = await extract_tables(source=SIMPLE_PDF)
        assert "Table 1" in result
        assert "|" in result

    async def test_csv_format(self):
        result = await extract_tables(source=SIMPLE_PDF, format="csv")
        assert "Table 1" in result
        assert "," in result

    async def test_json_format(self):
        result = await extract_tables(source=SIMPLE_PDF, format="json")
        assert "Table 1" in result
        assert "[" in result

    async def test_html_format(self):
        result = await extract_tables(source=SIMPLE_PDF, format="html")
        assert "<table>" in result

    async def test_page_selection(self):
        result = await extract_tables(source=MULTI_PDF, pages="1")
        assert "Table" in result

    async def test_file_not_found_returns_error(self):
        result = await extract_tables(source="/nonexistent/file.pdf")
        assert "Error" in result
        assert "not found" in result.lower()

    async def test_invalid_format_returns_error(self):
        result = await extract_tables(source=SIMPLE_PDF, format="xml")
        assert "Error" in result

    async def test_metadata_in_footer(self):
        result = await extract_tables(source=SIMPLE_PDF)
        assert "pdfplumber" in result
        assert "ms" in result
        assert "table(s) extracted" in result

    async def test_no_tables_message(self):
        result = await extract_tables(source=EMPTY_PAGE_PDF, pages="1")
        assert "No tables detected" in result


class TestListTablesTool:
    async def test_basic_list(self):
        result = await list_tables(source=SIMPLE_PDF)
        assert "Table 1" in result or "table" in result.lower()

    async def test_multi_table_list(self):
        result = await list_tables(source=MULTI_PDF)
        assert "2" in result

    async def test_list_file_not_found(self):
        result = await list_tables(source="/nonexistent/file.pdf")
        assert "Error" in result

    async def test_list_shows_headers(self):
        result = await list_tables(source=SIMPLE_PDF)
        assert "Headers" in result

    async def test_list_no_tables(self):
        result = await list_tables(source=EMPTY_PAGE_PDF, pages="1")
        assert "No tables detected" in result
