"""Generate a sample PDF for local demo uploads."""

from io import BytesIO
from pathlib import Path

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject, NumberObject

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "samples" / "demo-lab-report.pdf"
TEXT = """Sample Lab Report

Date: 15/03/2025
Hospital: City General Hospital
Physician: Dr. Anita Sharma

Diagnosis: Type 2 Diabetes Mellitus

Medication: Metformin 500mg twice daily

BP: 130/85 mmHg
HbA1c: 7.4%

Procedure: Fasting Blood Glucose Test

Allergy: Penicillin
"""


def build_pdf(text: str) -> bytes:
    # Minimal PDF with text stream (sufficient for pypdf extraction in demo)
    stream = DecodedStreamObject()
    stream.set_data(f"BT /F1 12 Tf 50 750 Td ({text.replace('(', '\\(').replace(')', '\\)')[:800]}) Tj ET".encode())
    page = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Page"),
            NameObject("/Parent"): NameObject("/Pages"),
            NameObject("/MediaBox"): [NumberObject(0), NumberObject(0), NumberObject(612), NumberObject(792)],
            NameObject("/Contents"): stream,
        }
    )
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


if __name__ == "__main__":
    OUTPUT.write_bytes(build_pdf(TEXT))
    print(f"Wrote {OUTPUT}")
