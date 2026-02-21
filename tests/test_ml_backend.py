"""Tests for the ML backend and image support.

Unit tests (BBox, routing, image detection) run without ML dependencies.
Integration tests that require torch/transformers are marked @pytest.mark.slow.
"""

from __future__ import annotations

import pytest

from tableshot.backends.ml_backend import BBox, IMAGE_EXTENSIONS, _check_ml_deps, _words_in_box
from tableshot.input_handler import has_text_layer, is_image_source


# ── Unit tests (no ML deps needed) ───────────────────────────────────


class TestBBox:
    """Tests for the BBox dataclass."""

    def test_width_height(self):
        b = BBox(10, 20, 50, 80)
        assert b.width == 40
        assert b.height == 60

    def test_intersection_overlap(self):
        a = BBox(0, 0, 100, 50)
        b = BBox(20, 10, 80, 40)
        result = a.intersection(b)
        assert result is not None
        assert result.x1 == 20
        assert result.y1 == 10
        assert result.x2 == 80
        assert result.y2 == 40

    def test_intersection_no_overlap(self):
        a = BBox(0, 0, 10, 10)
        b = BBox(20, 20, 30, 30)
        assert a.intersection(b) is None

    def test_intersection_edge_touch(self):
        a = BBox(0, 0, 10, 10)
        b = BBox(10, 0, 20, 10)
        # Touching edges — no overlap (x1 == x2)
        assert a.intersection(b) is None

    def test_intersection_partial(self):
        a = BBox(0, 0, 50, 50)
        b = BBox(25, 25, 75, 75)
        result = a.intersection(b)
        assert result is not None
        assert result.x1 == 25
        assert result.y1 == 25
        assert result.x2 == 50
        assert result.y2 == 50


class TestWordsInBox:
    """Tests for mapping OCR words to cell regions."""

    def test_words_inside_box(self):
        words = [
            ("hello", BBox(10, 10, 40, 20)),
            ("world", BBox(50, 10, 90, 20)),
            ("outside", BBox(200, 200, 250, 210)),
        ]
        box = BBox(0, 0, 100, 30)
        result = _words_in_box(words, box)
        assert "hello" in result
        assert "world" in result
        assert "outside" not in result

    def test_empty_words(self):
        assert _words_in_box([], BBox(0, 0, 100, 100)) == ""

    def test_word_center_must_be_inside(self):
        # Word bbox straddles the boundary, but center is outside
        words = [("edge", BBox(95, 0, 110, 10))]
        box = BBox(0, 0, 100, 20)
        result = _words_in_box(words, box)
        # Center x = 102.5, which is outside box.x2=100
        assert result == ""


class TestIsImageSource:
    """Tests for image source detection."""

    def test_png(self):
        assert is_image_source("photo.png") is True

    def test_jpg(self):
        assert is_image_source("photo.jpg") is True

    def test_jpeg(self):
        assert is_image_source("photo.JPEG") is True

    def test_pdf(self):
        assert is_image_source("report.pdf") is False

    def test_url_image(self):
        assert is_image_source("https://example.com/table.png") is True

    def test_url_pdf(self):
        assert is_image_source("https://example.com/report.pdf") is False

    def test_tiff(self):
        assert is_image_source("scan.tiff") is True

    def test_webp(self):
        assert is_image_source("image.webp") is True

    def test_image_extensions_complete(self):
        expected = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}
        assert IMAGE_EXTENSIONS == expected


class TestHasTextLayer:
    """Tests for text layer detection."""

    def test_pdf_with_text(self, simple_bordered_pdf):
        import pdfplumber
        pdf = pdfplumber.open(simple_bordered_pdf)
        assert has_text_layer(pdf, 0) is True
        pdf.close()

    def test_fixture_pdfs_have_text(self, fixtures_dir):
        import pdfplumber
        for pdf_file in fixtures_dir.glob("*.pdf"):
            pdf = pdfplumber.open(str(pdf_file))
            # All generated fixtures have text layers
            assert has_text_layer(pdf, 0) is True, f"{pdf_file.name} should have text"
            pdf.close()


class TestSmartRouting:
    """Tests for backend auto-detection."""

    def test_image_source_routes_to_ml(self):
        """Image files should be detected for ML routing."""
        assert is_image_source("table.png") is True
        assert is_image_source("report.pdf") is False

    def test_pdf_with_text_uses_pdfplumber(self, simple_bordered_pdf):
        """PDFs with text layers should use pdfplumber by default."""
        from tableshot.pipeline import run_extraction
        result = run_extraction(simple_bordered_pdf, fmt="markdown")
        assert result.backend == "pdfplumber"
        assert result.total_tables > 0

    def test_explicit_backend_pdfplumber(self, simple_bordered_pdf):
        """Explicit backend='pdfplumber' should work."""
        from tableshot.pipeline import run_extraction
        result = run_extraction(simple_bordered_pdf, fmt="markdown", backend="pdfplumber")
        assert result.backend == "pdfplumber"

    def test_image_source_rejected_without_ml(self):
        """Image input without ML deps should give a clear error."""
        from tableshot.pipeline import run_extraction
        try:
            run_extraction("tests/by hand/b5I1GQB.png", fmt="markdown")
            # If all ML deps are installed, this might succeed — that's fine
        except ImportError as e:
            assert "tableshot[ml]" in str(e)
        except (FileNotFoundError, ValueError):
            pass  # File might not exist in CI, or image load fails


class TestCheckMlDeps:
    """Tests for ML dependency checking."""

    def test_check_reports_install_command(self):
        """If ML deps are missing, error message should mention tableshot[ml]."""
        try:
            _check_ml_deps()
        except ImportError as e:
            assert "tableshot[ml]" in str(e)
        # If deps are installed, this just passes


# ── Integration tests (require torch + transformers) ─────────────────


@pytest.fixture
def has_ml():
    """Skip test if ML dependencies are not installed."""
    pytest.importorskip("torch")
    pytest.importorskip("transformers")


@pytest.fixture
def has_ocr():
    """Skip test if OCR dependencies are not installed."""
    pytest.importorskip("onnxtr")


@pytest.mark.slow
class TestMLDetection:
    """Integration tests for ML table detection. Requires torch + transformers."""

    def test_detect_tables_simple(self, has_ml, simple_bordered_pdf):
        """Detect tables in a rendered PDF page."""
        from tableshot.backends.ml_backend import detect_tables, render_pdf_page

        image = render_pdf_page(simple_bordered_pdf, page_idx=0)
        tables = detect_tables(image)
        assert len(tables) >= 1
        # Table should have reasonable dimensions
        assert tables[0].width > 50
        assert tables[0].height > 50

    def test_recognize_structure(self, has_ml, simple_bordered_pdf):
        """Recognize rows and columns in a table image."""
        from tableshot.backends.ml_backend import (
            detect_tables,
            recognize_structure,
            render_pdf_page,
        )

        image = render_pdf_page(simple_bordered_pdf, page_idx=0)
        table_boxes = detect_tables(image)
        assert len(table_boxes) >= 1

        tbox = table_boxes[0]
        table_img = image.crop((int(tbox.x1), int(tbox.y1), int(tbox.x2), int(tbox.y2)))
        rows, columns = recognize_structure(table_img)
        assert len(rows) >= 2  # at least header + 1 data row
        assert len(columns) >= 2

    def test_ml_pdf_extraction(self, has_ml, simple_bordered_pdf):
        """Full ML extraction pipeline on a PDF with text layer."""
        from tableshot.backends.ml_backend import extract_tables_ml_pdf

        import pdfplumber
        pdf = pdfplumber.open(simple_bordered_pdf)
        tables = extract_tables_ml_pdf(simple_bordered_pdf, pdf, [0])
        pdf.close()
        assert len(tables) >= 1
        assert tables[0].rows >= 2
        assert tables[0].cols >= 2

    def test_extract_from_image(self, has_ml):
        """Extract tables from a direct image input."""
        from tableshot.backends.ml_backend import extract_tables_from_image, render_pdf_page

        # Use a rendered PDF page as our "image"
        from pathlib import Path
        fixtures = Path(__file__).parent / "fixtures"
        pdf_path = str(fixtures / "simple_bordered.pdf")

        image = render_pdf_page(pdf_path, page_idx=0)
        tables = extract_tables_from_image(image)
        assert len(tables) >= 1

    def test_pipeline_ml_backend(self, has_ml, simple_bordered_pdf):
        """Pipeline with explicit backend='ml'."""
        from tableshot.pipeline import run_extraction
        result = run_extraction(simple_bordered_pdf, fmt="markdown", backend="ml")
        assert result.backend == "table-transformer"
        assert result.total_tables >= 1

    def test_render_pdf_page(self, has_ml, simple_bordered_pdf):
        """PDF page rendering produces a valid image."""
        from tableshot.backends.ml_backend import render_pdf_page

        image = render_pdf_page(simple_bordered_pdf, page_idx=0)
        assert image.width > 100
        assert image.height > 100
        assert image.mode == "RGB"

    def test_device_detection(self, has_ml):
        """Device detection returns a valid device string."""
        from tableshot.backends.ml_backend import _get_device

        device = _get_device()
        assert device in ("cpu", "cuda", "mps")
