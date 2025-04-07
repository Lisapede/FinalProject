# wine_menu_scraper.py
"""
Wine Menu Finder (Updated)
==========================
Reads every ``*_RestaurantList.csv`` from **data/Restaurant_Lists_by_City/**,
adds a city name column, visits each restaurant’s website, hunts for a wine list link or PDF or menu page,
saves PDF or HTML menu files locally, and writes results to **data/restaurant_wine_offerings.csv**.

Heuristics used
---------------
1. **Direct wine links**: anchor tags whose text or href contains
   ``wine``, ``vino``, or ``vin``.
2. **Menu-ish links**: fallback to links containing ``menu``, ``dinner``,
   ``drinks``, ``beverage``, or ``happy hour``.
   Up to 10 pages scanned for wine keywords.
3. **PDF fallback**: links to PDF files with wine or drinks-related names,
   or from domains where PDF content contains wine references.

If no wine content is found, records **"No wines found"**.
"""

import csv
import glob
import os
import re
import ssl
import sys
from typing import List, Tuple
from urllib.parse import urljoin, urlparse
import urllib.request

from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Network helpers
# ---------------------------------------------------------------------------

context = ssl._create_unverified_context()

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0 Safari/537.36"
    )
}

def pull(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, context=context, timeout=30) as resp:
        data = resp.read()
        ctype = resp.headers.get("Content-Type", "").lower()
    if "pdf" in ctype or url.lower().endswith(".pdf"):
        return data.decode("latin1", errors="ignore")
    return data.decode("utf-8", errors="ignore")

def download_pdf(url: str, city: str, restaurant: str) -> str:
    filename = f"{city}_{restaurant}.pdf".replace(" ", "_")
    folder = os.path.join("data", f"{city}_Menus")
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, filename)
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=context, timeout=30) as resp:
            with open(filepath, "wb") as f:
                f.write(resp.read())
        return filepath
    except Exception as e:
        print(f"Failed to download PDF for {restaurant}: {e}")
        return ""

def save_html_menu(content: str, city: str, restaurant: str) -> str:
    filename = f"{city}_{restaurant}.html".replace(" ", "_")
    folder = os.path.join("data", f"{city}_Menus")
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, filename)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath
    except Exception as e:
        print(f"Failed to save HTML menu for {restaurant}: {e}")
        return ""

# ---------------------------------------------------------------------------
# Load restaurant list(s)
# ---------------------------------------------------------------------------

def list_restaurant_csvs() -> List[str]:
    return glob.glob(os.path.join("data", "Restaurant_Lists_by_City", "*_RestaurantList.csv"))

def extract_city_from_filename(filename: str) -> str:
    base = os.path.basename(filename)
    city = base.split("_RestaurantList.csv")[0]
    return city.replace(" ", "_")

def load_restaurants() -> List[dict]:
    rows: List[dict] = []
    for path in list_restaurant_csvs():
        city = extract_city_from_filename(path)
        with open(path, newline="", encoding="utf-8") as fh:
            csv_rows = list(csv.DictReader(fh))
            for row in csv_rows:
                row["city"] = city
            rows.extend(csv_rows)
    return rows

# ---------------------------------------------------------------------------
# Wine menu discovery
# ---------------------------------------------------------------------------

WINE_RE = re.compile(r"(wine|vino|vin\\s(?:rouge|blanc)?|by the glass|by the bottle)", re.I)
MENU_RE = re.compile(r"(menu|dinner|lunch|drink|drinks|beverage|happy)", re.I)

def candidate_links(soup: BeautifulSoup, base_url: str) -> List[Tuple[str, bool]]:
    links: List[Tuple[str, bool]] = []
    for a in soup.find_all("a", href=True):
        text = a.get_text(" ", strip=True)
        href = a["href"]
        if not href or href.startswith("#"):
            continue
        abs_url = urljoin(base_url, href)
        combined = f"{text} {href}".lower()
        has_wine = bool(re.search(r"wine|vino|vin", combined))
        if has_wine or MENU_RE.search(combined):
            links.append((abs_url, has_wine))
    links.sort(key=lambda t: (not t[1]))  # wine links first
    return links


def page_mentions_wine(html: str) -> bool:
    return bool(WINE_RE.search(html))


def find_wine_menu(start_url: str, city: str, restaurant: str) -> Tuple[str, str]:
    try:
        homepage_html = pull(start_url)
    except Exception as e:
        return "", f"Error fetching homepage: {e}"

    soup = BeautifulSoup(homepage_html, "lxml")

    # 1. direct wine links
    for url, has_wine in candidate_links(soup, start_url):
        if has_wine:
            return url, "Wine link found"

    # 2. menu-ish pages
    for url, _ in candidate_links(soup, start_url)[:10]:
        try:
            html = pull(url)
        except Exception:
            continue
        if page_mentions_wine(html):
            save_html_menu(html, city, restaurant)
            return url, "Wine found inside menu page"

    # 3. PDF fallback
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full_url = urljoin(start_url, href)
        if href.lower().endswith(".pdf"):
            try:
                pdf_text = pull(full_url)
                if page_mentions_wine(pdf_text) or re.search(r"wine|drink|menu|beverage", href, re.I):
                    download_pdf(full_url, city, restaurant)
                    return full_url, "Wine PDF link"
            except Exception:
                continue

    return "", "No wines found"

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    restaurants = load_restaurants()
    if not restaurants:
        print("No restaurant list CSVs found. Run restaurant_scraper.py first.", file=sys.stderr)
        sys.exit(1)

    out_rows = []
    for rest in restaurants:
        name = rest.get("name", "Unknown")
        website = rest.get("website", "").strip()
        city = rest.get("city", "UnknownCity").replace(" ", "_")
        if not website:
            out_rows.append({
                "name": name,
                "website": "",
                "wine_menu_url": "",
                "status": "No website listed",
                "city": city,
            })
            continue

        print(f"🔎 Searching wine menu for {name} in {city}…")
        menu_url, status = find_wine_menu(website, city, name)
        out_rows.append({
            "name": name,
            "website": website,
            "wine_menu_url": menu_url,
            "status": status,
            "city": city,
        })

    os.makedirs("data", exist_ok=True)
    out_path = os.path.join("data", "restaurant_wine_offerings.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["name", "website", "wine_menu_url", "status", "city"])
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"✅ Results written to {out_path}")


if __name__ == "__main__":
    main()
