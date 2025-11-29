import json
from pathlib import Path
from utils.embeddings import get_embedding

def build_vector_index(codemap_path="codemap.json", save_path="vector_index.json"):
    codemap = json.loads(Path(codemap_path).read_text(encoding="utf-8"))
    index = []

    for f in codemap["files"]:
        if "short_name" not in f:
            continue

        path = f["file"]
        short = f["short_name"]

        try:
            code = Path(path).read_text(encoding="utf-8")
        except:
            continue

        text_for_embedding = f"FILENAME: {short}\nCONTENT:\n{code[:3000]}"

        embedding = get_embedding(text_for_embedding)
        if embedding:
            index.append({
                "file": path,
                "short_name": short,
                "embedding": embedding
            })

    Path(save_path).write_text(json.dumps(index, indent=2), encoding="utf-8")
    return index