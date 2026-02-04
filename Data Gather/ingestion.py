import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import time
import re
import sys
import os
from urllib.parse import quote_plus

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cli_helper import setup_cli, check_help

# Check for --help early
check_help("Scrape book descriptions using staged multi-source enrichment.")

# ---------------- CONFIG ----------------
DEFAULT_INPUT_CSV_PATH = "D:\DAU\SEM 2\BDE\Assignment\Assignment 1\Assignment 1\Big-Data-Engg\Data\dau_library_data.csv"
DEFAULT_OUTPUT_CSV_PATH = "D:\DAU\SEM 2\BDE\Assignment\Assignment 1\Assignment 1\Big-Data-Engg\Data\FinalDATA.csv"

USER_AGENT = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

DEFAULT_SLEEP_TIME = 1.2

MISSING_VALUES = [
    "Not Found",
    "ISBN Not Matched",
    "Description Not Available",
    None,
    ""
]

# ---------------- HELPERS ----------------
def clean_isbn(isbn):
    return re.sub(r"[^0-9Xx]", "", str(isbn))


def clean_text(text):
    if pd.isna(text):
        return ""
    text = str(text).lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


# ---------------- FETCH FUNCTIONS ----------------
def fetch_openlibrary_description(isbn):
    if not isbn:
        return None

    try:
        url = f"https://openlibrary.org/isbn/{isbn}"
        r = requests.get(url, headers=USER_AGENT, timeout=10)

        if r.status_code != 200:
            return None

        soup = BeautifulSoup(r.text, "html.parser")
        p = soup.select_one("div.book-description div.read-more__content p")

        return p.get_text(strip=True) if p else None

    except requests.RequestException:
        return None


def fetch_google_html_description(isbn):
    if not isbn:
        return None

    try:
        url = f"https://books.google.com/books?vid=ISBN{isbn}"
        r = requests.get(url, headers=USER_AGENT, timeout=10)

        if r.status_code != 200:
            return None

        soup = BeautifulSoup(r.text, "html.parser")
        div = soup.find("div", id="synopsis")

        return div.get_text(separator=" ", strip=True) if div else None

    except requests.RequestException:
        return None


def google_books_api_search(query):
    try:
        url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=1"
        res = requests.get(url, timeout=10).json()

        items = res.get("items")
        if not items:
            return None

        return items[0].get("volumeInfo", {}).get("description")

    except Exception:
        return None


def fetch_google_api_fallback(title, author):
    clean_title = clean_text(title)
    clean_author = clean_text(author)

    queries = [
        f"intitle:{clean_title}+inauthor:{clean_author}",
        f"intitle:{clean_title}"
    ]

    for q in queries:
        desc = google_books_api_search(quote_plus(q))
        if desc and len(desc) > 50:
            return desc

    return None


# ---------------- PIPELINE ----------------
def run_scrape(input, output, sleep_time):
    print("🔹 Loading input CSV...")
    df = pd.read_csv(input, encoding="latin1")

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

    if "description" not in df.columns:
        df["description"] = "Not Found"

    # ---------- STAGE 1: OpenLibrary ----------
    print("📚 Stage 1: OpenLibrary enrichment")
    missing_idx = df[df["description"].isin(MISSING_VALUES)].index

    for idx in tqdm(missing_idx, desc="OpenLibrary"):
        isbn = clean_isbn(df.at[idx, "ISBN"])
        desc = fetch_openlibrary_description(isbn)

        if desc:
            df.at[idx, "description"] = desc

        time.sleep(sleep_time)

    # ---------- STAGE 2: Google Books HTML ----------
    print("📘 Stage 2: Google Books HTML enrichment")
    missing_idx = df[df["description"].isin(MISSING_VALUES)].index

    for idx in tqdm(missing_idx, desc="Google HTML"):
        isbn = clean_isbn(df.at[idx, "ISBN"])
        desc = fetch_google_html_description(isbn)

        if desc:
            df.at[idx, "description"] = desc

        time.sleep(sleep_time)

    # ---------- STAGE 3: Google Books API ----------
    print("📗 Stage 3: Google Books API fallback")
    missing_idx = df[df["description"].isin(MISSING_VALUES)].index

    for idx in tqdm(missing_idx, desc="Google API"):
        title = df.at[idx, "Title"]
        author = df.at[idx, "Author_Editor"]

        desc = fetch_google_api_fallback(title, author)

        if desc:
            df.at[idx, "description"] = desc

        time.sleep(sleep_time)

    df.to_csv(output, index=False, encoding="latin1")
    print("✅ Enrichment completed")
    print("📁 Output saved to:", output)


# ---------------- ENTRY ----------------
if __name__ == "__main__":
    args = setup_cli(
        "Scrape book descriptions using staged multi-source enrichment.",
        [
            {
                'name': '--input_csv',
                'kwargs': {
                    'type': str,
                    'default': DEFAULT_INPUT_CSV_PATH,
                    'help': 'Path to input CSV file'
                }
            },
            {
                'name': '--output_csv',
                'kwargs': {
                    'type': str,
                    'default': DEFAULT_OUTPUT_CSV_PATH,
                    'help': 'Path to output CSV file'
                }
            },
            {
                'name': '--sleep_time',
                'kwargs': {
                    'type': float,
                    'default': DEFAULT_SLEEP_TIME,
                    'help': 'Delay between requests'
                }
            }
        ]
    )

    run_scrape(args.input_csv, args.output_csv, args.sleep_time)
