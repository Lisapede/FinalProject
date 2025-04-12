# -----------------------------------------------
#  3. Restaurant Wine Menu Scraper
# -----------------------------------------------
#  Notes: THIS IS AN IMAGE AND NEED TO FIGURE OUT HOW TO EXTRACT THE TEXT
# -----------------------------------------------
import re
import pandas as pd
import pytesseract
from PIL import Image
import io
import os
import requests
try:
    from PyPDF2 import PdfReader  # For newer versions
except ImportError:
    try:
        from PyPDF2 import PdfFileReader as PdfReader  # For older versions
    except ImportError:
        # If PyPDF2 is not available, we'll handle this in the code
        pass

def extract_text_from_image(image_path):
    """Extract text from image using OCR."""
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        print(f"Error processing image: {e}")
        return ""

def extract_text_from_file(file_path):
    """Determine file type and extract text accordingly."""
    file_extension = os.path.splitext(file_path)[1].lower()
    
    # If it's an image, use OCR directly
    if file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif']:
        return extract_text_from_image(file_path)
    
    # If it's a PDF, try PyPDF2 if available
    elif file_extension == '.pdf':
        try:
            # Check if PyPDF2 is available
            if 'PdfReader' in globals():
                with open(file_path, 'rb') as file:
                    pdf = PdfReader(file)
                    text = ""
                    for page_num in range(len(pdf.pages)):
                        text += pdf.pages[page_num].extract_text() + "\n"
                    return text
            else:
                print("PyPDF2 not available. Treating PDF as an image...")
                # If PyPDF2 not available, try using OCR as a fallback
                return extract_text_from_image(file_path)
        except Exception as e:
            print(f"Error processing PDF: {e}")
            return ""
    
    # For text files
    elif file_extension in ['.txt', '.csv', '.md']:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error reading text file: {e}")
            return ""
    
    else:
        print(f"Unsupported file type: {file_extension}")
        return ""

def parse_wine_entries(text):
    """Parse wine entries from text using pattern matching."""
    wines = []
    
    # Try to identify sections
    wine_by_glass_pattern = re.compile(r'(?:WINE BY (?:THE )?GLASS|WINES? BY (?:THE )?GLASS)(.*?)(?:WINE BY (?:THE )?BOTTLE|$)', 
                                     re.DOTALL | re.IGNORECASE)
    wine_by_bottle_pattern = re.compile(r'(?:WINE BY (?:THE )?BOTTLE|WINES? BY (?:THE )?BOTTLE)(.*?)(?:$|DESSERT|SPIRITS)', 
                                     re.DOTALL | re.IGNORECASE)
    
    # Find sections
    glass_match = wine_by_glass_pattern.search(text)
    bottle_match = wine_by_bottle_pattern.search(text)
    
    glass_section = glass_match.group(1) if glass_match else ""
    bottle_section = bottle_match.group(1) if bottle_match else ""
    
    # If no sections found, process the entire text
    if not glass_section and not bottle_section:
        sections = [("Unknown", text)]
    else:
        sections = []
        if glass_section:
            sections.append(("By Glass", glass_section))
        if bottle_section:
            sections.append(("By Bottle", bottle_section))
    
    # Process each section
    for category, section_text in sections:
        # Split by new lines
        lines = section_text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or len(line) < 5:
                continue
            
            # Patterns for different formats
            # Looking for wine name, region/varietal, year, and price
            
            # Pattern 1: "Name, Region, Year Price"
            pattern1 = re.search(r'([^,]+),\s*([^,]+),\s*(\d{2,4})\s+(\d+)', line)
            
            # Pattern 2: "Name Year Price"
            pattern2 = re.search(r'(.+)\s+(\d{2,4})\s+(\d+)$', line)
            
            # Pattern 3: "Name Price"
            pattern3 = re.search(r'(.+)\s+(\d+)$', line)
            
            # Try to extract specific patterns like the example you provided
            # E.g., "22 Oenogenesis, Mataroa Amber, GR 15"
            specific_pattern = re.search(r'(\d{2})\s+([^,]+),\s*([^,]+),\s*([A-Z]{2})\s+(\d+)', line)
            
            if specific_pattern:
                wines.append({
                    'Year': specific_pattern.group(1),
                    'Producer': specific_pattern.group(2).strip(),
                    'Name': specific_pattern.group(3).strip(),
                    'Region': specific_pattern.group(4),
                    'Price': specific_pattern.group(5),
                    'Category': category
                })
            elif pattern1:
                wines.append({
                    'Name': pattern1.group(1).strip(),
                    'Region': pattern1.group(2).strip(),
                    'Year': pattern1.group(3),
                    'Price': pattern1.group(4),
                    'Category': category
                })
            elif pattern2:
                name_part = pattern2.group(1).strip()
                # Try to extract region if there's a comma
                if ',' in name_part:
                    name_region = name_part.split(',', 1)
                    name = name_region[0].strip()
                    region = name_region[1].strip()
                else:
                    name = name_part
                    region = ""
                
                wines.append({
                    'Name': name,
                    'Region': region,
                    'Year': pattern2.group(2),
                    'Price': pattern2.group(3),
                    'Category': category
                })
            elif pattern3:
                name_part = pattern3.group(1).strip()
                # Try to extract region if there's a comma
                if ',' in name_part:
                    parts = name_part.split(',')
                    if len(parts) >= 3 and parts[2].strip().isdigit():
                        # Might be format "Name, Region, Year"
                        wines.append({
                            'Name': parts[0].strip(),
                            'Region': parts[1].strip(),
                            'Year': parts[2].strip(),
                            'Price': pattern3.group(2),
                            'Category': category
                        })
                    elif len(parts) >= 2:
                        wines.append({
                            'Name': parts[0].strip(),
                            'Region': parts[1].strip(),
                            'Year': "",
                            'Price': pattern3.group(2),
                            'Category': category
                        })
                else:
                    wines.append({
                        'Name': name_part,
                        'Region': "",
                        'Year': "",
                        'Price': pattern3.group(2),
                        'Category': category
                    })
    
    return wines

def process_menu(file_path, output_csv):
    """Process menu file and save results to CSV."""
    print(f"Processing file: {file_path}")
    
    # Extract text
    text = extract_text_from_file(file_path)
    
    # Save extracted text for debugging
    with open("extracted_text.txt", "w", encoding="utf-8") as f:
        f.write(text)
    print("Extracted text saved to extracted_text.txt")
    
    # Parse wine entries
    wines = parse_wine_entries(text)
    
    # Save to CSV
    if wines:
        df = pd.DataFrame(wines)
        df.to_csv(output_csv, index=False)
        print(f"Successfully extracted {len(wines)} wine entries to {output_csv}")
    else:
        print("No wine entries found in the extracted text.")

# Example usage
if __name__ == "__main__":
    input_file = "wine_menu.pdf"  # Change to your file path
    output_csv = "wine_list.csv"
    process_menu(input_file, output_csv)