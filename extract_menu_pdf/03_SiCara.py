# -----------------------------------------------
#  3. Restaurant Wine Menu Scraper
# -----------------------------------------------
#  Notes: when it is listed directly on the website.
# -----------------------------------------------

import requests
import os
import re
import pandas as pd
from bs4 import BeautifulSoup

# URL for the Si Cara drink menu page
url = "https://sicarapizza.com/cambridge-central-square-si-cara-drink-menu"

# Download the webpage
response = requests.get(url)
html = response.text

soup = BeautifulSoup(html, "html.parser")

# Locate the Natural Wine section using its CSS class ("menu_133755")
natural_wine_section = soup.find("div", class_="menu_133755")
if not natural_wine_section:
    print("Could not locate the Natural Wine section.")
    exit()

# In this section, there are several grid items (each representing a wine category)
grid_items = natural_wine_section.find_all("div", class_="food-menu-grid-item")

wine_rows = []

# Process each grid item
for grid in grid_items:
    # Look inside a <section> element within the grid item.
    section = grid.find("section")
    if not section:
        continue

    # The header (h2) in the section indicates the wine category (e.g. Red, White, etc.)
    header = section.find("h2")
    if not header:
        continue
    wine_category = header.get_text(strip=True)

    # In this section, find all wine listings (each in a "food-item-holder")
    food_items = section.find_all("div", class_="food-item-holder")
    for item in food_items:
        # Extract Producer from the food-item-title (inside an <h3> tag)
        title_elem = item.find("div", class_="food-item-title")
        if not title_elem:
            continue
        producer_tag = title_elem.find("h3")
        if not producer_tag:
            continue
        producer = producer_tag.get_text(strip=True)

        # Extract Price by Glass from a div containing "/Glass"
        price_glass_elem = item.find("div", class_="food-price", text=re.compile(r"/Glass", re.I))
        price_by_glass = ""
        if price_glass_elem:
            price_text = price_glass_elem.get_text(strip=True)
            price_by_glass = re.sub(r"/Glass", "", price_text, flags=re.I).strip()

        # Extract Price by Bottle from the element with class "food-price multiple-price"
        price_bottle_elem = item.find("div", class_="food-price multiple-price")
        price_by_bottle = ""
        if price_bottle_elem:
            price_text = price_bottle_elem.get_text(strip=True)
            price_by_bottle = re.sub(r"/Bottle", "", price_text, flags=re.I).strip()

        # Extract Raw Description from the food-item-description
        desc_elem = item.find("div", class_="food-item-description")
        raw_description = ""
        subcategory = ""
        region = ""
        country = ""
        if desc_elem:
            raw_description = desc_elem.get_text(strip=True)
            # Split the description by commas; assume the last part is the country.
            parts = [p.strip() for p in raw_description.split(",") if p.strip()]
            if len(parts) >= 3:
                subcategory = parts[0]
                region = parts[1]
                country = parts[-1]
            elif len(parts) == 2:
                subcategory = parts[0]
                country = parts[1]
            elif len(parts) == 1:
                subcategory = parts[0]
        # Append the row
        wine_rows.append({
            "Wine Category": wine_category,
            "Producer": producer,
            "Subcategory": subcategory,
            "Region": region,
            "Country": country,
            "Price by Glass": price_by_glass,
            "Price by Bottle": price_by_bottle,
            "Raw Description": raw_description
        })

# Save the results to a CSV file
if wine_rows:
    os.makedirs("data", exist_ok=True)
    csv_file_path = os.path.join("data", "03_websitewine.csv")
    df = pd.DataFrame(wine_rows, columns=["Wine Category", "Producer", "Subcategory", "Region", "Country", "Price by Glass", "Price by Bottle", "Raw Description"])
    df.to_csv(csv_file_path, index=False)
    print("Wine listings saved to", csv_file_path)
else:
    print("No wine listings found.")
