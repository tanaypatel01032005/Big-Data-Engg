import sqlite3
import pandas as pd

# Read CSV
df = pd.read_csv("D:/DAU/SEM 2/BDE/Assignment/Assignment 1/BDE/Data/FinalDATA.csv")


# SQLite connection
conn = sqlite3.connect("db.sqlite3")
cursor = conn.cursor()
import os
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
