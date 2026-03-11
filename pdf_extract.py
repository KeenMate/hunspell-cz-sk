"""Extract text from a PDF file and write it to a .txt file."""

import argparse
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("PyMuPDF not installed. Run: pip install pymupdf")


def extract(pdf_path: Path) -> str:
    doc = fitz.open(pdf_path)
    pages = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()
    return "\n".join(pages)


def main():
    parser = argparse.ArgumentParser(description="Extract text from PDF")
    parser.add_argument("pdf", type=Path, help="Path to PDF file")
    parser.add_argument("-o", "--output", type=Path, help="Output .txt file (default: same name as PDF)")
    args = parser.parse_args()

    if not args.pdf.exists():
        sys.exit(f"File not found: {args.pdf}")

    text = extract(args.pdf)

    out = args.output or args.pdf.with_suffix(".txt")
    out.write_text(text, encoding="utf-8")
    print(f"Extracted {len(text)} chars -> {out}")


if __name__ == "__main__":
    main()
