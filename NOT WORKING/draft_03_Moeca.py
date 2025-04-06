# -----------------------------------------------
#  This menu is a pdf but it is a picture of a menu
# 
# https://static1.squarespace.com/static/61a58f89a26b58039973adf7/t/67db38bd0f36e96d332fec7b/1742420159919/beverage+menu+3.5.25.pdf
# 
#  Objective: Download data from restaurant lists
# -----------------------------------------------

# pip install pdf2image pytesseract pillow pandas openpyxl

import urllib.request
import ssl
import os
import re
import pandas as pd
import pytesseract
from pdf2image import convert_from_path
from urllib.parse import urljoin

# --- Setup SSL context ---
context = ssl._create_unverified_context()

# --- PDF URL and download ---
pdf_url = "https://static1.squarespace.com/static/61a58f89a26b58039973adf7/t/67db38bd0f36e96d332fec7b/1742420159919/beverage+menu+3.5.25.pdf"
os.makedirs("data", exist_ok=True)
pdf_path = os.path.join("data", "beverage_menu.pdf")
with urllib.request.urlopen(pdf_url, context=context) as response:
    pdf_data = response.read()
with open(pdf_path, "wb") as f:
    f.write(pdf_data)
print("PDF downloaded to", pdf_path)

# --- Convert PDF pages to images using pdf2image ---
# Adjust dpi if needed; higher dpi may improve OCR accuracy
images = convert_from_path(pdf_path, dpi=300)

# --- Use pytesseract to extract text from each image ---
pdf_text = ""
for i, image in enumerate(images):
    text = pytesseract.image_to_string(image)
    pdf_text += text + "\n"
    
if not pdf_text.strip():
    print("No text extracted via OCR. Check your Tesseract installation or DPI settings.")
    exit()

# --- Split extracted text into lines ---
lines = pdf_text.splitlines()

# --- Define header sets for serving types and wine categories ---
serving_type_set = {"WINE BY THE GLASS", "BY THE GLASS", "WINE BY THE BOTTLE", "BY THE BOTTLE", "HALF BOTTLE"}
wine_category_set = {"SPARKLING", "WHITE", "RED", "WINE", "OTHER"}

# --- Initialize current state ---
current_wine_category = "Unknown"
current_serving_type = "By the Glass"  # default serving type

def parse_wine_label(label_text):
    """
    Parse a wine label string assumed to be in the format:
      [Vintage] [Producer], [Designation], [Country] [Price]
    For example: "‘22 Oenogenesis, Mataroa Amber, GR 15"
    Returns a dictionary with keys: vintage, producer, designation, country, price.
    If parsing fails, returns None.
    """
    text = label_text.strip().lstrip("$").strip()
    tokens = [t.strip() for t in text.split(",")]
    if len(tokens) < 3:
        return None
    # Token 1: should start with vintage (e.g., ‘22 or '22) followed by producer name
    m = re.match(r"^[‘']?(\d{2})\s+(.*)$", tokens[0])
    if not m:
        return None
    vintage = m.group(1)
    producer = m.group(2).strip()
    designation = tokens[1]
    # Token 3: should have a country code (2 uppercase letters) and a price number at the end
    m2 = re.search(r"([A-Z]{2})\s+(\d+)\s*$", tokens[2])
    if not m2:
        return None
    country = m2.group(1)
    price = m2.group(2)
    return {
        "vintage": vintage,
        "producer": producer,
        "designation": designation,
        "country": country,
        "price": price
    }

# --- Process each line to build rows ---
rows = []
for line in lines:
    line = line.strip()
    if not line:
        continue
    upper_line = line.upper()
    # Update state if the line exactly matches a known header
    if upper_line in serving_type_set or upper_line in wine_category_set:
        if "GLASS" in upper_line:
            current_serving_type = "By the Glass"
        elif "BOTTLE" in upper_line:
            if "HALF" in upper_line:
                current_serving_type = "Half Bottle"
            else:
                current_serving_type = "By the Bottle"
        if upper_line in wine_category_set:
            current_wine_category = upper_line
        if "WINE" in upper_line and "BY THE" in upper_line:
            if "GLASS" in upper_line:
                current_serving_type = "By the Glass"
            elif "BOTTLE" in upper_line:
                current_serving_type = "By the Bottle"
        continue

    # If the line appears to be a wine entry (starts with a vintage indicator)
    if re.match(r"^[‘']?\d{2}", line):
        parsed = parse_wine_label(line)
        if parsed:
            row = {
                "Wine Type": current_wine_category,
                "Entry Type": current_serving_type,
                "Vintage": parsed["vintage"],
                "Producer": parsed["producer"],
                "Designation": parsed["designation"],
                "Country": parsed["country"],
                "Price ($)": parsed["price"],
                "Raw Label": line
            }
            rows.append(row)

if not rows:
    print("No wine entries parsed from OCR text. Adjust parsing rules as needed.")
    exit()

# --- Save the results to an Excel file ---
df = pd.DataFrame(rows, columns=["Wine Type", "Entry Type", "Vintage", "Producer", "Designation", "Country", "Price ($)", "Raw Label"])
excel_file_path = os.path.join("data", "beverage_menu_details.xlsx")
df.to_excel(excel_file_path, index=False)
print("Beverage menu details have been saved to", excel_file_path)
