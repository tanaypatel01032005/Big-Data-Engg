from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import json
import os
import re
import sqlite3
import sys
from typing import Dict, List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cli_helper import setup_cli, check_help

# Check for --help early
check_help("FastAPI application for book library management.")

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = os.getenv("BOOK_DB_PATH", str(BASE_DIR / "Database" / "db.sqlite3"))

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_DIMENSION = 384
DEFAULT_THRESHOLD = 0.60
MIN_THRESHOLD = 0.45
THRESHOLD_STEP = 0.05

EMBEDDINGS_DIR = BASE_DIR / "embeddings"
TITLE_EMBEDDINGS_PATH = EMBEDDINGS_DIR / "title_embeddings.npy"
TITLE_METADATA_PATH = EMBEDDINGS_DIR / "title_metadata.json"
DESC_EMBEDDINGS_PATH = EMBEDDINGS_DIR / "desc_embeddings.npy"
DESC_METADATA_PATH = EMBEDDINGS_DIR / "desc_metadata.json"

def get_db_connection():
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=500, detail="Database file not found")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def normalize_vectors(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms


def normalize_vector(vector: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector
    return vector / norm


STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "he",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "that",
    "the",
    "to",
    "was",
    "were",
    "will",
    "with",
}


def extract_phrases(text: str, max_phrases: int = 3) -> List[str]:
    tokens = [token for token in re.findall(r"[A-Za-z0-9']+", text.lower())]
    if not tokens:
        return []
    candidate_phrases = []
    for length in (3, 2):
        for idx in range(len(tokens) - length + 1):
            phrase_tokens = tokens[idx : idx + length]
            if any(token in STOP_WORDS for token in phrase_tokens):
                continue
            phrase = " ".join(phrase_tokens)
            score = sum(len(token) for token in phrase_tokens)
            candidate_phrases.append((score, phrase))
    candidate_phrases.sort(key=lambda item: (-item[0], item[1]))
    phrases = []
    for _, phrase in candidate_phrases:
        if phrase not in phrases:
            phrases.append(phrase)
        if len(phrases) >= max_phrases:
            break
    return phrases


class SearchEngine:
    def __init__(self) -> None:
        self.model: Optional[SentenceTransformer] = None
        self.title_vectors: Optional[np.ndarray] = None
        self.title_metadata: List[Dict[str, str]] = []
        self.desc_vectors: Optional[np.ndarray] = None
        self.desc_metadata: List[Dict[str, str]] = []

    def load(self) -> None:
        required_files = [
            TITLE_EMBEDDINGS_PATH,
            DESC_EMBEDDINGS_PATH,
            TITLE_METADATA_PATH,
            DESC_METADATA_PATH,
        ]
        if not all(path.exists() for path in required_files):
            return
        self.model = SentenceTransformer(MODEL_NAME, device="cpu")
        self.title_vectors = normalize_vectors(np.load(TITLE_EMBEDDINGS_PATH))
        self.desc_vectors = normalize_vectors(np.load(DESC_EMBEDDINGS_PATH))
        self.title_metadata = json.loads(TITLE_METADATA_PATH.read_text(encoding="utf-8"))
        self.desc_metadata = json.loads(DESC_METADATA_PATH.read_text(encoding="utf-8"))

    def ready(self) -> bool:
        return (
            self.model is not None
            and self.title_vectors is not None
            and self.desc_vectors is not None
            and self.title_metadata is not None
            and self.desc_metadata is not None
        )


search_engine = SearchEngine()


@app.on_event("startup")
def load_embeddings() -> None:
    search_engine.load()


def ensure_search_ready() -> None:
    if not search_engine.ready():
        raise HTTPException(
            status_code=503,
            detail="Embeddings not found. Run scripts/build_embeddings.py first.",
        )


def compute_query_embedding(query: str) -> np.ndarray:
    ensure_search_ready()
    vector = search_engine.model.encode([query], show_progress_bar=False)
    return normalize_vector(vector[0])


def resolve_threshold(scores: List[float]) -> Dict[str, float | bool]:
    threshold = DEFAULT_THRESHOLD
    reduced = False
    if any(score >= threshold for score in scores):
        return {"threshold": threshold, "reduced": reduced}
    while threshold > MIN_THRESHOLD:
        threshold = round(threshold - THRESHOLD_STEP, 2)
        reduced = True
        if any(score >= threshold for score in scores):
            break
    return {"threshold": threshold, "reduced": reduced}


def fetch_books_by_acc_no(acc_nos: List[int]) -> Dict[int, Dict[str, str]]:
    if not acc_nos:
        return {}
    placeholders = ",".join("?" for _ in acc_nos)
    query = f"SELECT * FROM books WHERE Acc_No IN ({placeholders})"
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, acc_nos)
    rows = cursor.fetchall()
    conn.close()
    return {row["Acc_No"]: dict(row) for row in rows}


def build_title_results(query: str) -> Dict[str, object]:
    query_vector = compute_query_embedding(query)
    title_scores = np.dot(search_engine.title_vectors, query_vector)
    scores = title_scores.tolist()
    threshold_info = resolve_threshold(scores)
    filtered = [
        (idx, score)
        for idx, score in enumerate(scores)
        if score >= threshold_info["threshold"]
    ]
    filtered.sort(key=lambda item: item[1], reverse=True)
    acc_nos = [int(search_engine.title_metadata[idx]["acc_no"]) for idx, _ in filtered]
    books = fetch_books_by_acc_no(acc_nos)
    results = []
    for idx, score in filtered:
        meta = search_engine.title_metadata[idx]
        acc_no = int(meta["acc_no"])
        book = books.get(acc_no, {})
        results.append(
            {
                "acc_no": acc_no,
                "title": book.get("Title"),
                "author": book.get("Author_Editor"),
                "year": book.get("Year"),
                "similarity": round(float(score), 4),
                "match": {
                    "field": "title",
                    "text": meta["title"],
                    "score": round(float(score), 4),
                },
                "highlight_phrases": extract_phrases(meta["title"]),
            }
        )
    return {
        "query": query,
        "threshold": threshold_info,
        "count": len(results),
        "results": results,
    }


def build_semantic_results(query: str) -> Dict[str, object]:
    query_vector = compute_query_embedding(query)
    title_scores = np.dot(search_engine.title_vectors, query_vector)
    desc_scores = np.dot(search_engine.desc_vectors, query_vector)

    title_map = {
        int(meta["acc_no"]): float(score)
        for meta, score in zip(search_engine.title_metadata, title_scores)
    }

    best_desc: Dict[int, Dict[str, object]] = {}
    for meta, score in zip(search_engine.desc_metadata, desc_scores):
        acc_no = int(meta["acc_no"])
        current = best_desc.get(acc_no)
        if current is None or score > current["score"]:
            best_desc[acc_no] = {
                "score": float(score),
                "text": meta["chunk"],
            }

    combined_scores = []
    acc_nos = []
    for acc_no, title_score in title_map.items():
        desc_entry = best_desc.get(acc_no, {"score": 0.0, "text": ""})
        combined = (title_score + desc_entry["score"]) / 2
        combined_scores.append(combined)
        acc_nos.append(acc_no)

    threshold_info = resolve_threshold(combined_scores)

    filtered = []
    for acc_no, combined_score in zip(acc_nos, combined_scores):
        if combined_score >= threshold_info["threshold"]:
            filtered.append((acc_no, combined_score))

    filtered.sort(key=lambda item: item[1], reverse=True)
    books = fetch_books_by_acc_no([acc_no for acc_no, _ in filtered])
    results = []
    for acc_no, combined_score in filtered:
        book = books.get(acc_no, {})
        title_score = title_map.get(acc_no, 0.0)
        desc_entry = best_desc.get(acc_no, {"score": 0.0, "text": ""})
        match_text = desc_entry["text"] or book.get("Title", "")
        results.append(
            {
                "acc_no": acc_no,
                "title": book.get("Title"),
                "author": book.get("Author_Editor"),
                "year": book.get("Year"),
                "similarity": round(float(combined_score), 4),
                "matches": [
                    {
                        "field": "title",
                        "text": book.get("Title"),
                        "score": round(float(title_score), 4),
                    },
                    {
                        "field": "description",
                        "text": desc_entry["text"],
                        "score": round(float(desc_entry["score"]), 4),
                    },
                ],
                "highlight_phrases": extract_phrases(match_text),
            }
        )
    return {
        "query": query,
        "threshold": threshold_info,
        "count": len(results),
        "results": results,
    }

@app.get("/")
def root():
    return {"message": "Book Library API is working"}


@app.get("/books")
def get_books(
    limit: int = Query(1000, ge=1, le=5000, description="Number of books to fetch")
):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM books
        WHERE description IS NOT NULL
        ORDER BY Acc_Date DESC
        LIMIT ?
    """, (limit,))

    books = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return {
        "count": len(books),
        "data": books
    }


@app.get("/book")
def get_book_by_isbn(isbn: str):
    isbn = isbn.strip().replace("-", "")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM books
        WHERE REPLACE(ISBN, '-', '') = ?
    """, (isbn,))

    row = cursor.fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Book not found")

    return dict(row)


@app.get("/books/{isbn}")
def get_book_by_isbn_path(isbn: str):
    isbn = isbn.strip().replace("-", "")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM books
        WHERE REPLACE(ISBN, '-', '') = ?
    """, (isbn,))

    row = cursor.fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Book not found")

    return dict(row)


@app.get("/search/isbn")
def search_isbn(isbn: str = Query(..., min_length=3)):
    isbn = isbn.strip().replace("-", "")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT *
        FROM books
        WHERE REPLACE(ISBN, '-', '') = ?
    """,
        (isbn,),
    )
    row = cursor.fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return {"count": 1, "data": [dict(row)]}


@app.get("/search/title")
def search_title(query: str = Query(..., min_length=3, max_length=200)):
    return build_title_results(query)


@app.get("/search/semantic")
def search_semantic(query: str = Query(..., min_length=3, max_length=200)):
    return build_semantic_results(query)


@app.get("/search/raw")
def search_raw(query: str = Query(..., min_length=3, max_length=200)):
    query_vector = compute_query_embedding(query)
    title_scores = np.dot(search_engine.title_vectors, query_vector)
    desc_scores = np.dot(search_engine.desc_vectors, query_vector)

    raw_titles = [
        {
            "acc_no": int(meta["acc_no"]),
            "title": meta["title"],
            "score": round(float(score), 6),
        }
        for meta, score in zip(search_engine.title_metadata, title_scores)
    ]
    raw_desc = [
        {
            "acc_no": int(meta["acc_no"]),
            "chunk": meta["chunk"],
            "score": round(float(score), 6),
        }
        for meta, score in zip(search_engine.desc_metadata, desc_scores)
    ]

    return {
        "query": query,
        "title_scores": raw_titles,
        "description_scores": raw_desc,
    }


@app.get("/model-info")
def model_info():
    return {
        "model_name": MODEL_NAME,
        "vector_dimension": MODEL_DIMENSION,
        "default_threshold": DEFAULT_THRESHOLD,
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "database": os.path.exists(DB_PATH),
        "embeddings_loaded": search_engine.ready(),
    }


if (BASE_DIR / "frontend" / "dist").exists():
    app.mount(
        "/assets",
        StaticFiles(directory=BASE_DIR / "frontend" / "dist" / "assets", html=True),
        name="assets",
    )

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Allow API calls to pass through
        if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
             raise HTTPException(status_code=404, detail="Not Found")
             
        # Serve the index.html for all other routes (SPA support)
        index_path = BASE_DIR / "frontend" / "dist" / "index.html"
        if index_path.exists():
             from fastapi.responses import FileResponse
             return FileResponse(index_path)
        return {"message": "Frontend not found"}


if __name__ == "__main__":
    args = setup_cli(
        "FastAPI application for book library management.",
        []
    )
    # Run the FastAPI app
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
