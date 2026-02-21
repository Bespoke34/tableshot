"""Optional ML backend: Table Transformer for image-based table detection.

Requires the [ml] extra: pip install tableshot[ml]
Uses Microsoft's Table Transformer models for:
  - Table detection (finding tables in document images)
  - Table structure recognition (finding rows/columns within tables)

For text extraction:
  - PDF sources: maps detected regions back to PDF coordinates, uses pdfplumber
  - Image sources: uses OCR if [ocr] extra is installed
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from tableshot.backends.pdfplumber_backend import Table
from tableshot.utils import clean_cell, pad_row

logger = logging.getLogger(__name__)

# Lazy-loaded globals
_detection_model = None
_detection_processor = None
_structure_model = None
_structure_processor = None
_ocr_predictor = None
_device: str | None = None

DETECTION_MODEL_ID = "microsoft/table-transformer-detection"
STRUCTURE_MODEL_ID = "microsoft/table-transformer-structure-recognition-v1.1-all"
DETECTION_THRESHOLD = 0.7
STRUCTURE_THRESHOLD = 0.6

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}


def _check_ml_deps() -> None:
    """Verify that ML dependencies are installed."""
    missing = []
    for pkg in ("torch", "transformers", "timm"):
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        raise ImportError(
            f"ML backend requires: {', '.join(missing)}. "
            "Install with: pip install tableshot[ml]"
        )


def _get_device() -> str:
    """Detect the best available compute device."""
    global _device
    if _device is not None:
        return _device

    import torch

    if torch.cuda.is_available():
        _device = "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        _device = "mps"
    else:
        _device = "cpu"

    logger.info("ML backend using device: %s", _device)
    return _device


def _load_detection_model():
    """Lazy-load the table detection model."""
    global _detection_model, _detection_processor
    if _detection_model is not None:
        return _detection_model, _detection_processor

    _check_ml_deps()
    from transformers import AutoImageProcessor, TableTransformerForObjectDetection

    device = _get_device()
    _detection_processor = AutoImageProcessor.from_pretrained(DETECTION_MODEL_ID)
    _detection_model = TableTransformerForObjectDetection.from_pretrained(DETECTION_MODEL_ID)
    _detection_model.to(device)
    _detection_model.eval()

    logger.info("Loaded table detection model: %s", DETECTION_MODEL_ID)
    return _detection_model, _detection_processor


def _load_structure_model():
    """Lazy-load the table structure recognition model."""
    global _structure_model, _structure_processor
    if _structure_model is not None:
        return _structure_model, _structure_processor

    _check_ml_deps()
    from transformers import AutoImageProcessor, TableTransformerForObjectDetection

    device = _get_device()
    # Explicit size avoids compat issues with newer transformers versions
    # where the saved config may only have 'longest_edge'.
    _structure_processor = AutoImageProcessor.from_pretrained(
        STRUCTURE_MODEL_ID,
        size={"shortest_edge": 800, "longest_edge": 1000},
    )
    _structure_model = TableTransformerForObjectDetection.from_pretrained(STRUCTURE_MODEL_ID)
    _structure_model.to(device)
    _structure_model.eval()

    logger.info("Loaded structure recognition model: %s", STRUCTURE_MODEL_ID)
    return _structure_model, _structure_processor


def _load_ocr() -> object | None:
    """Lazy-load the OCR predictor (requires [ocr] extra). Returns None if unavailable."""
    global _ocr_predictor
    if _ocr_predictor is not None:
        return _ocr_predictor

    try:
        from onnxtr.models import ocr_predictor
        _ocr_predictor = ocr_predictor(pretrained=True)
        logger.info("Loaded OCR predictor (onnxtr)")
        return _ocr_predictor
    except ImportError:
        logger.debug("OCR not available — install tableshot[ocr] for image text extraction")
        return None


# ── Bounding box helper ──────────────────────────────────────────────


@dataclass
class BBox:
    """Axis-aligned bounding box."""

    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    def intersection(self, other: BBox) -> BBox | None:
        """Return the intersection box, or None if they don't overlap."""
        ix1 = max(self.x1, other.x1)
        iy1 = max(self.y1, other.y1)
        ix2 = min(self.x2, other.x2)
        iy2 = min(self.y2, other.y2)
        if ix1 < ix2 and iy1 < iy2:
            return BBox(ix1, iy1, ix2, iy2)
        return None


# ── Core ML functions ────────────────────────────────────────────────


def detect_tables(image) -> list[BBox]:
    """Detect table locations in a document image.

    Args:
        image: PIL Image of a full document page.

    Returns:
        List of BBox for each detected table, sorted top to bottom.
    """
    import torch

    model, processor = _load_detection_model()
    device = _get_device()

    inputs = processor(images=image, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)

    target_sizes = torch.tensor([image.size[::-1]]).to(device)  # (height, width)
    results = processor.post_process_object_detection(
        outputs, threshold=DETECTION_THRESHOLD, target_sizes=target_sizes
    )[0]

    boxes = []
    for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
        label_name = model.config.id2label[label.item()]
        if label_name == "table":
            x1, y1, x2, y2 = box.tolist()
            boxes.append(BBox(x1, y1, x2, y2))

    boxes.sort(key=lambda b: b.y1)
    return boxes


def recognize_structure(table_image) -> tuple[list[BBox], list[BBox]]:
    """Recognize rows and columns in a cropped table image.

    Args:
        table_image: PIL Image of a cropped table region.

    Returns:
        Tuple of (rows, columns) — each a list of BBox sorted by position.
    """
    import torch

    model, processor = _load_structure_model()
    device = _get_device()

    inputs = processor(images=table_image, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)

    target_sizes = torch.tensor([table_image.size[::-1]]).to(device)
    results = processor.post_process_object_detection(
        outputs, threshold=STRUCTURE_THRESHOLD, target_sizes=target_sizes
    )[0]

    rows: list[BBox] = []
    columns: list[BBox] = []

    for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
        label_name = model.config.id2label[label.item()]
        x1, y1, x2, y2 = box.tolist()
        bbox = BBox(x1, y1, x2, y2)

        if label_name == "table row":
            rows.append(bbox)
        elif label_name == "table column":
            columns.append(bbox)

    rows.sort(key=lambda b: b.y1)
    columns.sort(key=lambda b: b.x1)
    return rows, columns


def ocr_image(image) -> list[tuple[str, BBox]]:
    """Run OCR on an image. Returns list of (word_text, bbox) pairs.

    Requires the [ocr] extra. Returns empty list if OCR is unavailable.
    """
    predictor = _load_ocr()
    if predictor is None:
        return []

    import numpy as np

    img_array = np.array(image.convert("RGB"))
    result = predictor([img_array])

    words: list[tuple[str, BBox]] = []
    if not result.pages:
        return words

    page = result.pages[0]
    h, w = image.size[1], image.size[0]

    for block in page.blocks:
        for line in block.lines:
            for word in line.words:
                # onnxtr returns normalized coords (0-1)
                (nx1, ny1), (nx2, ny2) = word.geometry
                bbox = BBox(nx1 * w, ny1 * h, nx2 * w, ny2 * h)
                words.append((word.value, bbox))

    return words


def _words_in_box(words: list[tuple[str, BBox]], box: BBox) -> str:
    """Find all OCR'd words whose center falls within a bounding box."""
    found = []
    for text, wbox in words:
        cx = (wbox.x1 + wbox.x2) / 2
        cy = (wbox.y1 + wbox.y2) / 2
        if box.x1 <= cx <= box.x2 and box.y1 <= cy <= box.y2:
            found.append((wbox.y1, wbox.x1, text))  # sort by position

    found.sort()
    return " ".join(t for _, _, t in found)


# ── High-level extraction ────────────────────────────────────────────


def render_pdf_page(pdf_path: str, page_idx: int, scale: float = 2.0):
    """Render a PDF page to a PIL Image using pypdfium2.

    Args:
        pdf_path: Path to the PDF file.
        page_idx: 0-indexed page number.
        scale: Resolution scale (2.0 = 144 DPI).

    Returns:
        PIL Image of the rendered page.
    """
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(pdf_path)
    page = pdf[page_idx]
    bitmap = page.render(scale=scale)
    image = bitmap.to_pil()
    pdf.close()
    return image


def extract_tables_from_image(image, page_num: int = 1) -> list[Table]:
    """Detect and extract all tables from a document image.

    Uses Table Transformer for detection and structure recognition,
    and OCR for text extraction (if [ocr] extra is installed).

    Args:
        image: PIL Image of a document page.
        page_num: 1-indexed page number for metadata.

    Returns:
        List of Table objects.
    """
    _check_ml_deps()

    table_boxes = detect_tables(image)
    if not table_boxes:
        return []

    tables: list[Table] = []

    for idx, tbox in enumerate(table_boxes):
        # Crop the table from the full page image
        table_img = image.crop((
            max(0, int(tbox.x1)),
            max(0, int(tbox.y1)),
            min(image.width, int(tbox.x2)),
            min(image.height, int(tbox.y2)),
        ))

        rows, columns = recognize_structure(table_img)
        if not rows or not columns:
            continue

        # OCR the table image once, then map words to cells
        words = ocr_image(table_img)
        ocr_available = len(words) > 0

        grid: list[list[str]] = []
        for row in rows:
            row_data: list[str] = []
            for col in columns:
                cell_box = row.intersection(col)
                if cell_box and cell_box.width > 2 and cell_box.height > 2:
                    if ocr_available:
                        text = _words_in_box(words, cell_box)
                        row_data.append(clean_cell(text))
                    else:
                        row_data.append("")
                else:
                    row_data.append("")
            grid.append(row_data)

        if not grid or not any(any(cell for cell in row) for row in grid):
            # If no OCR, we still have the structure — return with empty cells
            # and a note that OCR is needed
            if not ocr_available and rows and columns:
                grid = [[""] * len(columns) for _ in rows]
                logger.warning(
                    "Table %d detected but no text extracted — install tableshot[ocr]", idx + 1
                )

        if not grid:
            continue

        max_cols = max(len(row) for row in grid)
        grid = [pad_row(row, max_cols) for row in grid]

        tables.append(Table(
            page=page_num,
            table_index=idx,
            data=grid,
            headers=grid[0] if grid else [],
        ))

    return tables


def extract_tables_ml_pdf(
    pdf_path: str,
    pdf,
    page_indices: list[int],
    scale: float = 2.0,
) -> list[Table]:
    """ML-assisted extraction from a PDF.

    Uses Table Transformer for table detection and structure recognition,
    then maps detected cells back to PDF coordinates for text extraction
    via pdfplumber (fast, no OCR needed for native PDFs).

    Args:
        pdf_path: Path to the PDF file on disk.
        pdf: Open pdfplumber.PDF object.
        page_indices: 0-indexed page numbers to process.
        scale: Rendering scale for ML detection.

    Returns:
        List of Table objects.
    """
    _check_ml_deps()

    all_tables: list[Table] = []

    for page_idx in page_indices:
        image = render_pdf_page(pdf_path, page_idx, scale=scale)
        table_boxes = detect_tables(image)

        if not table_boxes:
            continue

        page = pdf.pages[page_idx]

        for idx, tbox in enumerate(table_boxes):
            # Crop table region from image for structure recognition
            table_img = image.crop((
                max(0, int(tbox.x1)),
                max(0, int(tbox.y1)),
                min(image.width, int(tbox.x2)),
                min(image.height, int(tbox.y2)),
            ))

            rows, columns = recognize_structure(table_img)
            if not rows or not columns:
                continue

            grid: list[list[str]] = []
            for row in rows:
                row_data: list[str] = []
                for col in columns:
                    cell_box = row.intersection(col)
                    if cell_box and cell_box.width > 2 and cell_box.height > 2:
                        # Convert cell coords (relative to table image) to PDF coords
                        pdf_bbox = (
                            (tbox.x1 + cell_box.x1) / scale,
                            (tbox.y1 + cell_box.y1) / scale,
                            (tbox.x1 + cell_box.x2) / scale,
                            (tbox.y1 + cell_box.y2) / scale,
                        )
                        try:
                            cropped = page.crop(pdf_bbox)
                            text = cropped.extract_text() or ""
                        except Exception:
                            text = ""
                        row_data.append(clean_cell(text))
                    else:
                        row_data.append("")
                grid.append(row_data)

            if not grid or not any(any(cell for cell in row) for row in grid):
                continue

            max_cols = max(len(row) for row in grid)
            grid = [pad_row(row, max_cols) for row in grid]

            all_tables.append(Table(
                page=page_idx + 1,
                table_index=idx,
                data=grid,
                headers=grid[0] if grid else [],
            ))

    return all_tables
