# 01_RestaurantList.py
"""
Restaurant List Scraper
=======================
Scrapes an Eater "best restaurants" article and writes the results to a
CSV file named ``<CityName>_RestaurantList.csv`` inside a
``data/Restaurant_Lists_by_City`` folder.

Usage
-----
$ python restaurant_scraper.py <eater_article_url>

Example
-------
$ python restaurant_scraper.py https://boston.eater.com/maps/best-restaurants-boston-38
"""

import argparse
import csv
import os
import re
import ssl
from typing import Dict, List
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Disable SSL verification warnings (Eater occasionally mis‑configures TLS)
ssl._create_default_https_context = ssl._create_unverified_context  # type: ignore

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0 Safari/537.36"
    )
}


def extract_city_name(url: str) -> str:
    """Guess the city name from the Eater article URL."""
    parsed = urlparse(url)

    # First, try the sub‑domain pattern ``city.eater.com``
    if parsed.netloc.endswith(".eater.com"):
        sub = parsed.netloc.split(".")[0]
        if sub and sub.lower() not in {"www", "maps"}:
            return sub.capitalize()

    # Fallback: look for an alphabetic segment in the path (e.g. /boston/…)
    for segment in parsed.path.split("/"):
        if segment.isalpha():
            return segment.capitalize()

    return "UnknownCity"


def fetch_html(url: str) -> str:
    """Download *url* and return the HTML as text."""
    resp = requests.get(url, headers=HEADERS, timeout=30, verify=False)
    resp.raise_for_status()
    return resp.text


def parse_restaurants(html: str) -> List[Dict[str, str]]:
    """Parse the Eater HTML and return a list of restaurant dicts."""

    soup = BeautifulSoup(html, "lxml")

    # Eater list pages use <section class="c-mapstack__card">; keep a
    # fallback for the occasional <div class="c-mapstack__card">.
    cards = soup.find_all(["section", "div"], class_="c-mapstack__card")

    restaurants: Dict[str, Dict[str, str]] = {}

    for card in cards:
        slug = card.get("data-slug", "").strip()
        if not slug or slug in restaurants:
            continue  # skip duplicates / malformed cards

        # --- Name ----------------------------------------------------------------
        name_tag = card.find("h1")
        name = name_tag.get_text(strip=True) if name_tag else ""
        if not name:
            continue  # name is mandatory

        # --- Description ---------------------------------------------------------
        desc_tag = card.find("div", class_="c-entry-content")
        description = (
            desc_tag.find("p").get_text(strip=True)
            if desc_tag and desc_tag.find("p") else ""
        )

        # --- Address -------------------------------------------------------------
        addr_tag = card.find("div", class_="c-mapstack__address")
        address = ""
        if addr_tag:
            a = addr_tag.find("a")
            address = a.get_text(strip=True) if a else addr_tag.get_text(strip=True)

        # --- Phone ---------------------------------------------------------------
        phone_tag = card.find("div", class_="c-mapstack__phone-url")
        phone = ""
        if phone_tag:
            tel_link = phone_tag.find("a", href=re.compile(r"^tel:"))
            phone = tel_link.get_text(strip=True) if tel_link else ""

        # --- Website -------------------------------------------------------------
        site_tag = card.find("a", string=re.compile(r"visit website", re.I))
        website = site_tag["href"] if site_tag and site_tag.has_attr("href") else ""

        # --- Image ---------------------------------------------------------------
        img = ""
        photo_tag = card.find("div", class_="c-mapstack__photo")
        if photo_tag:
            span = photo_tag.find("span", class_="e-image__image")
            if span and span.has_attr("data-original"):
                img = span["data-original"]
            else:
                img_tag = photo_tag.find("img")
                if img_tag and img_tag.has_attr("src"):
                    img = img_tag["src"]

        restaurants[slug] = {
            "name": name,
            "description": description,
            "address": address,
            "phone": phone,
            "website": website,
            "image": img,
        }

    return list(restaurants.values())


def save_csv(city: str, rows: List[Dict[str, str]]) -> str:
    """Write *rows* to ``data/Restaurant_Lists_by_City/<City>_RestaurantList.csv`` and return the path."""

    # Create the "data/Restaurant_Lists_by_City" folder if it doesn't exist
    folder_path = os.path.join("data", "Restaurant_Lists_by_City")
    os.makedirs(folder_path, exist_ok=True)

    # Replace whitespace with underscores for a cleaner filename
    safe_city = re.sub(r"\s+", "_", city)
    path = os.path.join(folder_path, f"{safe_city}_RestaurantList.csv")

    fieldnames = ["name", "description", "address", "phone", "website", "image"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return os.path.abspath(path)


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape an Eater restaurant list")
    parser.add_argument("url", help="Eater \"best restaurants\" article URL")
    args = parser.parse_args()

    city = extract_city_name(args.url)
    print(f"Detected city: {city}\nDownloading article…")

    html = fetch_html(args.url)
    restaurants = parse_restaurants(html)
    print(f"Found {len(restaurants)} restaurants. Saving…")

    csv_path = save_csv(city, restaurants)
    print(f"Done! CSV saved to {csv_path}")


if __name__ == "__main__":
    main()
