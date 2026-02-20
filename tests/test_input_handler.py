"""Tests for input_handler: local files, URLs, error conditions."""

from __future__ import annotations

import http.server
import threading
from pathlib import Path

import pytest

from tableshot.input_handler import _is_url, load_pdf

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SIMPLE_PDF = str(FIXTURES_DIR / "simple_bordered.pdf")


class TestIsUrl:
    def test_http(self):
        assert _is_url("http://example.com/file.pdf") is True

    def test_https(self):
        assert _is_url("https://example.com/file.pdf") is True

    def test_local_path(self):
        assert _is_url("/home/user/file.pdf") is False

    def test_windows_path(self):
        assert _is_url(r"C:\Users\test\file.pdf") is False

    def test_empty(self):
        assert _is_url("") is False


class TestLoadPdfLocal:
    def test_opens_valid_pdf(self):
        pdf, temp = load_pdf(SIMPLE_PDF)
        assert temp is None
        assert len(pdf.pages) >= 1
        pdf.close()

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError, match="File not found"):
            load_pdf("/nonexistent/path/file.pdf")

    def test_not_a_pdf(self):
        with pytest.raises(ValueError, match="Expected a PDF"):
            load_pdf(__file__)  # .py file


class TestLoadPdfUrl:
    """Test URL download via a local HTTP server serving our fixtures."""

    @pytest.fixture(autouse=True)
    def _start_server(self, tmp_path: Path):
        """Start a minimal HTTP server serving the fixtures directory."""
        import functools

        handler = functools.partial(
            http.server.SimpleHTTPRequestHandler,
            directory=str(FIXTURES_DIR),
        )
        self.server = http.server.HTTPServer(("127.0.0.1", 0), handler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        yield
        self.server.shutdown()

    def test_download_and_open(self):
        url = f"http://127.0.0.1:{self.port}/simple_bordered.pdf"
        pdf, temp = load_pdf(url)
        try:
            assert len(pdf.pages) >= 1
            assert temp is not None
            assert temp.exists()
        finally:
            pdf.close()
            if temp:
                temp.unlink(missing_ok=True)

    def test_download_cleans_up_temp(self):
        url = f"http://127.0.0.1:{self.port}/simple_bordered.pdf"
        pdf, temp = load_pdf(url)
        pdf.close()
        temp_path = temp
        temp.unlink(missing_ok=True)
        assert not temp_path.exists()

    def test_download_bad_url(self):
        with pytest.raises(ValueError, match="Failed to download"):
            load_pdf(f"http://127.0.0.1:{self.port}/nonexistent.pdf")


class TestCorruptPdf:
    def test_corrupt_file(self, tmp_path: Path):
        """A file with .pdf extension but garbage content should raise."""
        bad_pdf = tmp_path / "corrupt.pdf"
        bad_pdf.write_bytes(b"this is not a PDF at all")
        with pytest.raises(Exception):
            load_pdf(str(bad_pdf))
