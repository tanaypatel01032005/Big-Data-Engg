import sqlite3
import pandas as pd
import sys
import os
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cli_helper import setup_cli, check_help

# Check for --help early
check_help("Script to import CSV data into SQLite database.")

# Resolve paths relative to project root
BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "Data" / "FinalDATA.csv"
DB_PATH = BASE_DIR / "Database" / "db.sqlite3"

# Read CSV
df = pd.read_csv(CSV_PATH)

# SQLite connection
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
print(f"Database path: {DB_PATH}")

# Drop existing table to recreate with new columns
cursor.execute("DROP TABLE IF EXISTS books")

# Create table with ALL columns including image_url and book_url
cursor.execute("""
CREATE TABLE IF NOT EXISTS books (
    Acc_Date TEXT,
    Acc_No INTEGER PRIMARY KEY,
    Title TEXT,
    ISBN INTEGER,
    Author_Editor TEXT,
    Edition_Volume TEXT,
    Place_Publisher TEXT,
    Year INTEGER,
    Pages TEXT,
    Class_No TEXT,
    description TEXT,
    image_url TEXT,
    book_url TEXT
)
""")

for _, row in df.iterrows():
    cursor.execute("""
    INSERT OR IGNORE INTO books
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        row["Acc_Date"],
        int(row["Acc_No"]),
        row["Title"],
        str(row["ISBN"]),
        row["Author_Editor"],
        row["Edition_Volume"],
        row["Place_Publisher"],
        row["Year"],
        row["Pages"],
        row["Class_No"],
        row["description"],
        row.get("image_url", None),
        row.get("book_url", None),
    ))

conn.commit()
conn.close()

print("FULL CSV copied into SQLite (all columns including image_url and book_url)")

if __name__ == "__main__":
    args = setup_cli(
        "Script to import CSV data into SQLite database.",
        []
    )
