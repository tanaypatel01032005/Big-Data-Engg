import sys
import os
from pathlib import Path
import time

# Setup path
sys.path.append(os.getcwd())

from API.semantic_engine import semantic_search, _ensure_loaded, _vectors, _metadata

def test_engine():
    print("Testing Semantic Engine loading...")
    start = time.time()
    
    # Trigger load
    _ensure_loaded()
    
    duration = time.time() - start
    print(f"Engine loaded in {duration:.2f} seconds")
    
    # Check data
    from API.semantic_engine import _vectors, _metadata
    print(f"Vectors shape: {_vectors.shape}")
    print(f"Metadata count: {len(_metadata)}")
    
    # Perform search
    print("\nSearching for 'machine learning'...")
    results = semantic_search("machine learning")
    print(f"Found {len(results['results'])} results")
    for r in results['results'][:3]:
        print(f" - {r['acc_no']}: {r['similarity']:.4f} ({r['text'][:50]}...)")

if __name__ == "__main__":
    test_engine()
