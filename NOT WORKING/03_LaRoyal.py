# -----------------------------------------------
#  3. Testing how to pull the wine off of La Royal
# ------------------------------------------------
# Objective: Pull the wine menu off of the restaurant's website
# https://www.laroyalcambridge.com/menu
#
#  Notes: NOT WORKING
# -----------------------------------------------
import requests
import os
import pandas as pd
from bs4 import BeautifulSoup

# Define CATEGORY_WORDS for filtering wine categories
CATEGORY_WORDS = ["WINE", "RED", "WHITE", "SPARKLING", "ROSE"]

def tidy_price(price_text):
    """Clean up price text and extract numeric value."""
    return price_text.replace("$", "").strip()

def split_description(description):
    """Split the description into subcategory, region, country, and price."""
    parts = description.split(", ")
    subcat = parts[0] if len(parts) > 0 else ""
    region = parts[1] if len(parts) > 1 else ""
    country = parts[2] if len(parts) > 2 else ""
    tail_price = parts[-1] if len(parts) > 3 else ""
    return subcat, region, country, tail_price

def scrape_la_royal_wine_menu():
    # URL for the La Royal Cambridge menu page
    url = "https://www.laroyalcambridge.com/menu"
    restaurant_name = "LaRoyal"  # Name to use in the filename
    
    # Set up headers to mimic a browser request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
    }
    
    # Fetch the webpage content
    print(f"Fetching content from {url}...")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
        return [], restaurant_name
        
    # Parse the HTML content
    soup = BeautifulSoup(response.text, "html.parser")
    print("Successfully retrieved webpage content")
    
    # Print all headings to help debug
    print("All headers on the page:")
    for heading in soup.find_all(['h1', 'h2', 'h3', 'h4']):
        print(f"  {heading.name}: {heading.get_text()}")
    
    # Look for any divs that might contain menu items
    menu_sections = soup.find_all("div", class_=lambda c: c and any(term in str(c) for term in ["menu", "section", "food", "item", "grid"]))
    
    wine_rows = []  # Initialize list to store wine data
    
    # Every grid item with a <section><h2> whose text matches a wine category
    for grid in soup.select("div.food-menu-grid-item section"):
        h2 = grid.find("h2")
        if not h2:
            continue
        category = h2.get_text(strip=True).upper()
        if not any(word in category for word in CATEGORY_WORDS):
            continue

        for item in grid.select("div.food-item-holder"):
            # ---- producer ------------------------------------------------------
            h3 = item.select_one("div.food-item-title h3")
            if not h3:
                continue
            producer = h3.get_text(strip=True)

            # ---- prices from explicit <div class="food-price …"> --------------
            price_by_glass = price_by_bottle = ""
            for pdiv in item.select("div.food-price"):
                txt = pdiv.get_text(strip=True)
                if "glass" in txt.lower():
                    price_by_glass = tidy_price(txt)
                elif "bottle" in txt.lower():
                    price_by_bottle = tidy_price(txt)

            # ---- description & fallback price/country -------------------------
            desc_div = item.select_one("div.food-item-description")
            raw_desc = desc_div.get_text(strip=True) if desc_div else ""
            subcat, region, country, tail_price = split_description(raw_desc)

            # if explicit “/Glass” price missing, use the tail price
            if not price_by_glass and tail_price:
                price_by_glass = tail_price

            wine_rows.append(
                {
                    "Wine Category": category,
                    "Producer": producer,
                    "Subcategory": subcat,
                    "Region": region,
                    "Country": country,
                    "Price by Glass": price_by_glass,
                    "Price by Bottle": price_by_bottle,
                    "Raw Description": raw_desc,
                }
            )
    
    print(f"Found {len(wine_rows)} wine listings.")
    return wine_rows, restaurant_name

def save_to_csv(data, restaurant_name):
    # Create the filename in the format "03_restaurantname.csv"
    filename = f"03_{restaurant_name}.csv"
    
    # Create the data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    file_path = os.path.join("data", filename)
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(data, columns=[
        "Wine Category",
        "Producer",
        "Subcategory",
        "Region",
        "Country",
        "Price by Glass",
        "Price by Bottle",
        "Raw Description"
    ])
    
    df.to_csv(file_path, index=False)
    print(f"Data saved to {file_path}")
    return file_path

if __name__ == "__main__":
    print("Starting La Royal wine menu scraper...")
    wine_data, restaurant_name = scrape_la_royal_wine_menu()
    
    if wine_data:
        save_to_csv(wine_data, restaurant_name)
    else:
        print("No data to save.")