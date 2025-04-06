# -----------------------------------------------
#  1. Restaurant list:
# -------------------------------------------------
#  Objective: Download data from restaurant lists
# -----------------------------------------------

# pip install lxml

import urllib.request
import ssl
import os
import csv
from bs4 import BeautifulSoup

# Workaround for SSL certificate errors
context = ssl._create_unverified_context()

# URL for the Boston Eater "38 Best Restaurants" page
main_url = 'https://boston.eater.com/maps/best-restaurants-boston-38'

def pull(url):
    """Fetch and decode HTML content from a URL."""
    response = urllib.request.urlopen(url, context=context).read()
    return response.decode('utf-8')

def store(data, file):
    """Store raw data in the data folder."""
    os.makedirs('data', exist_ok=True)
    with open(os.path.join('data', file), 'w', encoding='utf-8') as f:
        f.write(data)
    print('File saved as ' + file)

# Fetch the main page content and store it for debugging if needed
main_page_content = pull(main_url)
store(main_page_content, 'raw.html')

# Parse the main page HTML
soup = BeautifulSoup(main_page_content, 'lxml')

# Find all restaurant cards; each card is a <section> with class "c-mapstack__card"
cards = soup.find_all('section', class_='c-mapstack__card')
print("Found", len(cards), "restaurant cards.")

# Use a dictionary to track unique restaurants by their 'data-slug'
unique_restaurants = {}

for card in cards:
    # Use the 'data-slug' attribute as a unique identifier (if available)
    slug = card.get("data-slug", "").strip()
    if not slug:
        # Skip cards without a valid slug
        continue

    # If we already have an entry for this slug, skip it.
    if slug in unique_restaurants:
        continue

    # Restaurant Name: located in the <h1> tag inside the card header.
    name = "No name found"
    header_div = card.find('div', class_='c-mapstack__card-hed')
    if header_div:
        h1 = header_div.find('h1')
        if h1:
            name = h1.get_text(strip=True)
    
    # Skip cards that do not have a valid restaurant name.
    if name == "No name found":
        continue

    # Description: found in the <p> tag within the "c-entry-content" container.
    description = "No description found"
    content_div = card.find('div', class_='c-entry-content')
    if content_div:
        p = content_div.find('p')
        if p:
            description = p.get_text(strip=True)
    
    # Address: found in the <div class="c-mapstack__address">, typically inside an <a> tag.
    address = "No address found"
    addr_div = card.find('div', class_='c-mapstack__address')
    if addr_div:
        a_addr = addr_div.find('a')
        if a_addr:
            address = a_addr.get_text(strip=True)
        else:
            address = addr_div.get_text(strip=True)
    
    # Phone Number: located in the <div class="c-mapstack__phone-url">, look for an <a> tag with a "tel:" link.
    phone = "No phone found"
    phone_div = card.find('div', class_='c-mapstack__phone-url')
    if phone_div:
        a_phone = phone_div.find('a', href=lambda x: x and x.startswith('tel:'))
        if a_phone:
            phone = a_phone.get_text(strip=True)
    
    # Website: look for an <a> tag with visible text like "Visit Website".
    website = "No website found"
    website_a = card.find('a', string=lambda s: s and "Visit Website" in s)
    if website_a and website_a.has_attr('href'):
        website = website_a['href']
    
    # Image: Extract the primary image URL from the <span class="e-image__image"> element's data-original attribute.
    image = "No image found"
    photo_div = card.find('div', class_='c-mapstack__photo')
    if photo_div:
        span_img = photo_div.find('span', class_='e-image__image')
        if span_img and span_img.has_attr('data-original'):
            image = span_img['data-original']
        else:
            # Fallback: get the src from an <img> tag if available.
            img = photo_div.find('img')
            if img and img.has_attr('src'):
                image = img['src']
    
    # Store the restaurant details in the dictionary, keyed by slug.
    unique_restaurants[slug] = {
        "name": name,
        "description": description,
        "address": address,
        "phone": phone,
        "website": website,
        "image": image
    }

# Convert unique restaurants to a list for CSV output.
restaurants = list(unique_restaurants.values())

# Save the extracted restaurant data to a CSV file.
os.makedirs('data', exist_ok=True)
csv_file_path = os.path.join('data', 'RestaurantList.csv')
with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ["name", "description", "address", "phone", "website", "image"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for restaurant in restaurants:
        writer.writerow(restaurant)

print("Restaurant data has been fetched and saved to", csv_file_path)
