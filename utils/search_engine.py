import json
import numpy as np
from pathlib import Path
from utils.embeddings import get_embedding

def cosine_sim(a, b):
    a = np.array(a)
    b = np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def search(query, index_path="vector_index.json", top_k=3):
    if not Path(index_path).exists():
        return None, "Vector index not found. Run: build_vector_index first."

    index = json.loads(Path(index_path).read_text(encoding="utf-8"))
    q_embed = get_embedding(query)

    if q_embed is None:
        return None, "Failed to embed query."

    results = []

    for item in index:
        sim = cosine_sim(q_embed, item["embedding"])
        results.append((sim, item))

    results.sort(reverse=True, key=lambda x: x[0])
    return results[:top_k], None
