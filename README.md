# ____________________________________
# Final Project
  This project helps local wine producers find out what restaurants are selling their wine.
# ____________________________________

## How does it work
  The wine producer enters in their wine into the website and the website displays the restaurants that carry that wine.

# ____________________________________
# Backend to set up Restaurant Database
# ____________________________________

<Restaurant Scripts>

## 01_RestaurantList.py
This step loads the restaurants from an online Top Rated restaurants list from a particular city.

Process:
Download the article HTML.
Parse the page to extract:
- Restaurant name
- Short description
- Address
- Phone number
- Website link
- Restaurant image link

Save all this into a CSV:
data/Restaurant_Lists_by_City/<City>_RestaurantList.csv


## 02_WineList.py
Take those restaurant CSVs, visit each restaurant's website, hunt for wine lists (or menus mentioning wine), and save the findings.

Input:
CSVs created from 01_RestaurantList.py (like Boston_RestaurantList.csv)

Process:
For each restaurant:
- Visit their website (if available).
- Look for links to:
    - Wine menus (preferred)
    - General menus (backup)
    - PDF menus (if HTML fails)
- Download/save either:
    - HTML menus locally
    - PDF menus locally
- Record the wine menu URL (if found), or log failure if no wine menu is found.

Output: A CSV file: data/restaurant_wine_offerings. 

The output is saved in the <Restaurant Data> Folder under the name of the city that the restaurants are located
ex. <Boston_Menus>. The portion of the restaurant's website that contains the wine menu is extracted and saved 
in the folder and labeled <City_RestaurantName.html>

## 03_WineMenuExtractor.py




# ____________________________________
# Calling LLM 
# ____________________________________

<00_chat_wine_info>

## 01_RestaurantList.py
This step loads the restaurants from an online Top Rated restaurants list from a particular city.
The output is saved in the <Restaurant Data> Folder under the name of the city that the restaurants are located
ex. <Boston_Menus>. The portion of the restaurant's website that contains the wine menu is extracted and saved 
in the folder and labeled <City_RestaurantName.html>

## 02_WineList.py

## 03_WineMenuExtractor.py

Parse the downloaded wine menus (PDF or HTML) for each restaurant and extract individual wine listings into a structured CSV file.

Input:
- Wine menu files from data/{City}_Menus/ folders
(These files were downloaded by 02_WineList.py.)

Process:
- Open each downloaded menu (both .html and .pdf formats).
- Read the full text of the menu.
- Search for sections like:
    - By the Glass
    - By the Bottle
    - Glass Pours
- Within each section, identify lines that:
    - Contain wine-related keywords (Chardonnay, Cabernet, Riesling, etc.)
    - Look like menu entries (especially if they end with prices, like "$15").
- For each wine entry found, capture:
    - City
    - Restaurant name
    - Wine section
    - Full wine name (e.g., "Duckhorn Chardonnay Napa Valley $18")
- Save all extracted wine entries into a master CSV file.

Output example: A CSV file called wine_menu_extracted.csv

# ____________________________________
# Website 
# ____________________________________
