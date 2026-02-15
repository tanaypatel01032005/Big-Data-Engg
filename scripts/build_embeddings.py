import sqlite3
import json
import re
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# ================== CONFIG ==================

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "Database" / "db.sqlite3"
EMBEDDINGS_DIR = BASE_DIR / "embeddings"

VECTORS_PATH = EMBEDDINGS_DIR / "vectors.npy"
METADATA_PATH = EMBEDDINGS_DIR / "metadata.json"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_DIM = 384

# ================== TEXT UTILITIES ==================

def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())

def split_sentences(text: str):
    if not text:
        return []
    text = normalize_text(text)
    return re.split(r"(?<=[.!?])\s+", text)

def chunk_sentences(sentences, min_sent=2, max_sent=3):
    chunks = []
    i = 0
    while i < len(sentences):
        chunk = sentences[i:i + max_sent]
        if len(chunk) >= min_sent:
            chunks.append(" ".join(chunk))
        i += max_sent
    return chunks

# ================== MAIN PIPELINE ==================

def build_embeddings():
    print("▶ Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)

    print("▶ Connecting to SQLite database...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT Acc_No, Title, description
        FROM books
        ORDER BY Acc_No ASC
    """)

    rows = cursor.fetchall()
    conn.close()

    # ---------- Step 1: Collect all texts + metadata ----------
    texts = []
    metadata = []

    print(f"▶ Preparing {len(rows)} books...")
    for acc_no, title, description in rows:
        if title:
            text = normalize_text(title)
            texts.append(text)
            metadata.append({
                "chunk_id": len(texts) - 1,
                "acc_no": acc_no,
                "field": "title",
                "text": text
            })

        if description:
            sentences = split_sentences(description)
            chunks = chunk_sentences(sentences)
            for chunk in chunks:
                texts.append(chunk)
                metadata.append({
                    "chunk_id": len(texts) - 1,
                    "acc_no": acc_no,
                    "field": "description",
                    "text": chunk
                })

    # ---------- Step 2: Batch encode ----------
    print(f"▶ Encoding {len(texts)} text chunks in batches...")
    vectors = model.encode(
        texts,
        batch_size=256,
        show_progress_bar=True,
        normalize_embeddings=True  # pre-normalize for fast dot-product similarity
    )

    vectors = np.array(vectors, dtype=np.float32)

    if vectors.shape[1] != VECTOR_DIM:
        raise ValueError("Embedding dimension mismatch")

    # ---------- Step 3: Save ----------
    EMBEDDINGS_DIR.mkdir(exist_ok=True)

    print("▶ Writing embedding vectors...")
    np.save(VECTORS_PATH, vectors)

    print("▶ Writing metadata...")
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False)

    print("✅ Embedding rebuild completed successfully")
    print(f"   Total vectors: {len(vectors)}")
    print(f"   Output:")
    print(f"     - {VECTORS_PATH}")
    print(f"     - {METADATA_PATH}")

# ================== ENTRY POINT ==================

if __name__ == "__main__":
    build_embeddings()
