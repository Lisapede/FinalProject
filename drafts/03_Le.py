import requests
import io
import pandas as pd
import re
import pytesseract
from PIL import Image
try:
    from PyPDF2 import PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfFileReader as PdfReader
    except ImportError:
        print("PyPDF2 not available. Install with: pip install PyPDF2")

def download_pdf(url):
    """Download PDF from URL"""
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check for HTTP errors
        print(f"Successfully downloaded PDF from {url}")
        return io.BytesIO(response.content)
    except Exception as e:
        print(f"Error downloading PDF: {e}")
        return None

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF"""
    text = ""
    try:
        pdf = PdfReader(pdf_file)
        for page_num in range(len(pdf.pages)):
            page = pdf.pages[page_num]
            page_text = page.extract_text()
            text += page_text + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

def parse_spirit_list(text):
    """Parse spirit list text into structured data"""
    # First save the text for debugging
    with open("extracted_text.txt", "w", encoding="utf-8") as f:
        f.write(text)
    
    # Split text into sections
    sections = []
    current_section = {"name": "Unknown", "items": []}
    lines = text.split('\n')
    
    # Process line by line
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if this is a section header (all uppercase, shorter than 40 chars)
        if line.isupper() and len(line) < 40 and not re.search(r'\d', line):
            # Save previous section if it has items
            if current_section["items"]:
                sections.append(current_section)
            # Start new section
            current_section = {"name": line, "items": []}
        else:
            # Try to parse as an item with price
            # Pattern: Item name followed by price (number)
            price_match = re.search(r'(.*)\s+(\d+)$', line)
            
            if price_match:
                name = price_match.group(1).strip()
                price = price_match.group(2).strip()
                
                # Extract any details from the name (like year, region)
                details = {}
                
                # Look for year
                year_match = re.search(r'\b(19|20)\d{2}\b', name)
                if year_match:
                    details["year"] = year_match.group(0)
                
                # Add item to current section
                current_section["items"].append({
                    "name": name,
                    "price": price,
                    "section": current_section["name"],
                    **details
                })
            else:
                # If no price found, might be a continuation or description
                # Attach to the previous item if there is one
                if current_section["items"]:
                    prev_item = current_section["items"][-1]
                    if "description" not in prev_item:
                        prev_item["description"] = line
                    else:
                        prev_item["description"] += " " + line
    
    # Add the last section
    if current_section["items"]:
        sections.append(current_section)
    
    # Flatten sections into items
    items = []
    for section in sections:
        for item in section["items"]:
            items.append(item)
    
    return items

def main():
    url = "https://static1.squarespace.com/static/604a17fbc98ac75732163979/t/65bac6f2ba8e3e600af3e9c5/1706739442486/Spirit+List+1.30.24.pdf"
    output_file = "restaurant_wine_list.csv"
    
    print(f"Downloading PDF from {url}")
    pdf_file = download_pdf(url)
    
    if pdf_file:
        print("Extracting text from PDF")
        text = extract_text_from_pdf(pdf_file)
        
        print("Parsing spirit list")
        items = parse_spirit_list(text)
        
        print(f"Found {len(items)} items")
        
        # Convert to DataFrame and save to CSV
        df = pd.DataFrame(items)
        df.to_csv(output_file, index=False)
        print(f"Saved to {output_file}")

if __name__ == "__main__":
    main()