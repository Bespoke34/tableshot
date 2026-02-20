# TableShot v2 — Revised Build Specification

**"Extract tables from PDFs and images into clean, structured data — instantly."**

You give it a PDF, image, or screenshot. It gives you back a perfect Markdown table, CSV, or JSON.
No API keys. No cloud. No 2GB downloads. Just clean data.

---

## Consultant's Note: GoodNotes Reality Check

> **Hard truth: This project is weak signal for GoodNotes' ML roles, and making it lightweight makes it weaker.**

GoodNotes currently has three ML-related openings:

1. **Senior Machine Learning Researcher - Handwriting** (Europe Timezone / London only)
2. **AI Research Manager** (Asia/Europe)
3. **Engineering Manager – AI Transformation & Developer Experience** (Asia/Europe)

The Handwriting Researcher role — the one most aligned with "ML" — explicitly requires:
- Deep knowledge in **Handwriting Recognition, Handwriting Synthesis, Document Layout Analysis**
- **Research track record via publications and/or open-source contributions in Document AI**
- **Model optimization for on-device deployment**
- Python + PyTorch/TensorFlow/JAX proficiency
- C++, Rust or Swift is a plus

**TableShot (especially the lightweight version) demonstrates almost none of this.** A pdfplumber wrapper is integration engineering, not ML research. It doesn't involve training models, handwriting recognition, on-device optimization, or anything resembling a research contribution.

Even the ML-heavy version (Table Transformer) would be marginal — you'd be using Microsoft's pretrained models, not doing original research. GoodNotes wants someone who pushes boundaries, not someone who wraps existing tools.

**Geographic problem:** The Handwriting Researcher role is Europe timezone only. You're in Hong Kong. The AI Research Manager and EM roles are Asia-compatible, but those require management experience and research leadership — a different profile than "I built an OSS tool."

### What Would Actually Help for GoodNotes

If GoodNotes is a priority target, you'd want a **different or additional** project:

- **Option A:** Build a handwriting recognition demo using TrOCR or a fine-tuned model on IAM Handwriting Dataset. Ship it as a Hugging Face Space. This directly addresses their core technology and shows you can work with transformer-based recognition models.
- **Option B:** Contribute to an existing Document AI open-source project (Docling, DocTR, TrOCR) with a meaningful PR — especially around handwriting or on-device optimization. The JD literally says "open-source contributions in Document AI."
- **Option C:** Write a technical blog post comparing handwriting recognition approaches (TrOCR vs. CTC-based vs. attention-based) with benchmarks. This demonstrates the "research track record" they want without requiring a full paper.

### Where TableShot Actually Helps

TableShot is strong signal for:
- **Anthropic ecosystem roles** — You're building on their MCP protocol. This is direct portfolio evidence.
- **Developer tooling companies** (Ramp, Stripe, Vercel, etc.) — Shows you can ship OSS tools that developers use.
- **Any "AI-forward" role** that values building and shipping over pure research.
- **General credibility** — A published, starred OSS project is better than no project for any application.

### Recommendation

**Build TableShot anyway** — it's the highest-ROI project for your *overall* job search. But don't pretend it's a GoodNotes play. If GoodNotes matters to you, allocate 2-3 days separately for one of the options above. A Hugging Face Space with a handwriting recognition demo + TableShot on GitHub covers both angles.

---

## What Changed from v1

| Decision | v1 (Wrong) | v2 (Correct) | Why |
|----------|-----------|--------------|-----|
| Core engine | Table Transformer (PyTorch) | pdfplumber + pypdfium2 | Sub-50MB, instant install, no model downloads |
| PDF backend | PyMuPDF (AGPL-3.0) | pypdfium2 (Apache-2.0) + pdfplumber (MIT) | AGPL taints MIT license, blocks enterprise users |
| ML role | Primary path | Strictly optional extra | Users want instant results, not a 2GB download |
| Install experience | `uvx tableshot` (fiction with PyTorch) | `uvx tableshot` (actually works, <30MB) | First-run must be <30 seconds or users bounce |
| Positioning | "Table extraction" | "Structured data extraction from documents" | "Table extraction" caps ceiling at ~3,600 stars (Camelot) |
| Sprint length | 10 days | 7 days | Lighter scope, ship faster, iterate from feedback |
| Tool count | 4 tools | 2 tools (v1), 4 tools (v1.1) | Ship the minimum that works, add tools based on usage |
| Framing | "Does one thing" | "Does one thing, instantly" | Speed is the differentiator vs heavyweight alternatives |

---

## Architecture

```
User (via MCP client)
    │
    ▼
┌──────────────────────────────────────────┐
│  TableShot MCP Server                    │
│  (FastMCP / official mcp SDK)            │
│                                          │
│  Tools:                                  │
│   • extract_tables (primary)             │
│   • list_tables (scan)                   │
│                                          │
│  Pipeline:                               │
│   1. Input normalization                 │
│      (PDF pages → text/coords)           │
│   2. Table detection                     │
│      (pdfplumber heuristics OR           │
│       Table Transformer if [ml])         │
│   3. Cell extraction                     │
│      (coordinate-based text grab)        │
│   4. Output formatting                   │
│      (Markdown/CSV/JSON/HTML)            │
│                                          │
│  Dependencies (base):                    │
│   • pypdfium2 (~15MB, Apache-2.0)        │
│   • pdfplumber (~8MB, MIT)               │
│   • mcp SDK (~5MB, MIT)                  │
│   • Pillow (~5MB, MIT-like)              │
│   Total: ~33MB                           │
│                                          │
│  Optional [ml]:                          │
│   • torch + table-transformer            │
│   • For scanned/image-only tables        │
│   Total: +700MB-5GB                      │
│                                          │
│  Optional [ocr]:                         │
│   • doctr or OnnxTR                      │
│   • For scanned documents                │
│   Total: +200MB-1GB                      │
└──────────────────────────────────────────┘
```

### Why pdfplumber Is Enough for v1

pdfplumber already handles:
- **Native PDF tables** (90%+ of real-world use cases) — financial reports, invoices, academic papers, government forms, spreadsheet exports
- **Bordered tables** — detects lines/edges, groups into cells
- **Borderless tables** — uses text alignment heuristics (column detection via x-coordinate clustering)
- **Merged cells** — partial support via spanning detection
- **Multi-page tables** — extraction per page, user can concatenate

What pdfplumber CANNOT do (and ML extras solve):
- **Scanned PDFs** with no text layer (photos, old documents)
- **Images of tables** (screenshots, camera photos)
- **Complex borderless tables** where text alignment is ambiguous

This means the base install handles the use case that 90% of users actually have: "I have a PDF with a table, Claude can't read it properly, give me the data."

---

## Tech Stack

| Component | Choice | License | Size | Why |
|-----------|--------|---------|------|-----|
| MCP Framework | `mcp` SDK with FastMCP | MIT | ~5MB | Anthropic's official, spec-compliant |
| PDF parsing | pdfplumber | MIT | ~8MB | Best OSS table extraction for native PDFs |
| PDF rendering | pypdfium2 | Apache-2.0/BSD-3 | ~15MB | Google's PDFium engine, same as Chromium. Replaces PyMuPDF |
| Image processing | Pillow | MIT-like | ~5MB | Standard, already a pdfplumber dependency |
| Build system | hatchling | MIT | — | Standard for MCP ecosystem |
| Dev tooling | uv | MIT | — | Fast Python package manager |

### Optional Extras

| Extra | Adds | License | Size | Use Case |
|-------|------|---------|------|----------|
| `[ml]` | torch, transformers, table-transformer | MIT/BSD | 700MB-5GB | Scanned docs, image tables |
| `[ocr]` | OnnxTR (ONNX-based, avoids PyTorch) | Apache-2.0 | ~200MB | OCR for scanned text |
| `[all]` | Everything | Mixed | 1-6GB | Full capability |

**Key decision: OnnxTR over DocTR for OCR extra.** OnnxTR is a fork of DocTR that uses ONNX Runtime instead of PyTorch/TensorFlow. This means:
- OCR without pulling in PyTorch (~700MB savings)
- Faster cold start (ONNX Runtime is lighter)
- Still high quality (same DocTR models, just ONNX-exported)

### Dependency Strategy

```
tableshot              # Base: pdfplumber + pypdfium2 + MCP SDK (~33MB, instant)
tableshot[ml]          # + PyTorch + Table Transformer (scanned docs, image tables)
tableshot[ocr]         # + OnnxTR (OCR without PyTorch)
tableshot[all]         # Everything
```

---

## Project Structure

```
tableshot/
├── .github/
│   └── workflows/
│       ├── ci.yml              # Test on Python 3.10, 3.11, 3.12
│       └── publish.yml         # PyPI via trusted publishing on tag
├── src/tableshot/
│   ├── __init__.py             # Version, public API
│   ├── __main__.py             # python -m tableshot
│   ├── server.py               # MCP server + tool definitions
│   ├── pipeline.py             # Orchestrates extraction (routes to backend)
│   ├── backends/
│   │   ├── __init__.py
│   │   ├── pdfplumber_backend.py   # Default: pdfplumber table extraction
│   │   └── ml_backend.py          # Optional: Table Transformer detection
│   ├── input_handler.py        # PDF/image/URL normalization via pypdfium2
│   ├── formatter.py            # Output as Markdown, CSV, JSON, HTML
│   └── utils.py                # Page range parsing, text cleaning
├── tests/
│   ├── conftest.py
│   ├── test_pipeline.py
│   ├── test_formatter.py
│   ├── test_server.py          # MCP tool integration tests
│   └── fixtures/               # Sample PDFs
│       ├── simple_bordered.pdf
│       ├── borderless_table.pdf
│       ├── merged_cells.pdf
│       ├── financial_report.pdf
│       └── multi_page_table.pdf
├── pyproject.toml
├── README.md
├── LICENSE                     # MIT
└── CHANGELOG.md
```

**What's removed from v1:**
- `detector.py`, `structure.py`, `device.py`, `cache.py` — Not needed for base install
- `Dockerfile` — Premature for v1 (add if there's demand)
- `benchmarks/` directory — Do benchmarks, but put results in README, not a separate directory
- Reduced from 10 source files to 7

---

## MCP Tool Definitions

### v1.0: Ship with 2 tools

```python
@mcp.tool()
async def extract_tables(
    source: str,           # File path or URL
    pages: str = "all",    # "all", "1", "1-3", "1,3,5"
    format: str = "markdown",  # "markdown", "csv", "json", "html"
) -> str:
    """Extract all tables from a PDF into structured data.

    Returns tables as clean Markdown, CSV, JSON, or HTML.
    Automatically detects table boundaries — no coordinates needed.

    Examples:
    - extract_tables("/path/to/report.pdf")
    - extract_tables("/path/to/report.pdf", pages="1-3", format="csv")
    """
```

```python
@mcp.tool()
async def list_tables(
    source: str,
    pages: str = "all",
) -> str:
    """Quickly scan a document and list all detected tables with
    their page numbers, row/column counts, and a preview of headers.
    Use this before extract_tables to see what's available.
    """
```

**Why only 2 tools for v1:**
- `extract_tables` covers 95% of use cases
- `list_tables` lets the LLM be smart about which tables to extract
- `extract_table_to_file` and `describe_table` are nice-to-haves that add complexity without core value
- Ship 2, add more based on real user feedback

### v1.1: Add based on demand
- `extract_table_to_file` — Save to disk (CSV/JSON/XLSX)
- `describe_table` — Natural language description
- `extract_from_image` — Image-only input (requires [ml] extra)

### Output Schema

```json
{
  "source": "report.pdf",
  "tables": [
    {
      "page": 1,
      "table_index": 0,
      "rows": 5,
      "cols": 3,
      "headers": ["Product", "Price", "Stock"],
      "data": {
        "markdown": "| Product | Price | Stock |\n|---|---|---|\n| Widget A | $99 | In stock |",
        "csv": "Product,Price,Stock\nWidget A,$99,In stock",
        "json": [{"Product": "Widget A", "Price": "$99", "Stock": "In stock"}]
      }
    }
  ],
  "metadata": {
    "total_tables": 1,
    "pages_scanned": 1,
    "processing_time_ms": 85,
    "backend": "pdfplumber"
  }
}
```

**Note: processing_time_ms: 85.** That's not a typo. pdfplumber on a native PDF with a text layer is nearly instant. This is the speed differentiator — while Docling takes 5-30 seconds per page to run its ML pipeline, TableShot returns in under 100ms for native PDFs.

---

## Pipeline Implementation

### Step 1: Input Normalization (`input_handler.py`)

```python
import pypdfium2 as pdfium

def load_pdf(source: str, pages: str = "all") -> list[pdfium.PdfPage]:
    """
    Load PDF and resolve page ranges.
    Uses pypdfium2 (Apache-2.0) instead of PyMuPDF (AGPL).

    For URL sources: download to temp file first.
    """
```

- pypdfium2 handles PDF loading and page-level access
- pdfplumber handles the actual text/table extraction
- Page range parsing: "all", "1", "1-3", "1,3,5"
- URL support: download to tempfile, process, clean up

### Step 2: Table Detection + Extraction (`backends/pdfplumber_backend.py`)

```python
import pdfplumber

class PdfplumberBackend:
    """Default backend: extract tables using pdfplumber's built-in detection."""

    def extract(self, pdf_path: str, pages: list[int]) -> list[Table]:
        with pdfplumber.open(pdf_path) as pdf:
            tables = []
            for page_num in pages:
                page = pdf.pages[page_num]
                for table_data in page.extract_tables():
                    tables.append(Table(
                        page=page_num + 1,
                        data=table_data,
                        headers=table_data[0] if table_data else [],
                    ))
            return tables
```

**pdfplumber's table detection strategy:**
1. Finds explicit lines (borders) in the PDF
2. Groups lines into rectangular cells
3. For borderless tables: uses `text_strategy="lines_strict"` or falls back to text alignment
4. Configurable via `table_settings` dict — we expose sensible defaults

**Tuning for edge cases:**
```python
# Default settings optimized for common table types
TABLE_SETTINGS = {
    "vertical_strategy": "lines",      # Use explicit lines first
    "horizontal_strategy": "lines",
    "snap_tolerance": 3,               # Allow slight misalignment
    "join_tolerance": 3,
    "edge_min_length": 3,
    "min_words_vertical": 3,           # Minimum words for vertical text strategy
    "min_words_horizontal": 1,
}

# Fallback for borderless tables
BORDERLESS_SETTINGS = {
    "vertical_strategy": "text",
    "horizontal_strategy": "text",
    "snap_tolerance": 5,
    "join_tolerance": 5,
}
```

**Smart fallback logic:**
1. Try extraction with line-based detection (default)
2. If no tables found → retry with text-based detection (borderless)
3. If still no tables → report "no tables detected" (honest > hallucinated)

### Step 3: Output Formatting (`formatter.py`)

```python
def format_table(table: Table, format: str) -> str:
    """
    Formats:
    - "markdown": GitHub-flavored markdown table (default, best for LLM context)
    - "csv": RFC 4180 compliant CSV string
    - "json": Array of objects with headers as keys
    - "html": Clean HTML <table> (useful for rendering)
    """
```

Formatting details:
- **Markdown**: Aligned columns, proper escaping of pipes
- **CSV**: Proper quoting of commas, quotes, newlines within cells
- **JSON**: Array of objects `[{"col1": "val1", "col2": "val2"}, ...]`
- **HTML**: Clean `<table>` with `<thead>` and `<tbody>`
- Empty cells → empty string (not None, not "N/A")
- Leading/trailing whitespace stripped per cell
- Number formatting preserved ($1,234.56 stays as-is)

---

## Sprint Plan (7 days)

### Day 1 — Skeleton + First Working Demo

- [ ] Init repo: `src/tableshot/`, `pyproject.toml` (hatchling), MIT license
- [ ] Implement `server.py` with FastMCP, register `extract_tables` + `list_tables`
- [ ] Implement `input_handler.py` — PDF loading via pypdfium2/pdfplumber
- [ ] Implement `backends/pdfplumber_backend.py` — table extraction
- [ ] Implement `formatter.py` — Markdown + CSV output
- [ ] Get it running in Claude Desktop via stdio transport
- [ ] First 3 tests: load PDF, detect table, format output
- [ ] Git init, push to GitHub

**End of Day 1: Working demo in Claude Desktop.** You can hand it a PDF and get a markdown table back.

### Day 2 — Edge Cases + JSON/HTML Output

- [ ] Add JSON and HTML output formats
- [ ] Borderless table fallback (text-based detection)
- [ ] Page range parsing ("1-3", "1,3,5")
- [ ] URL download support (tempfile + cleanup)
- [ ] Handle: empty tables, single-row tables, tables with merged cells
- [ ] Handle: multi-page extraction
- [ ] Text cleaning: whitespace normalization, unicode cleanup
- [ ] Number formatting preservation
- [ ] 10+ tests covering edge cases

### Day 3 — Testing + Quality

- [ ] Target 80%+ coverage
- [ ] Test with real-world PDFs: financial reports, invoices, academic papers, government forms
- [ ] Parametrized tests for all output formats
- [ ] Error condition tests (bad files, missing pages, corrupt PDFs)
- [ ] GitHub Actions CI: Python 3.10, 3.11, 3.12
- [ ] Lint with ruff, type hints on public API

### Day 4 — Benchmarks + Comparison

- [ ] Create 10 test PDFs covering: simple bordered, complex bordered, borderless, merged cells, financial, academic, invoice, government, multi-page, mixed content
- [ ] Measure: extraction accuracy (cell-level), processing time
- [ ] Compare against: raw text extraction (baseline), Camelot, Tabula-py
- [ ] Document results in README with concrete numbers
- [ ] Record before/after screenshots (messy text vs clean table)

### Day 5 — README + Demo

- [ ] Write README: logo → badges → one-liner → before/after demo → install → config → tools → examples → benchmarks → architecture → contributing
- [ ] Record demo GIF: Claude Desktop extracting table from financial PDF
- [ ] Set up Hugging Face Space (Gradio app) for live browser demo
- [ ] Finalize `pyproject.toml` with all extras
- [ ] PyPI Trusted Publishing setup (OIDC)
- [ ] Tag v0.1.0, push, auto-publish to PyPI

### Day 6 — ML Extra (Optional Backend)

- [ ] Implement `backends/ml_backend.py` with Table Transformer
- [ ] Lazy model loading, device detection (GPU/MPS/CPU)
- [ ] Image file support (PNG, JPEG → direct to ML detector)
- [ ] Smart routing: check for text layer → pdfplumber, else → ML
- [ ] Tests for ML path (mark as `@pytest.mark.slow`)
- [ ] Document ML extra in README: when you need it, how to install

### Day 7 — Launch

- [ ] Submit to: mcp.so, Smithery.ai, Glama.ai, PulseMCP
- [ ] PR to `punkpeye/awesome-mcp-servers`
- [ ] Show HN post (Tuesday/Wednesday, 9-10 AM ET)
- [ ] Reddit: r/ClaudeAI, r/Python, r/LocalLLaMA
- [ ] X/Twitter thread with before/after screenshots + demo GIF
- [ ] Dev.to technical post
- [ ] Monitor issues, fix critical bugs, tag v0.1.1 if needed

---

## README Structure

```markdown
# 📊 TableShot

**Extract tables from PDFs into clean, structured data — instantly.**

[![PyPI](badge)](link) [![License: MIT](badge)](link) [![Tests](badge)](link) [![Python 3.10+](badge)](link) [![Downloads](badge)](link)

[Demo GIF: Claude Desktop extracting a financial table]

## The Problem

Ask any AI assistant to read a table from a PDF. You get this:

```
Product Price Stock Widget A $99 In stock Widget B $149 Out of stock
```

TableShot gives you this:

| Product | Price | Stock |
|---------|-------|-------|
| Widget A | $99 | In stock |
| Widget B | $149 | Out of stock |

## Quick Start

### Claude Desktop / Cursor / VS Code
{JSON config: "command": "uvx", "args": ["tableshot"]}

### pip
pip install tableshot

## How It Works

[Simple 3-step diagram: PDF → detect tables → structured output]

~33MB install. No model downloads. No API keys. Results in <100ms.

## Tools

| Tool | What it does |
|------|-------------|
| `extract_tables` | Extract all tables as Markdown, CSV, JSON, or HTML |
| `list_tables` | Quick scan — preview tables before extracting |

## Examples

[3 real before/after examples with different PDF types]

## Benchmarks

[Table: TableShot vs raw text vs Camelot vs Tabula-py]
[Metrics: accuracy, speed, install size]

## Need Scanned PDFs or Images?

pip install tableshot[ml]    # Adds Table Transformer for image-based tables
pip install tableshot[ocr]   # Adds OCR for scanned documents
pip install tableshot[all]   # Everything

## How It Works Under the Hood

[Architecture diagram + brief explanation]

## Contributing

[Standard contributing guide]
```

**Key README principles applied:**
- Before/after is the hero — shows the problem and solution in 5 seconds
- Install size and speed called out prominently (differentiator)
- ML extras positioned as upgrades, not requirements
- No unnecessary sections (no "motivation" essay, no "philosophy")
- Badges signal maturity
- Live demo link (Hugging Face Space) above the fold

---

## pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "tableshot"
version = "0.1.0"
description = "Extract tables from PDFs into clean, structured data — instantly."
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.10"
authors = [{ name = "Andrew", email = "..." }]
keywords = ["mcp", "table-extraction", "pdf", "document-ai", "structured-data"]
classifiers = [
    "Development Status :: 4 - Beta",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]

dependencies = [
    "mcp>=1.0",
    "pdfplumber>=0.10",
    "pypdfium2>=4.0",
    "Pillow>=10.0",
]

[project.optional-dependencies]
ml = [
    "torch>=2.0",
    "torchvision>=0.15",
    "transformers>=4.30",
    "timm>=0.9",
]
ocr = [
    "onnxtr[cpu]>=0.5",
]
all = [
    "tableshot[ml,ocr]",
]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=5.0",
    "ruff>=0.4",
]

[project.scripts]
tableshot = "tableshot.server:main"

[tool.hatch.build.targets.wheel]
packages = ["src/tableshot"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.ruff]
target-version = "py310"
line-length = 100
```

**License check — all base dependencies are MIT/Apache-2.0 clean:**
- mcp: MIT ✓
- pdfplumber: MIT ✓
- pypdfium2: Apache-2.0/BSD-3 ✓
- Pillow: MIT-like (HPND) ✓

No AGPL contamination. Safe for enterprise use.

---

## Risk Mitigation (Updated)

| Risk | v1 Impact | Mitigation |
|------|-----------|------------|
| pdfplumber struggles with borderless tables | Medium — some tables won't extract cleanly | Smart fallback (lines → text strategy). Document limitations honestly. ML extra for hard cases |
| "Just a pdfplumber wrapper" criticism | High — someone will say this on HN | Speed + MCP integration + output quality are the moat. pdfplumber alone doesn't give you an MCP server, clean formatting, smart fallback, or benchmarked reliability |
| pypdfium2 less battle-tested than PyMuPDF | Low — used by Docling, DocTR, well-maintained | Test thoroughly on diverse PDFs. pypdfium2 is Google's PDF engine (Chromium). It's fine |
| Competition appears (someone ships first) | Medium — barrier to entry is low | Ship fast (7 days). First-mover advantage in MCP directories matters |
| Users want image/scanned support in base | Medium — "why doesn't it work on my screenshot?" | Clear README: base = native PDFs, [ml] = images/scans. Position as a feature, not a limitation |
| Show HN doesn't take off | Medium — launch is a lottery | Multi-channel launch. Reddit, newsletters, MCP directories as backup |

---

## Positioning for Maximum Stars

### Name: "TableShot"
- 9 characters, memorable, suggests "snapshot of a table"
- PyPI: available (verify before starting)
- GitHub: available (verify before starting)
- Short enough for CLI usage: `uvx tableshot`

### One-liner options (test which resonates):
1. "Extract tables from PDFs into clean, structured data — instantly."
2. "An MCP server that turns PDF tables into Markdown, CSV, and JSON."
3. "PDF tables → structured data. No ML required. <100ms."

### Broader positioning (for README/social, not the package name):
- GitHub topics: `mcp`, `pdf`, `table-extraction`, `document-ai`, `structured-data`, `rag`
- Frame as: "structured data extraction" not just "table extraction"
- Show use cases beyond tables: financial data, research data, invoice data

### Competitive messaging:
- vs Docling: "TableShot is 33MB. Docling is 5GB+. If you just need tables, you don't need the full document processing suite."
- vs Camelot: "TableShot is an MCP server. Your AI assistant can use it directly. Camelot is a Python library you have to code against."
- vs raw text: "TableShot gives you structured data with column alignment. Raw text gives you word soup."

---

## Success Metrics

### Week 1 (Launch)
- [ ] Published on PyPI with `uvx tableshot` working under 30 seconds
- [ ] 50+ GitHub stars
- [ ] Listed on 3+ MCP directories
- [ ] Hugging Face Space demo live
- [ ] Clean CI passing, 80%+ test coverage

### Month 1
- [ ] 100+ GitHub stars
- [ ] 500+ PyPI weekly downloads
- [ ] At least 3 GitHub issues from real users (proves someone used it)
- [ ] At least 1 external mention (blog post, newsletter, tweet by non-you)

### Month 3 (job search metric)
- [ ] 200+ GitHub stars
- [ ] Referenced in 2+ job applications
- [ ] Demo'd in at least 1 interview

---

## The Interview Story

> "I noticed every AI assistant fails at reading tables from PDFs — it's the number one complaint in the RAG developer community. So I built TableShot, an open-source MCP server that extracts tables into clean Markdown, CSV, or JSON. It installs in under 30 seconds, runs in under 100 milliseconds, and requires zero model downloads. I shipped it in a week, it's on PyPI, and it has X stars on GitHub. The architecture decision I'm most proud of is keeping the base install under 33MB by using pdfplumber instead of ML models — it covers 90% of real-world tables. For the other 10%, there's an optional ML backend."

**Why this story is stronger than v1:**
- "Under 30 seconds" and "under 100 milliseconds" are concrete, impressive numbers
- "33MB" vs "2GB" shows you made a deliberate engineering tradeoff
- "90% / 10%" shows you understood the user need, not just the technology
- The architecture decision shows judgment, not just implementation skill
