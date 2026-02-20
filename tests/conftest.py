"""Shared test fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def simple_bordered_pdf(fixtures_dir: Path) -> str:
    """Path to a simple bordered-table PDF fixture."""
    path = fixtures_dir / "simple_bordered.pdf"
    if not path.exists():
        pytest.skip("Fixture simple_bordered.pdf not found")
    return str(path)
