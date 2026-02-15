import numpy as np
import re

def normalize_query(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip().lower())

def cosine_similarity(query_vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    query_norm = np.linalg.norm(query_vec)
    matrix_norms = np.linalg.norm(matrix, axis=1)

    if query_norm == 0:
        return np.zeros(len(matrix))

    return np.dot(matrix, query_vec) / (matrix_norms * query_norm + 1e-10)
