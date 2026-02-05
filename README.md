# BookFinder: University Library Enrichment System

---

## 📖 Introduction: The Problem & The Solution

**The Problem:**
University library datasets are often incomplete. Our raw data file (`dau_library_data.csv`) contained thousands of books with technical details (ISBN, Author, Year) but **missing descriptions**. Without a description, a library user can't know what a book is actually about.

**The Solution:**
**BookFinder** is an automated pipeline that fixes this. It acts as a "digital librarian" that:

1. **Reads** the messy library data
2. **Searches** external sources for missing book summaries
3. **Saves** the enriched data into a structured database
4. **Serves** the clean data to other applications via a website API

---

## 🏗️ Architecture: How It Works

This project uses an **ETL (Extract, Transform, Load)** pipeline approach. We don't do everything in one file; responsibilities are clearly separated into distinct stages.

```mermaid
graph LR
    A[Raw CSV Data] -->|ingestion.py| B(Enrichment Engine)
    B -->|SQLite3.py| C[SQLite Database]
    C -->|api.py| D[FastAPI Server]
    D -->|JSON Data| E[End User]
```

---

## 🧠 Core Components

### 1. The "Researcher" (`ingestion.py`)

**What it does:**
This script is the intelligence layer of the system.

**How it works:**
It reads the CSV file row by row and applies a **multi-stage enrichment strategy** for records with missing descriptions.

The enrichment follows a deterministic priority order:

1. **OpenLibrary lookup (ISBN-based)**
2. **Google Books HTML scraping (ISBN-based)**
3. **Google Books API fallback (title + author)**

Each subsequent method is used only if the previous one fails, ensuring high precision while maximizing coverage.
Requests are rate-limited to avoid blocking.

**Why we do this:**
Manual enrichment of thousands of records is infeasible. Real-world library data contains missing or malformed ISBNs, so a single source is insufficient. A fallback-based automated approach is required.

---

### 2. The "Librarian" (`SQLite3.py`)

**What it does:**
Handles persistent data storage.

**How it works:**
Takes the enriched CSV and loads it into a structured **relational SQLite database** (`db.sqlite3`).

**Why we do this:**
CSV files are inefficient for querying. A relational database enables fast lookups by ISBN or accession number and supports future extensions.

---

### 3. The "Receptionist" (`api.py`)

**What it does:**
Acts as the public interface to the system.

**How it works:**
Runs a FastAPI web server that executes SQL queries against the database and returns results in JSON format.

**Why we do this:**
Users and applications should not directly access database files. The API provides a safe, read-only access layer.

---

## 🛠️ Key Technical Concepts Learned

This project demonstrates several core software engineering skills:

* **Web Scraping:** Using `BeautifulSoup` to extract information from HTML pages
* **Data Cleaning:** Using `Pandas` to remove duplicates and handle missing values
* **Multi-source Fallback Strategy:** Sequential enrichment using OpenLibrary and Google Books
* **Rate-limited Scraping:** Preventing request blocking
* **Database Normalization:** Relational schema with primary keys
* **API Development:** RESTful endpoints using FastAPI
* **Separation of Concerns:** Modular, single-purpose scripts
* **CLI-driven Pipelines:** Reproducible execution via command-line arguments

---

## 🎯 Objectives

* Clean and standardize raw library data
* Handle duplicate and inconsistent ISBN values
* Enrich missing book descriptions using multiple external sources
* Merge enriched data into a single canonical dataset
* Store structured data in a relational database
* Provide REST API access to the enriched dataset

---

## 📁 Project Structure

```
BDE
|__ API
|   |__ api.py
|__ Database
|   |__ SQLite3.py
|   |__ db.sqlite3
|__ Data Gather
|   |__ data_exploration.ipynb
|   |__ dau_library_data.csv
|   |__ ingestion.py
|__ Data
|   |__ FinalDATA.csv
|   |__ dau_library_data.csv
|__ cli_helper.py
|__ README.md
|__ requirements.txt
```

---

## 📁 Detailed File Descriptions

### Root Directory Files

* **cli_helper.py**: Utility for setting up command-line interfaces using `argparse`
* **README.md**: Project documentation
* **requirements.txt**: Python dependencies

### API Directory

* **API/api.py**: FastAPI application exposing book data via REST endpoints

### Data Gather Directory

* **data_exploration.ipynb**: Exploratory analysis of the raw dataset
* **dau_library_data.csv**: Raw dataset copy
* **ingestion.py**: Multi-source enrichment engine with CLI support

### Database Directory

* **SQLite3.py**: Creates schema and loads enriched CSV into SQLite
* **db.sqlite3**: Relational database file

---

## 📋 Data Files Description

### `dau_library_data.csv`

Raw library dataset containing accession details, titles, ISBNs, authors, publishers, year, pages, and classification numbers.
Contains **duplicate records and missing descriptions**.

### `FinalDATA.csv`

Enriched dataset generated by `ingestion.py`, ready for database insertion.

---

## 🔄 Data Enrichment Workflow

1. Load raw library records
2. Remove duplicate entries
3. Identify records with missing descriptions
4. Query **OpenLibrary** using ISBN
5. Fallback to **Google Books HTML scraping**
6. Final fallback using **Google Books API (title + author)**
7. Clean and normalize extracted text
8. Merge successful enrichments
9. Export final enriched CSV

---

## 📊 Dataset Statistics & Numerical Insights

This section summarizes the quantitative impact of the BookFinder enrichment pipeline on the DAU library dataset.

### 🧾 Raw Dataset (`dau_library_data.csv`)

**Size & Structure**

* Records: 36,358
* Columns: 21
* Usable columns: ~10
* Noise columns (`Unnamed:*`): ~11

**Null / Missing Values**

* Title: ~0% missing
* Author/Editor: ~2–3% missing
* ISBN: ~8–10% missing or malformed
* Publisher / Place: ~12% missing
* Year: ~6–8% missing
* Pages: ~15% missing
* Description: ❌ Not present (100% missing)

**Semantic Coverage**

* Books with descriptions: 0
* Average text per record: 0 words

---

### 📘 Final Dataset (`FinalDATA.csv`)

**Size & Structure**

* Records: 35,533
* Columns: 11
* Schema: Clean, normalized, database-ready

**Null / Completeness**

* Critical fields (Acc_No, Title, ISBN, Class_No): 0% missing
* Non-critical fields (Edition, Publisher, Pages): ~3–7% missing
* Description: 0% missing

**Description Enrichment Metrics**

* Books with descriptions: 35,533 (100%)
* Average description length: ~150 words
* Median description length: ~130 words
* Minimum length: ~2 words
* Maximum length: 600+ words

---

### 🔁 Transformation Summary

| Metric                     | Raw Data | Final Data |
| -------------------------- | -------- | ---------- |
| Columns                    | 21       | 11         |
| Description coverage       | 0%       | 100%       |
| Avg text per record        | 0 words  | ~150 words |
| Records usable for search  | 0        | 35,533     |
| NLP / recommendation ready | ❌ No     | ✅ Yes      |

---

## 🗄️ Database Design

**Database:** `db.sqlite3`
**Script:** `Database/SQLite3.py`

```sql
CREATE TABLE IF NOT EXISTS books (
    Acc_Date TEXT,
    Acc_No INTEGER PRIMARY KEY,
    Title TEXT,
    ISBN TEXT,
    Author_Editor TEXT,
    Edition_Volume TEXT,
    Place_Publisher TEXT,
    Year INTEGER,
    Pages TEXT,
    Class_No TEXT,
    description TEXT
);
```

* `Acc_No` is the primary key
* Duplicate insertions avoided using `INSERT OR IGNORE`
* All original metadata preserved

---

## 🌐 API Design

**Application file:** `API/api.py`
**Database:** `Database/db.sqlite3`

### Available Endpoints

| Method | Endpoint        | Description                             |
| ------ | --------------- | --------------------------------------- |
| GET    | `/`             | Health check                            |
| GET    | `/books`        | Fetch books with available descriptions |
| GET    | `/book?isbn=`   | Fetch book using ISBN (query parameter) |
| GET    | `/books/{isbn}` | Fetch book using ISBN (path parameter)  |

**API Characteristics**

* ISBN normalization (hyphens removed)
* Bulk queries return only records with descriptions
* Query limits enforced
* Proper HTTP status codes (`404`, `200`)

---

## 🚀 How to Run This Project

### Prerequisites

Python **3.7+**

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Enrich the Data (The "Researcher")

```bash
python "Data Gather/ingestion.py"
```

Custom execution:

```bash
python "Data Gather/ingestion.py" \
  --input_csv "Data/dau_library_data.csv" \
  --output_csv "Data/FinalDATA.csv" \
  --sleep_time 2.0
```

### 3. Build the Database (The "Librarian")

```bash
python Database/SQLite3.py
```

### 4. Launch the API (The "Receptionist")

```bash
python -m uvicorn API.api:app --reload

```

Access documentation:

```
http://127.0.0.1:8000/docs
```

---

## ⚠️ Limitations & Future Improvements

1. **Search Reliability:** External descriptions may vary in quality
2. **Speed:** Scraping is slower than paid APIs
3. **Read-Only API:** No POST/PUT endpoints
4. **Source Attribution:** Description source is not currently stored
5. **Async Execution:** Pipeline is synchronous

---

## 🛠️ Technologies Used

* Python
* Pandas
* Requests
* BeautifulSoup
* SQLite
* FastAPI
* Uvicorn
* Argparse

---

## 📚 Learning Outcomes

This project demonstrates:

* Practical data cleaning and enrichment
* Multi-layer fallback strategies
* Handling inconsistent real-world metadata
* Relational database design
* API-based data access
* CLI-based data pipelines
* End-to-end data engineering workflows

---

## 🎓 Conclusion

BookFinder addresses a real-world data quality problem using a structured engineering pipeline. It converts incomplete library metadata into an enriched, queryable system exposed through an API. The project emphasizes **robustness, reproducibility, and practical constraints**, making it suitable for both academic evaluation and portfolio presentation.

---

# Library Book Finder: Semantic Search Extension

## Overview
This extension adds a deterministic semantic search system on top of the existing library database. It introduces a manual embedding build pipeline, new FastAPI endpoints, and a React (Vite) front-end for three strict search modes: ISBN exact, Title semantic, and full Semantic search over Title + Description.

## Architecture
```
SQLite (db.sqlite3)
   │
   ├── scripts/build_embeddings.py (manual rebuild)
   │      ├── title_embeddings.npy
   │      ├── desc_embeddings.npy
   │      ├── title_metadata.json
   │      └── desc_metadata.json
   │
FastAPI (API/api.py) ─── /search/* endpoints ─── React UI (/app)
```

## Semantic Logic (Deterministic)
- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Vector dimension: 384
- Description chunking: 2–3 sentence segments (deterministic split)
- Similarity: cosine similarity on normalized vectors
- Title search: embeddings over `Title` only
- Semantic search (primary): equal-weighted average of Title similarity and the best Description chunk similarity

## Explainability (Academic-safe)
- No LLM-generated explanations
- Explanation data includes:
  - similarity score
  - matched text chunk
  - matched field (title or description)
- Highlighting uses deterministic phrase extraction from matched chunks

## Embedding Rebuild (Manual)
Embeddings are stored on disk and never in SQLite.

```
python scripts/build_embeddings.py
```

This will overwrite `embeddings/*.npy` and `embeddings/*.json` files.

## New API Endpoints
- `GET /search/isbn?isbn=...` (exact match only)
- `GET /search/title?query=...` (Title semantic search)
- `GET /search/semantic?query=...` (Title + Description, equal weight)
- `GET /search/raw?query=...` (raw similarity scores and chunks)
- `GET /model-info` (model metadata)
- `GET /health` (service readiness)

Existing endpoints (`/books`, `/book`, `/books/{isbn}`) are unchanged.

## Frontend (React + Vite)
The UI lives in `frontend/` and is served at `/app` when the FastAPI server is running.

Features:
- Three search boxes (only one active at a time)
- Expandable results
- Similarity scores + highlighted phrases
- Threshold-reduction warning banner
- "How Semantic Search Works" with model info from `/model-info`

## Docker Deployment (Single Container)
Build and run locally:

```
docker build -t library-book-finder .
docker run -p 8000:8000 library-book-finder
```

The container builds the front-end, precomputes embeddings, and starts FastAPI.

## Run Instructions (Local)
```
python scripts/build_embeddings.py
uvicorn API.api:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000/app` for the UI.
