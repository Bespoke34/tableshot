"""Tests for the table extraction pipeline."""

from __future__ import annotations

from pathlib import Path

import pytest

from tableshot.backends.pdfplumber_backend import Table
from tableshot.formatter import format_csv, format_html, format_json, format_markdown
from tableshot.pipeline import run_extraction, run_list
from tableshot.utils import clean_cell, pad_row, parse_page_range

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SIMPLE_PDF = str(FIXTURES_DIR / "simple_bordered.pdf")
MULTI_PDF = str(FIXTURES_DIR / "multi_table.pdf")
SINGLE_ROW_PDF = str(FIXTURES_DIR / "single_row.pdf")
MULTI_PAGE_PDF = str(FIXTURES_DIR / "multi_page.pdf")
EMPTY_PAGE_PDF = str(FIXTURES_DIR / "empty_page.pdf")
SPECIAL_CHARS_PDF = str(FIXTURES_DIR / "special_chars.pdf")
WIDE_TABLE_PDF = str(FIXTURES_DIR / "wide_table.pdf")


# ── parse_page_range ──────────────────────────────────────────────


class TestParsePageRange:
    def test_all(self):
        assert parse_page_range("all", 5) == [0, 1, 2, 3, 4]

    def test_empty_string(self):
        assert parse_page_range("", 3) == [0, 1, 2]

    def test_single_page(self):
        assert parse_page_range("2", 5) == [1]

    def test_range(self):
        assert parse_page_range("1-3", 5) == [0, 1, 2]

    def test_comma_separated(self):
        assert parse_page_range("1,3,5", 5) == [0, 2, 4]

    def test_mixed(self):
        assert parse_page_range("1-2,4", 5) == [0, 1, 3]

    def test_deduplication(self):
        assert parse_page_range("1,1,2,1-2", 5) == [0, 1]

    def test_whitespace(self):
        assert parse_page_range(" 1 , 3 ", 5) == [0, 2]

    def test_out_of_range(self):
        with pytest.raises(ValueError, match="out of range"):
            parse_page_range("10", 5)

    def test_invalid_range(self):
        with pytest.raises(ValueError, match="3 > 1"):
            parse_page_range("3-1", 5)

    def test_zero_page(self):
        with pytest.raises(ValueError, match=">= 1"):
            parse_page_range("0", 5)

    def test_negative_page(self):
        with pytest.raises(ValueError, match=">= 1"):
            parse_page_range("-1", 5)


# ── clean_cell ────────────────────────────────────────────────────


class TestCleanCell:
    def test_none(self):
        assert clean_cell(None) == ""

    def test_whitespace(self):
        assert clean_cell("  hello   world  ") == "hello world"

    def test_newlines(self):
        assert clean_cell("line1\nline2\rline3") == "line1 line2 line3"

    def test_smart_quotes(self):
        assert clean_cell("\u201cquoted\u201d") == '"quoted"'

    def test_en_dash(self):
        assert clean_cell("2020\u20132024") == "2020-2024"

    def test_non_breaking_space(self):
        assert clean_cell("hello\u00a0world") == "hello world"

    def test_zero_width_chars(self):
        assert clean_cell("he\u200bllo") == "hello"

    def test_number_preserved(self):
        assert clean_cell("$1,234.56") == "$1,234.56"

    def test_empty_string(self):
        assert clean_cell("") == ""


# ── pad_row ───────────────────────────────────────────────────────


class TestPadRow:
    def test_short_row(self):
        assert pad_row(["a", "b"], 4) == ["a", "b", "", ""]

    def test_exact_row(self):
        assert pad_row(["a", "b", "c"], 3) == ["a", "b", "c"]

    def test_long_row_truncated(self):
        assert pad_row(["a", "b", "c", "d"], 2) == ["a", "b"]


# ── extraction: simple bordered ───────────────────────────────────


class TestSimpleExtraction:
    def test_detects_table(self):
        result = run_extraction(SIMPLE_PDF, pages="1", fmt="markdown")
        assert result.total_tables >= 1
        assert result.tables[0].rows >= 2
        assert result.tables[0].cols >= 2

    def test_markdown_output(self):
        result = run_extraction(SIMPLE_PDF, pages="1", fmt="markdown")
        md = result.tables[0].data
        assert "|" in md
        assert "---" in md

    def test_csv_output(self):
        result = run_extraction(SIMPLE_PDF, pages="1", fmt="csv")
        csv_data = result.tables[0].data
        assert "," in csv_data

    def test_json_output(self):
        result = run_extraction(SIMPLE_PDF, pages="1", fmt="json")
        json_data = result.tables[0].data
        assert json_data.startswith("[")
        import json
        records = json.loads(json_data)
        assert isinstance(records, list)
        assert len(records) >= 1

    def test_html_output(self):
        result = run_extraction(SIMPLE_PDF, pages="1", fmt="html")
        html_data = result.tables[0].data
        assert "<table>" in html_data
        assert "<thead>" in html_data
        assert "<tbody>" in html_data
        assert "</table>" in html_data

    def test_processing_time(self):
        result = run_extraction(SIMPLE_PDF)
        assert result.processing_time_ms < 5000  # sanity check

    def test_backend_label(self):
        result = run_extraction(SIMPLE_PDF)
        assert result.backend == "pdfplumber"


# ── extraction: multi-table ───────────────────────────────────────


class TestMultiTable:
    def test_detects_two_tables(self):
        result = run_extraction(MULTI_PDF, pages="1", fmt="markdown")
        assert result.total_tables >= 2

    def test_different_column_counts(self):
        result = run_extraction(MULTI_PDF, pages="1", fmt="markdown")
        cols = [t.cols for t in result.tables]
        assert len(set(cols)) >= 2  # tables have different column counts


# ── extraction: single row ────────────────────────────────────────


class TestSingleRow:
    def test_single_row_table(self):
        result = run_extraction(SINGLE_ROW_PDF, pages="1", fmt="markdown")
        assert result.total_tables >= 1
        table = result.tables[0]
        assert table.rows == 2  # header + 1 data row

    def test_single_row_json(self):
        result = run_extraction(SINGLE_ROW_PDF, pages="1", fmt="json")
        import json
        records = json.loads(result.tables[0].data)
        assert len(records) == 1


# ── extraction: multi-page ────────────────────────────────────────


class TestMultiPage:
    def test_all_pages(self):
        result = run_extraction(MULTI_PAGE_PDF, pages="all", fmt="markdown")
        assert result.total_tables >= 2
        assert result.pages_scanned == 2

    def test_single_page_of_multi(self):
        result = run_extraction(MULTI_PAGE_PDF, pages="1", fmt="markdown")
        assert result.pages_scanned == 1
        assert result.total_tables >= 1

    def test_page_range(self):
        result = run_extraction(MULTI_PAGE_PDF, pages="1-2", fmt="markdown")
        assert result.pages_scanned == 2
        assert result.total_tables >= 2

    def test_tables_have_correct_page_numbers(self):
        result = run_extraction(MULTI_PAGE_PDF, pages="all", fmt="markdown")
        pages_seen = {t.page for t in result.tables}
        assert 1 in pages_seen
        assert 2 in pages_seen


# ── extraction: empty page ────────────────────────────────────────


class TestEmptyPage:
    def test_empty_page_returns_no_tables(self):
        result = run_extraction(EMPTY_PAGE_PDF, pages="1", fmt="markdown")
        assert result.total_tables == 0

    def test_table_on_second_page(self):
        result = run_extraction(EMPTY_PAGE_PDF, pages="2", fmt="markdown")
        assert result.total_tables >= 1

    def test_all_pages_finds_table(self):
        result = run_extraction(EMPTY_PAGE_PDF, pages="all", fmt="markdown")
        assert result.total_tables >= 1


# ── extraction: special characters ────────────────────────────────


class TestSpecialChars:
    def test_csv_handles_commas(self):
        result = run_extraction(SPECIAL_CHARS_PDF, pages="1", fmt="csv")
        csv_data = result.tables[0].data
        # CSV should properly quote fields containing commas
        assert "$1,234.56" in csv_data or '"$1,234.56"' in csv_data

    def test_html_escapes_entities(self):
        result = run_extraction(SPECIAL_CHARS_PDF, pages="1", fmt="html")
        html_data = result.tables[0].data
        # & should be escaped
        assert "&amp;" in html_data
        # < should be escaped
        assert "&lt;" in html_data


# ── extraction: wide table ────────────────────────────────────────


class TestWideTable:
    def test_many_columns(self):
        result = run_extraction(WIDE_TABLE_PDF, pages="1", fmt="markdown")
        assert result.total_tables >= 1
        assert result.tables[0].cols >= 6


# ── list_tables ───────────────────────────────────────────────────


class TestListTables:
    def test_simple(self):
        result = run_list(SIMPLE_PDF, pages="1")
        assert result.total_tables >= 1
        t = result.tables[0]
        assert t.rows >= 2
        assert t.cols >= 2
        assert len(t.headers) >= 2

    def test_preview(self):
        result = run_list(SIMPLE_PDF, pages="1")
        t = result.tables[0]
        assert len(t.preview) >= 1  # first data row

    def test_multi_table_list(self):
        result = run_list(MULTI_PDF, pages="1")
        assert result.total_tables >= 2


# ── error conditions ──────────────────────────────────────────────


class TestErrors:
    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            run_extraction("/nonexistent/file.pdf")

    def test_not_a_pdf(self):
        with pytest.raises(ValueError, match="Expected a PDF"):
            run_extraction(__file__)  # this .py file

    def test_invalid_format(self):
        with pytest.raises(ValueError, match="Unknown format"):
            run_extraction(SIMPLE_PDF, fmt="xml")

    def test_page_out_of_range(self):
        with pytest.raises(ValueError, match="out of range"):
            run_extraction(SIMPLE_PDF, pages="999")


# ── formatter unit tests ─────────────────────────────────────────


class TestFormatter:
    @pytest.fixture
    def sample_table(self):
        return Table(
            page=1,
            table_index=0,
            data=[["Name", "Age", "City"], ["Alice", "30", "NYC"], ["Bob", "25", "LA"]],
            headers=["Name", "Age", "City"],
        )

    def test_markdown(self, sample_table):
        md = format_markdown(sample_table)
        assert "| Name" in md
        assert "| Alice" in md
        assert "---" in md
        lines = md.split("\n")
        assert len(lines) == 4  # header + sep + 2 data rows

    def test_csv(self, sample_table):
        out = format_csv(sample_table)
        assert "Name,Age,City" in out
        assert "Alice,30,NYC" in out

    def test_json(self, sample_table):
        out = format_json(sample_table)
        import json
        records = json.loads(out)
        assert len(records) == 2
        assert records[0]["Name"] == "Alice"
        assert records[1]["City"] == "LA"

    def test_html(self, sample_table):
        out = format_html(sample_table)
        assert "<table>" in out
        assert "<th>Name</th>" in out
        assert "<td>Alice</td>" in out

    def test_empty_table(self):
        table = Table(page=1, table_index=0, data=[], headers=[])
        assert format_markdown(table) == ""
        assert format_csv(table) == ""
        assert format_json(table) == "[]"
        assert format_html(table) == ""

    def test_header_only_json(self):
        table = Table(page=1, table_index=0, data=[["A", "B"]], headers=["A", "B"])
        assert format_json(table) == "[]"  # no data rows

    def test_markdown_escapes_pipes(self):
        table = Table(
            page=1, table_index=0,
            data=[["Col", "Val"], ["a|b", "c"]],
            headers=["Col", "Val"],
        )
        md = format_markdown(table)
        assert "a\\|b" in md

    def test_html_escapes_entities(self):
        table = Table(
            page=1, table_index=0,
            data=[["Col"], ["<script>alert('xss')</script>"]],
            headers=["Col"],
        )
        html = format_html(table)
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_csv_quotes_commas(self):
        table = Table(
            page=1, table_index=0,
            data=[["Name", "Value"], ["test", "$1,000"]],
            headers=["Name", "Value"],
        )
        out = format_csv(table)
        assert '"$1,000"' in out

    def test_json_empty_header_fallback(self):
        table = Table(
            page=1, table_index=0,
            data=[["", "B"], ["x", "y"]],
            headers=["", "B"],
        )
        import json
        records = json.loads(format_json(table))
        assert "col_0" in records[0]  # empty header gets col_N name
