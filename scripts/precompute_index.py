import json
import pickle
from pathlib import Path

def precompute_index():
    base_dir = Path(__file__).resolve().parent.parent
    meta_path = base_dir / "embeddings" / "metadata.json"
    out_path = base_dir / "embeddings" / "index.pkl"

    if not meta_path.exists():
        print(f"❌ Metadata file not found: {meta_path}")
        return

    print(f"Reading metadata from {meta_path}...")
    with open(meta_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Parsing {len(data)} records...")
    # Schema: List of (acc_no, is_title_bool)
    # Using 'I' (unsigned int) and '?' (bool) struct packing could be small,
    # but pickle of simple list of tuples is efficient enough and easy to load.
    index = [ (d["acc_no"], d["field"] == "title") for d in data ]

    print(f"Saving index to {out_path}...")
    with open(out_path, "wb") as out:
        pickle.dump(index, out)
    
    print(f"✅ Index precomputed. Size: {len(index)} records.")

if __name__ == "__main__":
    precompute_index()
