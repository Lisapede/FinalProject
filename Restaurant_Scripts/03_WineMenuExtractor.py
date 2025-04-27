# 03_WineMenuExtractor.py
"""
Wine Menu Extractor
===================

Parses downloaded wine menu files (HTML or PDF) from each `{city}_Menus` folder
and extracts individual wine entries into a structured CSV file:
`data/wine_menu_extracted.csv`

The output CSV includes:
- city
- restaurant
- wine_name (or line item)
- wine_section (e.g., 'by the glass', 'by the bottle', etc.)
"""

import os
import re
import csv
import glob
from bs4 import BeautifulSoup

WINE_SECTION_RE = re.compile(r"by the glass|by the bottle|glass pours|bottles", re.I)


def extract_from_html(filepath, city, restaurant):
    with open(filepath, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "lxml")
        text = soup.get_text("\n", strip=True)
    return extract_wines_from_text(text, city, restaurant)


def extract_from_pdf(filepath, city, restaurant):
    try:
        import PyPDF2
    except ImportError:
        print("PyPDF2 is required to extract from PDFs. Run 'pip install PyPDF2'.")
        return []

    lines = []
    try:
        with open(filepath, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                lines.append(page.extract_text())
    except Exception as e:
        print(f"Error reading PDF {filepath}: {e}")
        return []

    text = "\n".join(lines)
    return extract_wines_from_text(text, city, restaurant)


def extract_wines_from_text(text, city, restaurant):
    entries = []
    lines = text.splitlines()
    section = ""
    buffer = ""

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Detect section
        if WINE_SECTION_RE.search(line):
            section = line.strip()
            continue

        # Append line to buffer and decide when to finalize
        buffer += (" " + line if buffer else line)

        # Heuristic: finalize buffer if the line ends with price or punctuation
        if re.search(r"\$\d+|\d{2}\s*$|[\.:;\-]\s*$", line) or len(buffer.split()) > 12:
            if any(word in buffer.lower() for word in [
                "chardonnay", "cabernet", "pinot", "riesling", "merlot",
                "sauvignon", "rose", "sparkling", "bordeaux", "barolo", "tempranillo"
            ]):
                entries.append({
                    "city": city,
                    "restaurant": restaurant,
                    "wine_section": section,
                    "wine_name": buffer.strip(),
                })
            buffer = ""  # reset

    return entries


def main():
    all_entries = []
    folders = glob.glob("data/*_Menus")

    for folder in folders:
        city = os.path.basename(folder).replace("_Menus", "")
        for filepath in glob.glob(os.path.join(folder, "*.html")):
            restaurant = os.path.basename(filepath).replace(".html", "").replace(f"{city}_", "")
            all_entries.extend(extract_from_html(filepath, city, restaurant))
        for filepath in glob.glob(os.path.join(folder, "*.pdf")):
            restaurant = os.path.basename(filepath).replace(".pdf", "").replace(f"{city}_", "")
            all_entries.extend(extract_from_pdf(filepath, city, restaurant))

    out_path = os.path.join("data", "wine_menu_extracted.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["city", "restaurant", "wine_section", "wine_name"])
        writer.writeheader()
        writer.writerows(all_entries)

    print(f"✅ Extracted wine data written to {out_path}")


if __name__ == "__main__":
    main()
