#!/usr/bin/env python3
"""Generate the F0001-S0003 synthetic GL policy fixture (native + scanned variant).

No operator-supplied GL policy package was available before S0003 started, so per the
story's own contingency ("the Architect selects a synthetic package and records it",
section 117.1 item 5) this script generates one: a one-page Commercial General Liability
declarations page with an EachOccurrence limit, a GeneralAggregate limit, a named insured,
and policy effective dates — enough surface for both extraction profiles (gl-limits-a,
gl-limits-b) to exercise limit and date extraction with resolvable evidence.

Outputs:
    neuron/fixtures/gl-policy-declarations.pdf           (native text layer)
    neuron/fixtures/gl-policy-declarations-scanned.pdf   (image-only; forces OCR)
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

FIXTURES_DIR = Path(__file__).resolve().parent

DECLARATIONS_LINES = [
    "COMMERCIAL GENERAL LIABILITY COVERAGE PART",
    "DECLARATIONS",
    "",
    "Named Insured: Meridian Fabrication Works, LLC",
    "Policy Number: GL-2026-0001842",
    "Policy Period: 06/01/2026 to 06/01/2027",
    "",
    "LIMITS OF INSURANCE",
    "General Aggregate Limit (Other Than Products-Completed Operations): $2,000,000",
    "Products-Completed Operations Aggregate Limit: $2,000,000",
    "Each Occurrence Limit: $1,000,000",
    "Damage To Premises Rented To You Limit: $300,000",
    "Medical Expense Limit (Any One Person): $10,000",
    "",
    "Retroactive Date: Not Applicable",
    "Business Description: Metal Fabrication Contractor",
]


def build_native_pdf(path: Path) -> None:
    pdf = canvas.Canvas(str(path), pagesize=LETTER)
    width, height = LETTER
    y = height - 72
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(72, y, DECLARATIONS_LINES[0])
    y -= 18
    pdf.drawString(72, y, DECLARATIONS_LINES[1])
    y -= 30
    pdf.setFont("Helvetica", 10)
    for line in DECLARATIONS_LINES[2:]:
        pdf.drawString(72, y, line)
        y -= 16
    pdf.showPage()
    pdf.save()


def build_scanned_pdf(native_path: Path, scanned_path: Path) -> None:
    """Rasterize the native PDF's page to an image, then embed the image with no text
    layer — Docling must OCR this variant, exercising the S0003 OCR-call counter."""
    import pypdfium2 as pdfium

    doc = pdfium.PdfDocument(str(native_path))
    page = doc[0]
    bitmap = page.render(scale=2.0)
    pil_image = bitmap.to_pil()
    image_path = scanned_path.with_suffix(".png")
    pil_image.save(image_path)

    pdf = canvas.Canvas(str(scanned_path), pagesize=LETTER)
    width, height = LETTER
    pdf.drawImage(str(image_path), 0, 0, width=width, height=height)
    pdf.showPage()
    pdf.save()
    image_path.unlink()


def main() -> None:
    native_path = FIXTURES_DIR / "gl-policy-declarations.pdf"
    scanned_path = FIXTURES_DIR / "gl-policy-declarations-scanned.pdf"
    build_native_pdf(native_path)
    build_scanned_pdf(native_path, scanned_path)
    print(f"wrote {native_path}")
    print(f"wrote {scanned_path}")


if __name__ == "__main__":
    main()
