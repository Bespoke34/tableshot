"""Generate test PDF fixtures.

Run: python tests/generate_fixtures.py
"""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF, XPos, YPos

FIXTURES_DIR = Path(__file__).parent / "fixtures"
FIXTURES_DIR.mkdir(exist_ok=True)


def _new_pdf() -> FPDF:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    return pdf


def _bordered_table(pdf: FPDF, headers: list[str], rows: list[list[str]],
                    col_widths: list[int], row_height: int = 8):
    """Helper to draw a bordered table."""
    pdf.set_font("Helvetica", "B", 10)
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], row_height, h, border=1)
    pdf.ln()
    pdf.set_font("Helvetica", size=10)
    for row in rows:
        for i, cell in enumerate(row):
            pdf.cell(col_widths[i], row_height, cell, border=1)
        pdf.ln()


def generate_simple_bordered():
    """Simple 4-column bordered table."""
    pdf = _new_pdf()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 10, "Sales Report Q1 2024", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(10)

    _bordered_table(pdf,
        headers=["Product", "Price", "Quantity", "Total"],
        rows=[
            ["Widget A", "$10.00", "100", "$1,000.00"],
            ["Widget B", "$25.50", "50", "$1,275.00"],
            ["Widget C", "$5.99", "200", "$1,198.00"],
            ["Widget D", "$149.00", "10", "$1,490.00"],
        ],
        col_widths=[45, 35, 35, 40],
        row_height=10,
    )

    pdf.output(str(FIXTURES_DIR / "simple_bordered.pdf"))
    print("Generated: simple_bordered.pdf")


def generate_multi_table():
    """Two tables on one page."""
    pdf = _new_pdf()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 10, "Employee Directory", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)

    _bordered_table(pdf,
        headers=["Name", "Department", "Email"],
        rows=[
            ["Alice Smith", "Engineering", "alice@example.com"],
            ["Bob Jones", "Marketing", "bob@example.com"],
        ],
        col_widths=[50, 45, 65],
    )

    pdf.ln(20)
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 10, "Budget Summary", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)

    _bordered_table(pdf,
        headers=["Category", "Amount"],
        rows=[
            ["Salaries", "$500,000"],
            ["Equipment", "$50,000"],
            ["Travel", "$25,000"],
        ],
        col_widths=[60, 50],
    )

    pdf.output(str(FIXTURES_DIR / "multi_table.pdf"))
    print("Generated: multi_table.pdf")


def generate_single_row():
    """Table with only a header row and one data row."""
    pdf = _new_pdf()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 10, "Single Row Table", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)

    _bordered_table(pdf,
        headers=["Key", "Value"],
        rows=[["version", "1.0.0"]],
        col_widths=[60, 60],
    )

    pdf.output(str(FIXTURES_DIR / "single_row.pdf"))
    print("Generated: single_row.pdf")


def generate_multi_page():
    """Table spanning multiple pages (one table per page)."""
    pdf = _new_pdf()

    # Page 1
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 10, "Page 1 - Inventory", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    _bordered_table(pdf,
        headers=["Item", "Count"],
        rows=[["Apples", "50"], ["Bananas", "30"], ["Cherries", "100"]],
        col_widths=[60, 40],
    )

    # Page 2
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 10, "Page 2 - Pricing", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    _bordered_table(pdf,
        headers=["Item", "Unit Price", "Currency"],
        rows=[["Apples", "1.50", "USD"], ["Bananas", "0.75", "USD"]],
        col_widths=[50, 40, 40],
    )

    pdf.output(str(FIXTURES_DIR / "multi_page.pdf"))
    print("Generated: multi_page.pdf")


def generate_empty_page():
    """PDF with one empty page and one page with a table."""
    pdf = _new_pdf()

    # Page 1: no table, just text
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 10, "This page has no tables, just text.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(10)
    pdf.cell(0, 10, "Lorem ipsum dolor sit amet.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Page 2: has a table
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 10, "Data Page", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    _bordered_table(pdf,
        headers=["Name", "Score"],
        rows=[["Alice", "95"], ["Bob", "87"]],
        col_widths=[60, 40],
    )

    pdf.output(str(FIXTURES_DIR / "empty_page.pdf"))
    print("Generated: empty_page.pdf")


def generate_special_chars():
    """Table with special characters: pipes, commas, quotes, HTML entities."""
    pdf = _new_pdf()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 10, "Special Characters", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)

    _bordered_table(pdf,
        headers=["Description", "Value"],
        rows=[
            ["Price (USD)", "$1,234.56"],
            ["Ratio", "3:1"],
            ['Contains "quotes"', "yes"],
            ["A & B", "<tag>"],
        ],
        col_widths=[70, 60],
    )

    pdf.output(str(FIXTURES_DIR / "special_chars.pdf"))
    print("Generated: special_chars.pdf")


def generate_wide_table():
    """Table with many columns."""
    pdf = _new_pdf()
    pdf.add_page(orientation="L")  # landscape
    pdf.set_font("Helvetica", size=8)
    pdf.cell(0, 10, "Wide Table", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)

    headers = ["ID", "Name", "Q1", "Q2", "Q3", "Q4", "Total", "Status"]
    rows = [
        ["1", "Alpha", "100", "150", "200", "250", "700", "Active"],
        ["2", "Beta", "90", "110", "130", "170", "500", "Active"],
        ["3", "Gamma", "0", "0", "50", "80", "130", "New"],
    ]
    col_widths = [15, 30, 25, 25, 25, 25, 30, 30]

    pdf.set_font("Helvetica", "B", 8)
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 7, h, border=1)
    pdf.ln()
    pdf.set_font("Helvetica", size=8)
    for row in rows:
        for i, cell in enumerate(row):
            pdf.cell(col_widths[i], 7, cell, border=1)
        pdf.ln()

    pdf.output(str(FIXTURES_DIR / "wide_table.pdf"))
    print("Generated: wide_table.pdf")


if __name__ == "__main__":
    generate_simple_bordered()
    generate_multi_table()
    generate_single_row()
    generate_multi_page()
    generate_empty_page()
    generate_special_chars()
    generate_wide_table()
    print("Done — all fixtures generated.")
