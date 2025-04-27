import csv
import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Input and output file paths
INPUT_FILE = "/workspaces/codespaces-blank//Restaurant_Data/wine_menu_extracted.csv"
OUTPUT_FILE = "processed_wine_menu.csv"

# Define the output CSV headers
HEADERS = [
    "City",
    "Restaurant",
    "Menu Wine Name",
    "Brand",
    "Wine Name",
    "Vintage",
    "Region",
    "State",
    "Country",
    "Wine Type",
    "Varietal",
    "Body",
    "ABV (Alcohol by Volume)",
    "Taste Profile",
    "Sweetness Level",
    "Tannin Level",
    "Acidity",
    "Price",
    "Price by Glass",
    "Price by Bottle",
    "Sources",
]

# Function to call the LLM
def call_llm(row):
    """
    Calls the LLM to process a row and return structured data.
    """
    prompt = f"""
You are a wine data expert. Take the following row of wine menu data and split it into the following columns:
{', '.join(HEADERS)}

Row: {row}

Return ONLY a valid, minified JSON object with the exact schema:
{{
    "City": string|null,
    "Restaurant": string|null,
    "Menu Wine Name": string|null,
    "Brand": string|null,
    "Wine Name": string|null,
    "Vintage": string|null,
    "Region": string|null,
    "State": string|null,
    "Country": string|null,
    "Wine Type": string|null,
    "Varietal": string|null,
    "Body": string|null,
    "ABV (Alcohol by Volume)": string|null,
    "Taste Profile": string|null,
    "Sweetness Level": string|null,
    "Tannin Level": string|null,
    "Acidity": string|null,
    "Price": string|null,
    "Price by Glass": string|null,
    "Price by Bottle": string|null,
    "Sources": string[]
}}
Use null for missing values. Do not add extra keys or comments.
    """.strip()

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        content = response["choices"][0]["message"]["content"]
        return eval(content)  # Convert the JSON string to a Python dictionary
    except Exception as e:
        print(f"Error calling LLM for row: {row}\n{e}")
        return {header: None for header in HEADERS}  # Return empty values if LLM fails


# Function to process the CSV file
def process_csv(input_file, output_file):
    """
    Processes the input CSV file and writes the structured data to the output CSV file.
    """
    with open(input_file, "r", encoding="utf-8") as infile, open(
        output_file, "w", newline="", encoding="utf-8"
    ) as outfile:
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=HEADERS)
        writer.writeheader()

        for row in reader:
            # Combine the row into a single string for the LLM
            row_data = f"{row['city']}, {row['restaurant']}, {row['wine_section']}, {row['wine_name']}"
            print(f"Processing row: {row_data}")

            # Call the LLM to process the row
            structured_data = call_llm(row_data)

            # Write the structured data to the output file
            writer.writerow(structured_data)


if __name__ == "__main__":
    # Ensure the OpenAI API key is set
    if not openai.api_key:
        print("Error: OpenAI API key not found. Please set it in the .env file.")
        exit(1)

    # Process the CSV file
    print(f"Processing file: {INPUT_FILE}")
    process_csv(INPUT_FILE, OUTPUT_FILE)
    print(f"Processed data saved to: {OUTPUT_FILE}")