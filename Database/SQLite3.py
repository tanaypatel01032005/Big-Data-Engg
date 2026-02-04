import sqlite3
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cli_helper import setup_cli, check_help

# Check for --help early
check_help("Script to import CSV data into SQLite database.")

# Read CSV
df = pd.read_csv("Data/FinalDATA.csv")

# SQLite connection
conn = sqlite3.connect("db.sqlite3")
cursor = conn.cursor()
print(os.path.abspath("db.sqlite3"))
# Create table with ALL columns
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
    description TEXT
)
""")

for _, row in df.iterrows():
    cursor.execute("""
    INSERT OR IGNORE INTO books
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        row["description"]
    ))

conn.commit()
conn.close()

print("FULL CSV copied into SQLite (all columns, no changes)")

if __name__ == "__main__":
    args = setup_cli(
        "Script to import CSV data into SQLite database.",
        []
    )
