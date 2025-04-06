import sqlite3
import csv

# Connect to the database
conn = sqlite3.connect('/workspaces/codespaces-blank/00_chat_wine_info/wine.db')
cursor = conn.cursor()

# Step 2: Examine the structure of the "wines" table
print("Column information for 'wines' table:")
cursor.execute("PRAGMA table_info(wines);")
columns = cursor.fetchall()
for column in columns:
    print(column)

# Get column names for CSV header
column_names = [column[1] for column in columns]

# Step 3: Query data from the "wines" table
print("\nSample data from 'wines' table:")
cursor.execute("SELECT * FROM wines")  # Removed LIMIT to export all data
rows = cursor.fetchall()
for row in rows[:5]:  # Only print first 5 rows to console
    print(row)

# Export to CSV file
csv_filename = 'wines_export.csv'
with open(csv_filename, 'w', newline='', encoding='utf-8') as csv_file:
    csv_writer = csv.writer(csv_file)
    
    # Write header row
    csv_writer.writerow(column_names)
    
    # Write data rows
    csv_writer.writerows(rows)

print(f"\nData exported successfully to {csv_filename}")

conn.close()