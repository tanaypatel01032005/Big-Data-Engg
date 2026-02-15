from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
import sqlite3
import sys
from typing import List, Dict

# ---------------- CLI HELPERS ----------------
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cli_helper import setup_cli, check_help

# ---------------- SEMANTIC ENGINE ----------------
from API.semantic_engine import semantic_search, _model, _loading

# ---------------- CLI CHECK ----------------
check_help("FastAPI application for Library Book Finder")

# ---------------- APP ----------------
app = FastAPI(title="Library Book Finder")

# ---------------- PATHS ----------------
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = os.getenv("BOOK_DB_PATH", str(BASE_DIR / "Database" / "db.sqlite3"))

# ---------------- DB ----------------
def get_db_connection():
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=500, detail="Database file not found")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_books_by_acc_nos(acc_nos: List[int]) -> Dict[int, Dict]:
    if not acc_nos:
        return {}

    placeholders = ",".join("?" for _ in acc_nos)
    query = f"SELECT * FROM books WHERE Acc_No IN ({placeholders})"

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query, acc_nos)
    rows = cur.fetchall()
    conn.close()

    return {row["Acc_No"]: dict(row) for row in rows}

# ---------------- MIDDLEWARE ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- ROOT ----------------
@app.get("/")
def root():
    return {"status": "ok"}

# ---------------- HEALTH ----------------
@app.get("/health")
def health():
    return {
        "status": "ok",
        "database": os.path.exists(DB_PATH),
    }

# ---------------- BOOK LIST ----------------
@app.get("/books")
def get_books(limit: int = Query(1000, ge=1, le=5000)):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT *
        FROM books
        WHERE Title IS NOT NULL
          AND Author_Editor IS NOT NULL
        LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"count": len(rows), "data": rows}

# ---------------- BOOK BY ACC_NO (NEW, FOR MODAL) ----------------
@app.get("/books/id/{acc_no}")
def get_book_by_id(acc_no: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM books WHERE Acc_No = ?", (acc_no,))
    row = cur.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Book not found")

    return dict(row)

# ---------------- RANDOM BOOKS (NEW) ----------------
@app.get("/books/random")
def random_books(limit: int = Query(8, ge=1, le=20)):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT *
        FROM books
        WHERE Title IS NOT NULL
          AND Author_Editor IS NOT NULL
        ORDER BY RANDOM()
        LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"count": len(rows), "data": rows}

# ---------------- ISBN SEARCH ----------------
@app.get("/search/isbn")
def search_isbn(isbn: str = Query(..., min_length=3)):
    isbn = isbn.strip().replace("-", "")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT *
        FROM books
        WHERE REPLACE(ISBN, '-', '') = ?
    """, (isbn,))
    row = cur.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Book not found")

    return {"count": 1, "data": [dict(row)]}

# ---------------- UNIFIED SEARCH (NEW) ----------------
@app.get("/search/unified")
def unified_search(q: str = Query(..., min_length=2, max_length=200)):
    q = q.strip()

    # fast ISBN shortcut
    if q.isdigit():
        try:
            return search_isbn(q)
        except HTTPException:
            pass

    return semantic_search(q)

# ---------------- TITLE SEMANTIC SEARCH ----------------
@app.get("/search/title")
def search_title(query: str = Query(..., min_length=3, max_length=200)):
    semantic = semantic_search(query, allowed_fields=["title"])
    acc_nos = list({r["acc_no"] for r in semantic["results"]})
    books = fetch_books_by_acc_nos(acc_nos)

    results = []
    for r in semantic["results"]:
        book = books.get(r["acc_no"], {})
        results.append({
            **book,
            "similarity": r["similarity"],
            "matches": [{
                "field": r["field"],
                "text": r["text"],
                "score": r["similarity"]
            }]
        })

    return {
        "results": results,
        "final_threshold": semantic["final_threshold"],
        "threshold_reduced": semantic["threshold_reduced"]
    }

# ---------------- FULL SEMANTIC SEARCH ----------------
@app.get("/search/semantic")
def search_semantic(query: str = Query(..., min_length=3, max_length=200)):
    semantic = semantic_search(query)
    acc_nos = list({r["acc_no"] for r in semantic["results"]})
    books = fetch_books_by_acc_nos(acc_nos)

    results = []
    for r in semantic["results"]:
        book = books.get(r["acc_no"], {})
        results.append({
            **book,
            "similarity": r["similarity"],
            "matches": [{
                "field": r["field"],
                "text": r["text"],
                "score": r["similarity"]
            }]
        })

    return {
        "results": results,
        "final_threshold": semantic["final_threshold"],
        "threshold_reduced": semantic["threshold_reduced"]
    }

# ---------------- RAW SEMANTIC SEARCH ----------------
@app.get("/search/raw")
def search_raw(query: str = Query(..., min_length=3, max_length=200)):
    return semantic_search(query)

# ---------------- MODEL INFO ----------------
@app.get("/model-info")
def model_info():
    return {
        "model_name": "sentence-transformers/all-MiniLM-L6-v2",
        "vector_dimension": 384,
        "default_threshold": 0.60,
    }

# ---------------- SEARCH ENGINE STATUS ----------------
@app.get("/search/status")
def search_status():
    return {
        "ready": _model is not None,
        "loading": _loading,
    }

# ---------------- FRONTEND SERVING ----------------
frontend_dist = BASE_DIR / "frontend" / "dist"
if frontend_dist.exists():
    app.mount(
        "/app",
        StaticFiles(directory=frontend_dist, html=True),
        name="frontend",
    )

# ---------------- MAIN ----------------
if __name__ == "__main__":
    setup_cli("Library Book Finder API", [])
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
