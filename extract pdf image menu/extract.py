# extract_wines.py
"""
CLI tool that downloads a beverage‑menu PDF, OCRs it, extracts only the wine offerings,
and saves them to a text file named `<restaurant_name>_wine_names.txt`.

Updated to extract from "wines by the glass" and "wines by the bottle" sections.
"""

import re
import sys
import tempfile
from pathlib import Path
from typing import List
import requests
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
from urllib.parse import urlparse

# Regular expressions for parsing wine data
WINE_SECTION_START_RE = re.compile(r"^(wines by the glass|wines by the bottle)", re.I)
WINE_SECTION_END_RE = re.compile(r"^(beer|cocktails?|spirits?|mocktails|non[- ]?alcoholic|sake|vermouth|liqueur|brandy|whiskey|scotch|tequila|rum|cider)\b", re.I)


def extract_restaurant_name(url: str) -> str:
    """Extract the restaurant name from the URL."""
    parsed_url = urlparse(url)
    # Use the domain name or path to infer the restaurant name
    restaurant_name = parsed_url.netloc.split(".")[0]  # Take the subdomain
    if not restaurant_name or restaurant_name == "www":
        # Fallback to the first segment of the path
        restaurant_name = parsed_url.path.split("/")[1] if parsed_url.path else "restaurant"
    return restaurant_name.replace("-", "_").capitalize()


def download_pdf(url: str) -> bytes:
    """Download the PDF from the given URL."""
    print(f"Downloading PDF: {url}")
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.content


def pdf_to_images(pdf_bytes: bytes) -> List[Image.Image]:
    """Convert PDF bytes to a list of images."""
    print("Converting PDF pages to images…")
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
        tmp_pdf.write(pdf_bytes)
        tmp_pdf_path = tmp_pdf.name

    images = convert_from_path(tmp_pdf_path, dpi=300, fmt="png")
    Path(tmp_pdf_path).unlink(missing_ok=True)
    return images


def ocr_images(images: List[Image.Image]) -> str:
    """Perform OCR on the images and return the extracted text."""
    print("Running OCR with Tesseract… (this may take a moment)")
    full_text = []
    for img in images:
        text = pytesseract.image_to_string(img, config="--psm 6")
        full_text.append(text)
    return "\n".join(full_text)


def extract_wine_lines(raw_text: str) -> List[str]:
    """Extract wine lines from the OCR text."""
    lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]
    capture = False
    wine_lines: List[str] = []

    for ln in lines:
        if WINE_SECTION_START_RE.match(ln):
            capture = True
            continue
        if capture and WINE_SECTION_END_RE.match(ln):
            capture = False
        if capture:
            wine_lines.append(ln)
    return wine_lines


def save_wine_names(wine_lines: List[str], output_path: Path):
    """Save the extracted wine names to a text file."""
    with output_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(wine_lines))
    print(f"Wine names saved to {output_path}")


def main(url: str):
    """Main function to process the PDF and save wine names."""
    restaurant_name = extract_restaurant_name(url)
    pdf_bytes = download_pdf(url)
    images = pdf_to_images(pdf_bytes)
    raw_text = ocr_images(images)

    wine_lines = extract_wine_lines(raw_text)
    if not wine_lines:
        print("No wine offerings detected – check OCR output or adjust regex patterns.")
        sys.exit(1)

    output_path = Path(f"{restaurant_name}_wine_names.txt")
    save_wine_names(wine_lines, output_path)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python extract.py <pdf_url>")
        sys.exit(1)
    main(sys.argv[1])