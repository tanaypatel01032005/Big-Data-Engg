import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import time
import re
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from BDE.cli_helper import setup_cli

# ---------------- CONFIG ----------------
DEFAULT_INPUT_CSV_PATH = "D:/DAU/SEM 2/BDE/Assignment/Assignment 1/BDE/Data/dau_library_data.csv"
DEFAULT_OUTPUT_CSV_PATH = "D:/DAU/SEM 2/BDE/Assignment/Assignment 1/BDE/Data/FinalDATA.csv"

USER_AGENT = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}
DEFAULT_SLEEP_TIME = 1.5   # avoid Google blocking

# ---------------- HELPERS ----------------
def clean_text(text):
    if not text:
        return None
    text = re.sub("\s+", " ", text)
    return text.strip()


def google_search_snippet(query):
    try:
        url = f"https://www.google.com/search?q={query}"
        resp = requests.get(url, headers=USER_AGENT, timeout=10)

        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        for div in soup.find_all("div", class_="BNeawe s3v9rd AP7Wnd"):
            text = div.get_text(strip=True)
            if text:
                return clean_text(text)

    except requests.RequestException:
        return None

    return None


def fetch_book_description(title, author, isbn):
    """
    Try ISBN-based search first.
    Fall back to title + author if ISBN fails.
    """

    # 1️⃣ ISBN-based search (highest precision)
    if pd.notna(isbn) and str(isbn).strip() != "":
        isbn_query = f"ISBN {isbn} book description"
        snippet = google_search_snippet(isbn_query)
        if snippet:
            return snippet

    # 2️⃣ Fallback: Title + Author
    fallback_query = f"{title} {author} book description"
    return google_search_snippet(fallback_query)


# ---------------- PIPELINE ----------------
def run_scrape(input_csv_path, output_csv_path, sleep_time):
    print("Loading input CSV...")
    df = pd.read_csv(input_csv_path, encoding="latin1")

    print("Initial rows:", len(df))

    # Drop duplicates
    df = df.drop_duplicates(subset=[
        "Title",
        "ISBN",
        "Author_Editor",
        "Edition_Volume",
        "Place_Publisher",
        "Year",
        "Pages",
        "Class_No"
    ])

    print("After dedup:", len(df))

    # Ensure description column exists
    if "description" not in df.columns:
        df["description"] = None

    # Rows needing description
    missing_df = df[
        df["description"].isna() |
        (df["description"].astype(str).str.strip() == "") |
        (df["description"] == "Not Found")
    ]

    print("Rows needing description:", len(missing_df))

    # Scrape descriptions
    for idx in tqdm(missing_df.index, desc="Scraping"):
        title = df.at[idx, "Title"]
        author = df.at[idx, "Author_Editor"]
        isbn = df.at[idx, "ISBN"]

        snippet = fetch_book_description(title, author, isbn)

        if snippet:
            df.at[idx, "description"] = snippet
        else:
            df.at[idx, "description"] = "Not Found"

        time.sleep(sleep_time)

    # Write to OUTPUT file
    df.to_csv(output_csv_path, index=False, encoding="latin1")
    print("Scraping completed. Output saved to:", output_csv_path)


# ---------------- ENTRY ----------------
if __name__ == "__main__":
    args = setup_cli(
        "Scrape book descriptions from Google based on a CSV file.",
        [
            {'name': '--input_csv', 'kwargs': {'type': str, 'default': DEFAULT_INPUT_CSV_PATH, 'help': 'Path to the input CSV file containing book data'}},
            {'name': '--output_csv', 'kwargs': {'type': str, 'default': DEFAULT_OUTPUT_CSV_PATH, 'help': 'Path to the output CSV file to save the results'}},
            {'name': '--sleep_time', 'kwargs': {'type': float, 'default': DEFAULT_SLEEP_TIME, 'help': 'Time to sleep between requests to avoid being blocked'}}
        ]
    )
    run_scrape(args.input_csv, args.output_csv, args.sleep_time)
