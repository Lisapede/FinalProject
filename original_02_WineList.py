# -----------------------------------------------
#  2. Wine list:
# ------------------------------------------------
#  Objective: Pull the wine menu off of the restaurant's website
#  Notes: need to fix this since it is not finding all of the restaurant wine menus
# -----------------------------------------------

import urllib.request
import ssl
import os
import csv
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Setup SSL context
context = ssl._create_unverified_context()

def pull(url):
    """Fetch and decode HTML content from a URL."""
    response = urllib.request.urlopen(url, context=context).read()
    return response.decode('utf-8')

def find_menu_link(homepage_soup, base_url):
    """
    Search for an anchor tag that likely points to a drinks or wine menu.
    Looks for keywords 'menu' plus 'wine', 'drink', or 'beverage' in the link text or href.
    Returns the absolute URL if found.
    """
    candidates = []
    for a in homepage_soup.find_all('a', href=True):
        text = a.get_text(strip=True).lower()
        href = a['href'].lower()
        if "menu" in text and ("wine" in text or "drink" in text or "beverage" in text):
            candidates.append(a)
        elif "menu" in href and ("wine" in href or "drink" in href or "beverage" in href):
            candidates.append(a)
    if candidates:
        # Return the absolute URL of the first candidate
        return urljoin(base_url, candidates[0]['href'])
    return None

def extract_wine_details(menu_html):
    """
    Extract text lines mentioning 'wine' from the menu page.
    Returns a semicolon-separated string of unique lines.
    """
    soup = BeautifulSoup(menu_html, 'lxml')
    text = soup.get_text(separator='\n')
    wine_lines = []
    for line in text.splitlines():
        if "wine" in line.lower():
            wine_lines.append(line.strip())
    wine_lines = list(filter(None, set(wine_lines)))  # remove duplicates and empties
    return "; ".join(wine_lines) if wine_lines else "No wine details found"

# Read the RestaurantList.csv file (created by your earlier code)
restaurants_csv = os.path.join('data', 'RestaurantList.csv')
restaurants = []
with open(restaurants_csv, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        restaurants.append(row)

output = []

# Process each restaurant website to find a wine/drinks menu
for restaurant in restaurants:
    name = restaurant.get("name", "Unknown")
    website = restaurant.get("website", "")
    if not website or website == "No website found":
        output.append({
            "name": name,
            "website": website,
            "menu_url": "N/A",
            "wine_details": "No website"
        })
        continue

    print(f"Processing {name} - {website}")
    try:
        homepage_html = pull(website)
    except Exception as e:
        output.append({
            "name": name,
            "website": website,
            "menu_url": "Error",
            "wine_details": f"Error fetching homepage: {e}"
        })
        continue

    homepage_soup = BeautifulSoup(homepage_html, 'lxml')
    menu_url = find_menu_link(homepage_soup, website)
    if not menu_url:
        print(f"No menu link found for {name}")
        output.append({
            "name": name,
            "website": website,
            "menu_url": "N/A",
            "wine_details": "No menu link found"
        })
        continue

    print(f"Found menu link for {name}: {menu_url}")
    try:
        menu_html = pull(menu_url)
    except Exception as e:
        output.append({
            "name": name,
            "website": website,
            "menu_url": menu_url,
            "wine_details": f"Error fetching menu: {e}"
        })
        continue

    wine_details = extract_wine_details(menu_html)
    output.append({
        "name": name,
        "website": website,
        "menu_url": menu_url,
        "wine_details": wine_details
    })

# Write the results to a new CSV file.
output_csv = os.path.join('data', 'restaurant_wine_menus.csv')
with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ["name", "website", "menu_url", "wine_details"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for row in output:
        writer.writerow(row)

print("Wine menu details have been saved to", output_csv)
