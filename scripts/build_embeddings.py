import argparse
import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Dict, List

import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_DIMENSION = 384

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = os.getenv("BOOK_DB_PATH", str(BASE_DIR / "Database" / "db.sqlite3"))
OUTPUT_DIR = BASE_DIR / "embeddings"


def sentence_chunk(description: str) -> List[str]:
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", description)
        if sentence.strip()
    ]
    if not sentences:
        return []
    chunks = []
    idx = 0
    while idx < len(sentences):
        chunk_sentences = sentences[idx : idx + 2]
        idx += 2
        chunk = " ".join(chunk_sentences)
        chunks.append(chunk)
    if len(chunks) >= 2 and len(chunks[-1].split()) <= 6:
        chunks[-2] = f"{chunks[-2]} {chunks[-1]}".strip()
        chunks.pop()
    return chunks


def load_books(conn: sqlite3.Connection) -> List[Dict[str, str]]:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT Acc_No, Title, description
        FROM books
        WHERE Title IS NOT NULL
        ORDER BY Acc_No ASC
        """
    )
    rows = cursor.fetchall()
    return [
        {
            "acc_no": row[0],
            "title": row[1] or "",
            "description": row[2] or "",
        }
        for row in rows
    ]


def build_embeddings() -> None:
    if not Path(DB_PATH).exists():
        raise FileNotFoundError(f"Database file not found at {DB_PATH}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    books = load_books(conn)
    conn.close()

    model = SentenceTransformer(MODEL_NAME, device="cpu")

    title_texts = [book["title"] for book in books]
    title_vectors = model.encode(title_texts, batch_size=64, show_progress_bar=True)
    title_vectors = np.asarray(title_vectors, dtype=np.float32)
    title_metadata = [
        {"acc_no": book["acc_no"], "title": book["title"]} for book in books
    ]

    desc_texts = []
    desc_metadata = []
    for book in books:
        chunks = sentence_chunk(book["description"])
        for chunk in chunks:
            desc_texts.append(chunk)
            desc_metadata.append(
                {
                    "acc_no": book["acc_no"],
                    "chunk": chunk,
                }
            )

    if desc_texts:
        desc_vectors = model.encode(desc_texts, batch_size=64, show_progress_bar=True)
    else:
        desc_vectors = np.zeros((0, MODEL_DIMENSION), dtype=np.float32)

    desc_vectors = np.asarray(desc_vectors, dtype=np.float32)

    np.save(OUTPUT_DIR / "title_embeddings.npy", title_vectors)
    np.save(OUTPUT_DIR / "desc_embeddings.npy", desc_vectors)

    (OUTPUT_DIR / "title_metadata.json").write_text(
        json.dumps(title_metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "desc_metadata.json").write_text(
        json.dumps(desc_metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    (OUTPUT_DIR / "model_info.json").write_text(
        json.dumps(
            {
                "model_name": MODEL_NAME,
                "vector_dimension": MODEL_DIMENSION,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build semantic search embeddings for the library database."
    )
    parser.parse_args()
    build_embeddings()


if __name__ == "__main__":
    main()
