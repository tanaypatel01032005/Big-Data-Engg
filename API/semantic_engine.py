import json
import sys
import threading
from pathlib import Path
import numpy as np

from .utils import normalize_query, cosine_similarity

# ================= CONFIG =================

BASE_DIR = Path(__file__).resolve().parent.parent
EMBEDDINGS_DIR = BASE_DIR / "embeddings"

VECTORS_PATH = EMBEDDINGS_DIR / "vectors.npy"
METADATA_PATH = EMBEDDINGS_DIR / "metadata.json"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_DIM = 384

DEFAULT_THRESHOLD = 0.60
MIN_THRESHOLD = 0.45
THRESHOLD_STEP = 0.05

# ================= LAZY-LOADED SINGLETONS =================

_vectors = None
_metadata = None
_model = None
_lock = threading.Lock()
_loading = False


def _ensure_loaded():
    """Load model, vectors, and metadata on first use (not at import time)."""
    global _vectors, _metadata, _model, _loading

    if _model is not None:
        return  # already loaded

    with _lock:
        if _model is not None:
            return  # double-check after acquiring lock

        _loading = True

        # Auto-build if embeddings are missing
        if not VECTORS_PATH.exists() or not METADATA_PATH.exists():
            print("⚙️  Embeddings not found — building automatically...")
            sys.path.insert(0, str(BASE_DIR))
            from scripts.build_embeddings import build_embeddings
            build_embeddings()
            print("✅ Embeddings built successfully.")

        print("▶ Loading embedding vectors (mmap)...")
        # Use mmap_mode='r' to keep vectors on disk, saving ~130MB RAM
        _vectors = np.load(VECTORS_PATH, mmap_mode='r')

        print("▶ Loading metadata...")
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            _metadata = json.load(f)

        if _vectors.shape[1] != VECTOR_DIM:
            raise RuntimeError("Embedding dimension mismatch")

        print("▶ Loading sentence-transformer model...")
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME)

        _loading = False
        print(f"✅ Semantic engine ready ({len(_metadata)} vectors loaded)")


# ================= NO BACKGROUND PRELOAD =================
# We removed the background thread to prevent CPU/RAM spikes during
# the critical boot phase (avoiding Gunicorn timeouts).
# The model will load on the first user search request.


# ================= ENGINE =================

def semantic_search(query: str, allowed_fields=None):
    """
    allowed_fields:
        None            → title + description
        ["title"]       → title only
    """
    _ensure_loaded()

    query = normalize_query(query)
    if not query:
        return {
            "results": [],
            "final_threshold": DEFAULT_THRESHOLD,
            "threshold_reduced": False
        }

    query_vec = _model.encode(query)

    similarities = cosine_similarity(query_vec, _vectors)

    threshold = DEFAULT_THRESHOLD
    threshold_reduced = False

    while threshold >= MIN_THRESHOLD:
        matches = []

        for idx, score in enumerate(similarities):
            if score < threshold:
                continue

            meta = _metadata[idx]

            if allowed_fields and meta["field"] not in allowed_fields:
                continue

            matches.append({
                "acc_no": meta["acc_no"],
                "field": meta["field"],
                "text": meta["text"],
                "similarity": float(score)
            })

        if matches:
            matches.sort(
                key=lambda x: (-x["similarity"], x["acc_no"])
            )
            return {
                "results": matches,
                "final_threshold": threshold,
                "threshold_reduced": threshold < DEFAULT_THRESHOLD
            }

        threshold -= THRESHOLD_STEP
        threshold_reduced = True

    return {
        "results": [],
        "final_threshold": threshold,
        "threshold_reduced": True
    }
