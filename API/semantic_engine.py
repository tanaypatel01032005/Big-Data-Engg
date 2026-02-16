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
INDEX_PATH = EMBEDDINGS_DIR / "index.pkl"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_DIM = 384

DEFAULT_THRESHOLD = 0.60
MIN_THRESHOLD = 0.45
THRESHOLD_STEP = 0.05

# ================= LAZY-LOADED SINGLETONS =================

_vectors = None
_metadata_idx = None # List of (acc_no, is_title_bool)
_model = None
_lock = threading.Lock()
_loading = False

def is_model_ready():
    return _model is not None


def _ensure_loaded():
    """Load model, vectors, and metadata on first use (not at import time)."""
    global _vectors, _metadata_idx, _model, _loading

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

        print("▶ Loading metadata index...")
        # Optimization: Use precomputed pickle if available to avoid JSON parse spike
        if INDEX_PATH.exists():
            import pickle
            with open(INDEX_PATH, "rb") as f:
                _metadata_idx = pickle.load(f)
        else:
            print("⚠️ Precomputed index not found. Falling back to JSON parse (SLOW/HIGH RAM).")
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                _metadata_idx = [
                    (item["acc_no"], item["field"] == "title")
                    for item in raw_data
                ]
                del raw_data

        if _vectors.shape[1] != VECTOR_DIM:
            raise RuntimeError("Embedding dimension mismatch")

        print("▶ Loading sentence-transformer model...")
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME)

        _loading = False
        print(f"✅ Semantic engine ready ({len(_metadata_idx)} vectors loaded)")


# ================= ENGINE =================

def semantic_search(query: str, allowed_fields=None, top_k=50):
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

    candidate_k = min(len(_vectors), top_k * 10)
    chunk_size = 5000
    num_vectors = _vectors.shape[0]

    all_top_indices = []
    all_top_scores = []

    # Process vectors in chunks to avoid loading entire 137MB index into RAM
    for start in range(0, num_vectors, chunk_size):
        end = min(start + chunk_size, num_vectors)
        chunk = _vectors[start:end] # Memory-mapped slice (low RAM)

        # Compute cosine similarity for this chunk
        chunk_sims = cosine_similarity(query_vec, chunk)[0] # (local_size,)

        # Get top local candidates
        k_local = min(len(chunk_sims), top_k * 2) # Get enough candidates
        local_indices = np.argpartition(-chunk_sims, k_local)[:k_local]
        local_scores = chunk_sims[local_indices]

        # Convert to global indices
        global_indices = local_indices + start
        
        all_top_indices.extend(global_indices)
        all_top_scores.extend(local_scores)

    # Convert collected candidates to numpy arrays
    all_top_indices = np.array(all_top_indices)
    all_top_scores = np.array(all_top_scores)

    # Final Sort of candidates
    sorted_order = np.argsort(-all_top_scores)
    sorted_indices = all_top_indices[sorted_order]
    sorted_scores = all_top_scores[sorted_order]

    matches = []
    found_above_default = False

    for i, idx in enumerate(sorted_indices):
        score = sorted_scores[i]

        if score < MIN_THRESHOLD:
            break

        acc_no, is_title = _metadata_idx[idx]
        field = "title" if is_title else "description"

        if allowed_fields and field not in allowed_fields:
            continue

        matches.append({
            "acc_no": acc_no,
            "field": field,
            "text": "...", # Text is discarded to save RAM
            "similarity": float(score)
        })
        
        if score >= DEFAULT_THRESHOLD:
            found_above_default = True

        if len(matches) >= top_k:
            break

    return {
        "results": matches,
        "final_threshold": matches[0]["similarity"] if matches else DEFAULT_THRESHOLD,
        "threshold_reduced": not found_above_default if matches else True
    }
