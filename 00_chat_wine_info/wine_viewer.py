import sqlite3
import pandas as pd
import sqlite3
from prettytable import PrettyTable

# Connect to the database
conn = sqlite3.connect('/workspaces/codespaces-blank/00_chat_wine_info/wine.db')
cursor = conn.cursor() 

# Get column names
cursor.execute("PRAGMA table_info(wines)")
columns = [col[1] for col in cursor.fetchall()]

# Create a pretty table
table = PrettyTable()
table.field_names = ["Producer", "Wine Name", "Vintage", "Region", "Country", "Type", "Price"]

# Execute the query
cursor.execute("SELECT producer, wine_name, vintage_hint, region, country, wine_type, price FROM wines LIMIT 10")
rows = cursor.fetchall()

# Add rows to the table
for row in rows:
    table.add_row(row)

# Configure the table appearance
table.align = "l"  # Left-align text
table.max_width = 30  # Limit column width
table.border = True
table.header_style = "upper"

# Print the table
print(table)

conn.close()

# Let's use pandas to make the data easier to view
# df = pd.read_sql_query("SELECT * FROM wines LIMIT 10", conn)

# Display basic stats about the table
# print(f"Total wine records: {pd.read_sql_query('SELECT COUNT(*) FROM wines', conn).iloc[0,0]}")

# Show the data in a more readable format
# print("\nSample wines:")
# print(df)

# You could also look at specific categories
# print("\nWine types available:")
# wine_types = pd.read_sql_query("SELECT DISTINCT wine_type FROM wines", conn)
# print(wine_types)

# print("\nCountries represented:")
# countries = pd.read_sql_query("SELECT DISTINCT country FROM wines", conn)
# print(countries)

# conn.close()