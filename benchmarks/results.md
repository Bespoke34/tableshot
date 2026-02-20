# TableShot Benchmarks

*Generated 2026-02-21. Averaged over 5 runs after 2 warmup runs. Windows 11, Python 3.11, pdfplumber 0.11.9.*

## Extraction Performance

| PDF | Type | Pages | Tables | Rows | Cols | Avg Time | Accuracy |
|-----|------|-------|--------|------|------|----------|----------|
| simple_bordered.pdf | Bordered product table | 1 | 1 | 5 | 4 | **10.5ms** | Exact |
| multi_table.pdf | 2 tables on 1 page | 1 | 2 | 7 | 3 | **10.2ms** | Exact |
| multi_page.pdf | Tables across 2 pages | 2 | 2 | 7 | 3 | **8.7ms** | Exact |
| single_row.pdf | Header + 1 data row | 1 | 1 | 2 | 2 | **3.9ms** | Exact |
| special_chars.pdf | Commas, quotes, HTML entities | 1 | 1 | 5 | 2 | **5.9ms** | Exact |
| wide_table.pdf | 8-column landscape table | 1 | 1 | 4 | 8 | **10.7ms** | Exact |
| empty_page.pdf | Text page + table page | 2 | 1 | 3 | 2 | **6.0ms** | Exact |
| blackrock_mock.pdf | Financial table (bordered) | 1 | 1 | 11 | 5 | **25.1ms** | Exact |
| **Sample-Financial-Statements-1.pdf** | **Real financial statements** | **3** | **3** | **75** | **6** | **181.5ms** | **Partial** |

**Summary:** 8/9 test PDFs extracted with exact accuracy. Average time: **4-25ms per table** for bordered PDFs. The real financial statement PDF is an honest edge case (see below).

## Output Format Validity

All 4 output formats (Markdown, CSV, JSON, HTML) produce valid output across every test PDF:

| PDF | Markdown | CSV | JSON | HTML |
|-----|----------|-----|------|------|
| simple_bordered.pdf | pass | pass | pass | pass |
| multi_table.pdf | pass | pass | pass | pass |
| multi_page.pdf | pass | pass | pass | pass |
| single_row.pdf | pass | pass | pass | pass |
| special_chars.pdf | pass | pass | pass | pass |
| wide_table.pdf | pass | pass | pass | pass |
| empty_page.pdf | pass | pass | pass | pass |
| blackrock_mock.pdf | pass | pass | pass | pass |
| Sample-Financial-Statements-1.pdf | pass | pass | pass | pass |

## Before/After: Raw Text vs TableShot

The core value proposition: what an LLM sees *without* TableShot vs *with* it.

### simple_bordered.pdf

**Raw text** (word soup):
```
Sales Report Q1 2024 Product Price Quantity Total Widget A $10.00 100 $1,000.00 Widget B $25.50 50 $1,275.00 Widget C $5.99 200 $1,198.00 Widget D $149.00 10 $1,490.00
```

**TableShot output** (clean structure):
```
| Product  | Price   | Quantity | Total     |
| -------- | ------- | -------- | --------- |
| Widget A | $10.00  | 100      | $1,000.00 |
| Widget B | $25.50  | 50       | $1,275.00 |
| Widget C | $5.99   | 200      | $1,198.00 |
| Widget D | $149.00 | 10       | $1,490.00 |
```

### wide_table.pdf (8 columns, landscape)

**Raw text:**
```
Wide Table ID Name Q1 Q2 Q3 Q4 Total Status 1 Alpha 100 150 200 250 700 Active 2 Beta 90 110 130 170 500 Active 3 Gamma 0 0 50 80 130 New
```

**TableShot output:**
```
| ID  | Name  | Q1  | Q2  | Q3  | Q4  | Total | Status |
| --- | ----- | --- | --- | --- | --- | ----- | ------ |
| 1   | Alpha | 100 | 150 | 200 | 250 | 700   | Active |
| 2   | Beta  | 90  | 110 | 130 | 170 | 500   | Active |
| 3   | Gamma | 0   | 0   | 50  | 80  | 130   | New    |
```

### blackrock_mock.pdf (financial data, bordered)

**Raw text:**
```
EXECUTIVE SUMMARY (in millions, except per share data) Q3 2023 Q3 2022 9M 2023 9M 2022 Total revenue $4,522 $4,311 $13,228 $13,536 Total expense 2,885 2,785 8,538 8,578 Operating income $1,637 $1,526 ...
```

**TableShot output:**
```
|                                      | Q3 2023    | Q3 2022    | 9M 2023    | 9M 2022    |
| ------------------------------------ | ---------- | ---------- | ---------- | ---------- |
| Total revenue                        | $4,522     | $4,311     | $13,228    | $13,536    |
| Total expense                        | 2,885      | 2,785      | 8,538      | 8,578      |
| Operating income                     | $1,637     | $1,526     | $4,690     | $4,958     |
| ...10 rows total                     |            |            |            |            |
```

### Sample-Financial-Statements-1.pdf (edge case -- real financial statement)

**Raw text:**
```
Sample Company Income Statement (Service) For the Year Ended September 30, 2021 Service revenue $2,750 Operating Expenses: Depreciation expense 100 Wages expenses 1,200 Supplies expenses 60 ...
```

**TableShot output:**
```
|     |                      | For   | the Year End | ed September 3  | 0, 202 |
| --- | -------------------- | ----- | ------------ | --------------- | ------ |
|     |                      |       |              |                 |        |
| S   | ervice revenue       |       |              | $               | 2,750  |
```

*Honest assessment:* The data is extracted but columns are fragmented. This PDF uses visual whitespace positioning rather than cell borders, which causes pdfplumber's line-based detection to split text across too many columns. The raw text extraction is actually more readable for this specific case. This is the core limitation of rule-based table extraction -- and it affects Camelot and Tabula equally (Adhikari & Agarwal 2024).

## Comparison with Other Tools

Data sourced from Adhikari & Agarwal (2024), "A Comparative Study of PDF Parsing Tools
Across Diverse Document Categories" ([arXiv:2410.09871](https://arxiv.org/abs/2410.09871)),
OpenNews 2024 tool review, and published GitHub metrics.

| | TableShot | Camelot | Tabula-py | Table Transformer |
|---|---|---|---|---|
| **Install size** | ~33MB | ~15MB + Ghostscript/opencv | ~5MB + Java (100-300MB) | 700MB-5GB (PyTorch) |
| **External deps** | None | Ghostscript or pdfium | Java Runtime (JRE 7+) | PyTorch + model weights |
| **Speed (bordered)** | ~10ms/table | Moderate (>20s worst case) | Variable (JVM startup) | 2-5s/page on CPU |
| **Bordered tables** | Excellent | Excellent (self-reported ~99%) | Good | Excellent |
| **Borderless tables** | Good (text fallback) | Poor | Better detection than Camelot | Best overall |
| **Financial statements** | Partial (visual formatting) | Partial | Partial | Good |
| **Scanned/image PDFs** | No (base) / Yes (`[ml]`) | No | No | Yes |
| **MCP integration** | Native (stdio) | None | None | None |
| **Output formats** | MD/CSV/JSON/HTML | CSV/JSON/HTML | CSV/TSV/JSON | Custom |
| **License** | MIT | MIT | MIT | MIT/BSD |
| **Maintained** | Active (2026) | Stale (~5 years) | Active | Active |

## Known Limitations

TableShot uses pdfplumber under the hood -- the same engine that OpenNews called "exceptional"
for table extraction in their 2024 comparison. But all rule-based tools share fundamental limits:

1. **Financial statements with visual formatting** -- Amounts positioned via whitespace
   rather than cell borders get fragmented across columns. The data is extracted but
   column alignment may not match the visual layout.
2. **Borderless tables with ambiguous alignment** -- Text-based fallback detection works
   for simple cases but can misalign columns when spacing is irregular.
3. **Scanned PDFs and images** -- No OCR in the base install. Requires `tableshot[ocr]`
   or `tableshot[ml]` extras.
4. **Scientific papers with equations** -- Inline math can break table boundary detection
   (affects all rule-based tools per Adhikari & Agarwal 2024).
5. **Multi-column page layouts** -- Tables spanning visual columns may be detected as
   separate fragments.

For these edge cases, `tableshot[ml]` (Table Transformer) provides better results at
the cost of a larger install (~700MB+) and slower processing (2-5s/page).
