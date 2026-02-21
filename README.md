# TableShot

**Extract tables from PDFs into clean, structured data -- instantly.**

[![PyPI](https://img.shields.io/pypi/v/tableshot)](https://pypi.org/project/tableshot/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/github/actions/workflow/status/Bespoke34/tableshot/ci.yml?label=tests)](https://github.com/Bespoke34/tableshot/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://pypi.org/project/tableshot/)

An MCP server that gives your AI assistant the ability to read PDF tables properly.
~33MB install. No model downloads. No API keys. Results in <100ms.

<!-- TODO: Replace with actual demo GIF -->
<!-- ![Demo](assets/demo.gif) -->

## The Problem

Ask any AI assistant to read a table from a PDF. You get this:

```
Sales Report Q1 2024 Product Price Quantity Total Widget A $10.00 100
$1,000.00 Widget B $25.50 50 $1,275.00 Widget C $5.99 200 $1,198.00
```

TableShot gives you this:

| Product  | Price   | Quantity | Total     |
|----------|---------|----------|-----------|
| Widget A | $10.00  | 100      | $1,000.00 |
| Widget B | $25.50  | 50       | $1,275.00 |
| Widget C | $5.99   | 200      | $1,198.00 |
| Widget D | $149.00 | 10       | $1,490.00 |

## Quick Start

### Claude Desktop / Cursor / Windsurf

Add to your MCP config:

```json
{
  "mcpServers": {
    "tableshot": {
      "command": "uvx",
      "args": ["tableshot"]
    }
  }
}
```

Then just ask: *"Extract the tables from /path/to/report.pdf"*

### pip

```bash
pip install tableshot
```

Run as a standalone MCP server:

```bash
tableshot              # stdio transport (for MCP clients)
python -m tableshot    # same thing
```

## Tools

| Tool | What it does |
|------|-------------|
| `extract_tables` | Extract all tables as Markdown, CSV, JSON, or HTML |
| `list_tables` | Quick scan -- preview tables before extracting |

### `extract_tables`

```
source: str           # File path or URL to a PDF (or image with [ml] extra)
pages: str = "all"    # "all", "1", "1-3", "1,3,5"
format: str = "markdown"  # "markdown", "csv", "json", "html"
```

### `list_tables`

```
source: str           # File path or URL to a PDF
pages: str = "all"    # "all", "1", "1-3", "1,3,5"
```

Returns table count, dimensions, headers, and a preview row for each table found.

## Examples

### Financial report (bordered table)

**Input:** BlackRock-style quarterly earnings PDF

**Output (markdown):**
```
|                                      | Q3 2023    | Q3 2022    | 9M 2023    | 9M 2022    |
| ------------------------------------ | ---------- | ---------- | ---------- | ---------- |
| Total revenue                        | $4,522     | $4,311     | $13,228    | $13,536    |
| Total expense                        | 2,885      | 2,785      | 8,538      | 8,578      |
| Operating income                     | $1,637     | $1,526     | $4,690     | $4,958     |
| Operating margin                     | 36.2%      | 35.4%      | 35.5%      | 36.6%      |
```

Extracted in **25ms**.

### Multi-table document

**Input:** PDF with employee directory + budget summary on the same page

**Output:** Both tables extracted separately with correct headers:
```
Table 1: 3 rows x 3 cols (Name, Department, Email)
Table 2: 4 rows x 2 cols (Category, Amount)
```

### Wide table (8 columns, landscape)

```
| ID  | Name  | Q1  | Q2  | Q3  | Q4  | Total | Status |
| --- | ----- | --- | --- | --- | --- | ----- | ------ |
| 1   | Alpha | 100 | 150 | 200 | 250 | 700   | Active |
| 2   | Beta  | 90  | 110 | 130 | 170 | 500   | Active |
| 3   | Gamma | 0   | 0   | 50  | 80  | 130   | New    |
```

All 4 output formats (Markdown, CSV, JSON, HTML) available for every extraction.

## Benchmarks

Tested on 10 PDFs covering bordered tables, multi-table pages, multi-page documents,
special characters, wide tables, and real financial statements.

| Metric | Result |
|--------|--------|
| **Bordered table accuracy** | 8/8 exact match |
| **Speed (bordered tables)** | 4-25ms per extraction |
| **Speed (3-page financial PDF)** | 182ms |
| **Output format validity** | 36/36 pass (9 PDFs x 4 formats) |

### Test Data

Generated fixtures — click **Source** to see the input PDF, **Output** to see what TableShot extracts:

| Fixture | Description | Source | Output | Speed |
|---------|-------------|--------|--------|-------|
| simple_bordered | 4-column sales report (Product, Price, Quantity, Total) | [PDF](tests/fixtures/simple_bordered.pdf) | [Extracted](benchmarks/outputs/simple_bordered.md) | 10ms |
| multi_table | Two tables on one page: employee directory + budget summary | [PDF](tests/fixtures/multi_table.pdf) | [Extracted](benchmarks/outputs/multi_table.md) | 10ms |
| single_row | Minimal table — header + one data row | [PDF](tests/fixtures/single_row.pdf) | [Extracted](benchmarks/outputs/single_row.md) | 4ms |
| multi_page | One table per page across 2 pages | [PDF](tests/fixtures/multi_page.pdf) | [Extracted](benchmarks/outputs/multi_page.md) | 9ms |
| empty_page | Page 1 text only; page 2 has a table | [PDF](tests/fixtures/empty_page.pdf) | [Extracted](benchmarks/outputs/empty_page.md) | 6ms |
| special_chars | Cells with `$`, `:`, `"`, `&`, `<>` | [PDF](tests/fixtures/special_chars.pdf) | [Extracted](benchmarks/outputs/special_chars.md) | 6ms |
| wide_table | 8-column landscape table (Q1–Q4, Total, Status) | [PDF](tests/fixtures/wide_table.pdf) | [Extracted](benchmarks/outputs/wide_table.md) | 11ms |

Real-world PDFs (not included in repo due to size/licensing):

| PDF | Description | Tables | Speed |
|-----|-------------|--------|-------|
| BlackRock mock | Generated mock of a BlackRock quarterly earnings statement (5 columns) | 1 table, 11 rows | 25ms |
| Sample Financial Statements | 3-page financial statement with complex visual formatting (155KB) | 3 tables, 75 rows | 182ms |
| NHM table | Large 56-page document with 55 tables (25MB) | 55 tables, 2321 rows | 5.8s |

Full machine-readable results in [benchmarks/results.json](benchmarks/results.json). Detailed before/after comparisons in [benchmarks/results.md](benchmarks/results.md).

### vs Other Tools

| | TableShot | Camelot | Tabula-py | Table Transformer |
|---|---|---|---|---|
| **Install** | ~33MB, nothing else | Needs Ghostscript | Needs Java (100-300MB) | Needs PyTorch (700MB-5GB) |
| **Speed** | ~10ms/table | >20s worst case | Variable (JVM startup) | 2-5s/page |
| **Bordered tables** | Excellent | Excellent | Good | Excellent |
| **Borderless** | Good (text fallback) | Poor | Better detection | Best |
| **MCP support** | Native | None | None | None |
| **Maintained** | Active | ~5 years stale | Active | Active |

*Competitor data from [Adhikari & Agarwal 2024](https://arxiv.org/abs/2410.09871), OpenNews 2024 review, and published GitHub metrics. Full results in [benchmarks/results.md](benchmarks/results.md).*

## Need Scanned PDFs or Images?

The base install handles native PDFs with text layers (90%+ of real-world use cases).
For scanned documents and images:

```bash
pip install tableshot[ml]     # Table Transformer for image-based tables
pip install tableshot[ocr]    # OCR for scanned documents (ONNX, no PyTorch)
pip install tableshot[all]    # Everything
```

With `[ml]` installed, TableShot automatically detects whether a PDF has a text layer:
- **Text layer present** -- uses pdfplumber (fast, ~10ms)
- **Scanned / no text layer** -- uses Table Transformer for detection, pdfplumber for text extraction
- **Image files** (PNG, JPEG) -- uses Table Transformer + OCR (requires `[ocr]`)

You can also force the ML backend: `extract_tables("/path/to/scan.pdf", backend="ml")`

## How It Works

```
PDF/Image ──> Smart Router ──> Table Detection ──> Cell Extraction ──> Formatted Output
                  |                                                        |
                  |  PDF with text layer:                                  |  Markdown
                  |    pdfplumber (lines → text fallback)                  |  CSV
                  |                                                        |  JSON
                  |  Scanned PDF / Image (with [ml]):                      |  HTML
                  |    Table Transformer → pdfplumber text / OCR           |
```

- **pdfplumber** handles PDF parsing and table detection (MIT)
- **pypdfium2** renders PDF pages to images for ML backend (Apache-2.0)
- **Table Transformer** (optional `[ml]`) detects tables in images (MIT)
- **MCP SDK** exposes tools to AI assistants via stdio transport (MIT)

Total base install: ~33MB. No model downloads. No GPU required.

## Known Limitations

All rule-based PDF table extractors (including Camelot and Tabula) share these limits:

- **Financial statements with visual formatting** -- amounts positioned by whitespace rather than cell borders can fragment across columns
- **Scanned PDFs / images** -- no OCR in base install (use `tableshot[ml]` or `tableshot[ocr]`)
- **Scientific papers with equations** -- inline math breaks table boundary detection
- **Complex borderless tables** -- ambiguous column alignment can cause misdetection

We're honest about these. For edge cases, `tableshot[ml]` adds Table Transformer support.

## Contributing

```bash
git clone https://github.com/Bespoke34/tableshot.git
cd tableshot
pip install -e ".[dev]"
pip install fpdf2                 # for generating test fixtures
python tests/generate_fixtures.py # create test PDFs
pytest -m "not slow"              # run 160 tests (skip ML tests)
pytest                            # run all 167 tests (needs [ml] extra)
ruff check src/ tests/            # lint
```

- 95% test coverage, all tests must pass
- Ruff clean, no lint warnings
- MIT license -- all dependencies must be MIT/Apache-2.0/BSD compatible

## License

MIT
