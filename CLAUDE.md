# TableShot

Read SPEC.md before doing anything. It contains the full build specification,
architecture decisions, tech stack, and sprint plan.

Key constraints:
- Base install must be <50MB (pdfplumber + pypdfium2 + mcp SDK only)
- MIT license — no AGPL dependencies (no PyMuPDF)
- Python 3.10+, hatchling build system
- 2 MCP tools for v1: extract_tables, list_tables
- All code in src/tableshot/