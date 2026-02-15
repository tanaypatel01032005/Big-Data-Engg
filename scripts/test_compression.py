import numpy as np
import os

path = "c:\\TANAY\\ASSI\\Big-Data-Engg-main\\embeddings\\vectors.npy"
out_path = "c:\\TANAY\\ASSI\\Big-Data-Engg-main\\embeddings\\vectors.npz"

if os.path.exists(path):
    print(f"Loading {path} ({os.path.getsize(path) / 1024**2:.2f} MB)...")
    vectors = np.load(path)
    print(f"Shape: {vectors.shape}")
    
    print("Compressing...")
    np.savez_compressed(out_path, vectors=vectors)
    
    size_mb = os.path.getsize(out_path) / 1024**2
    print(f"Compressed size: {size_mb:.2f} MB")
    
    if size_mb < 100:
        print("SUCCESS: Compressed file is under 100MB!")
    else:
        print("FAILURE: Still too large.")
else:
    print("vectors.npy not found")
