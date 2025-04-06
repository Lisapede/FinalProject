# wine_menu_scraper.py
"""
Wine Menu Finder
================
Reads every ``*_RestaurantList.csv`` that the *restaurant_scraper.py* tool
produces (they live in **data/Restaurant_Lists_by_City/**), visits each
restaurant’s website, hunts for a page or PDF that contains the wine list,
and writes the results to **data/restaurant_wine_offerings.csv**.

Heuristics used
---------------
1. **Direct wine links** – anchor tags whose text **or** href contains any of
   ``wine``, ``vino``, or ``vin``.
2. **Menu‑ish links** – if no direct wine link exists, follow links whose text
   or href looks like a menu (``menu``, ``dinner``, ``drinks``, ``beverage``,
   ``happy hour``).  Up to 10 such pages are fetched and scanned for wine
   keywords.
3. **PDF fallback** – PDF links whose filename hints at wine or drinks.

If nothing is found the script records **“No wines found”**.

Run
---
$ python wine_menu_scraper.py
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
    """Download *url* and return decoded text (best‑effort for PDFs)."""
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, context=context, timeout=30) as resp:
        data = resp.read()
        ctype = resp.headers.get("Content-Type", "").lower()
    # naïve PDF handling — we only need to keyword‑scan
    if "pdf" in ctype or url.lower().endswith(".pdf"):
        return data.decode("latin1", errors="ignore")
    return data.decode("utf-8", errors="ignore")

# ---------------------------------------------------------------------------
# Load restaurant list(s)
# ---------------------------------------------------------------------------

def list_restaurant_csvs() -> List[str]:
    """Return paths to all *_RestaurantList.csv files under the city folder."""
    return glob.glob(os.path.join("data", "Restaurant_Lists_by_City", "*_RestaurantList.csv"))


def load_restaurants() -> List[dict]:
    rows: List[dict] = []
    for path in list_restaurant_csvs():
        with open(path, newline="", encoding="utf-8") as fh:
            rows.extend(list(csv.DictReader(fh)))
    return rows

# ---------------------------------------------------------------------------
# Wine‑menu discovery
# ---------------------------------------------------------------------------

WINE_RE = re.compile(r"(wine|vino|vin\s(?:rouge|blanc)?|by the glass|by the bottle)", re.I)
MENU_RE = re.compile(r"(menu|dinner|lunch|drink|drinks|beverage|happy)", re.I)


def candidate_links(soup: BeautifulSoup, base_url: str) -> List[Tuple[str, bool]]:
    """Return [(abs_url, has_wine_kw)] sorted with wine‑specific links first."""
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


def find_wine_menu(start_url: str) -> Tuple[str, str]:
    """Return (menu_url, status) or ("", "No wines found")."""
    try:
        homepage_html = pull(start_url)
    except Exception as e:
        return "", f"Error fetching homepage: {e}"

    soup = BeautifulSoup(homepage_html, "lxml")

    # 1️⃣  direct wine links
    for url, has_wine in candidate_links(soup, start_url):
        if has_wine:
            return url, "Wine link found"

    # 2️⃣  scan up to 10 menu‑ish pages
    for url, _ in candidate_links(soup, start_url)[:10]:
        try:
            html = pull(url)
        except Exception:
            continue
        if page_mentions_wine(html):
            return url, "Wine found inside menu page"

    # 3️⃣  PDF fallback
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.lower().endswith(".pdf") and re.search(r"wine|drink", href, re.I):
            return urljoin(start_url, href), "Wine PDF link"

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
        if not website:
            out_rows.append({
                "name": name,
                "website": "",
                "wine_menu_url": "",
                "status": "No website listed",
            })
            continue

        print(f"🔎 Searching wine menu for {name}…")
        menu_url, status = find_wine_menu(website)
        out_rows.append({
            "name": name,
            "website": website,
            "wine_menu_url": menu_url,
            "status": status,
        })

    os.makedirs("data", exist_ok=True)
    out_path = os.path.join("data", "restaurant_wine_offerings.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["name", "website", "wine_menu_url", "status"])
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"✅ Results written to {out_path}")


if __name__ == "__main__":
    main()
