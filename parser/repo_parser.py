# parser/repo_parser.py
"""
Simple JavaScript/Node repo parser.
Extracts: files, imports, functions, arrow functions, classes, exports and leading comment blocs.
Works with .js, .jsx, .mjs, .cjs, .ts (basic).
"""

from pathlib import Path
import re
import json

JS_EXTS = {'.js', '.jsx', '.mjs', '.cjs', '.ts'}

# regex patterns
RE_IMPORT = re.compile(r'^\s*(?:import\s.+from\s+[\'"].+[\'"]|const\s+\w+\s*=\s*require\([\'"].+[\'"]\))', re.MULTILINE)
RE_FUNCTION = re.compile(r'^\s*function\s+([A-Za-z0-9_$]+)\s*\(', re.MULTILINE)
RE_CLASS = re.compile(r'^\s*class\s+([A-Za-z0-9_$]+)\s*', re.MULTILINE)
RE_ARROW = re.compile(r'^\s*(?:const|let|var)\s+([A-Za-z0-9_$]+)\s*=\s*(?:async\s*)?\(?[^\)]*\)?\s*=>', re.MULTILINE)
RE_EXPORT = re.compile(r'^\s*(?:export\s+default|module\.exports|export\s+\{)', re.MULTILINE)
RE_COMMENT_BLOCK = re.compile(r'(?:/\*\*?[\s\S]*?\*/|//[^\n]*(?:\n//[^\n]*)*)\s*$', re.MULTILINE)

def read_file(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8')
    except Exception:
        return path.read_text(encoding='latin-1')

def extract_leading_comment_for_pos(text: str, start_index: int) -> str:
    """
    Given file text and index where entity starts, try to find a comment block immediately above.
    Returns the comment string or empty.
    """
    # slice up to start_index and search for last comment block
    head = text[:start_index]
    # find last block comment or contiguous line comments just before the entity
    # Search for '/** ... */' or '/* ... */' nearest to end
    block_matches = list(re.finditer(r'/\*\*?[\s\S]*?\*/', head))
    if block_matches:
        last_block = block_matches[-1]
        # ensure block is close to entity (few lines gap)
        gap = head.count('\n', last_block.end(), len(head))
        if gap <= 3:
            return last_block.group().strip()

    # fallback to contiguous line comments immediately above
    # capture last contiguous // lines
    lines = head.splitlines()
    idx = len(lines) - 1
    comments = []
    while idx >= 0 and lines[idx].strip().startswith('//'):
        comments.insert(0, lines[idx].strip())
        idx -= 1
    if comments:
        return "\n".join(comments).strip()
    return ""

def parse_file(path: Path) -> dict:
    text = read_file(path)
    res = {
        "file": str(path),
        "short_name": path.name,
        "imports": [],
        "functions": [],
        "arrow_functions": [],
        "classes": [],
        "exports": [],
    }

    # imports
    for m in RE_IMPORT.finditer(text):
        line = text[m.start(): text.find('\n', m.start())].strip()
        res["imports"].append(line)

    # functions (declarations)
    for m in RE_FUNCTION.finditer(text):
        name = m.group(1)
        start = m.start()
        comment = extract_leading_comment_for_pos(text, start)
        res["functions"].append({"name": name, "pos": start, "comment": comment})

    # classes
    for m in RE_CLASS.finditer(text):
        name = m.group(1)
        start = m.start()
        comment = extract_leading_comment_for_pos(text, start)
        res["classes"].append({"name": name, "pos": start, "comment": comment})

    # arrow functions assigned to vars/consts
    for m in RE_ARROW.finditer(text):
        name = m.group(1)
        start = m.start()
        comment = extract_leading_comment_for_pos(text, start)
        res["arrow_functions"].append({"name": name, "pos": start, "comment": comment})

    # exports
    for m in RE_EXPORT.finditer(text):
        # get the line
        line = text[m.start(): text.find('\n', m.start())].strip()
        res["exports"].append(line)

    return res

def parse_repo(root: str, max_files: int = 500) -> dict:
    root_path = Path(root)
    results = {"root": str(root_path.resolve()), "files": []}
    files = list(root_path.rglob('*'))
    js_files = [p for p in files if p.suffix in JS_EXTS]
    # optional: sort for deterministic behaviour
    js_files = sorted(js_files)[:max_files]

    for p in js_files:
        try:
            parsed = parse_file(p)
            results["files"].append(parsed)
        except Exception as e:
            results["files"].append({"file": str(p), "error": str(e)})

    return results

def save_index(index: dict, out_path: str = "codemap.json"):
    Path(out_path).write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding='utf-8')

# CLI usage
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Parse a JS repo and produce a code map JSON.")
    parser.add_argument("root", help="Path to repo root")
    parser.add_argument("--out", help="Output JSON file", default="codemap.json")
    args = parser.parse_args()

    index = parse_repo(args.root)
    save_index(index, args.out)
    print(f"Indexed {len(index['files'])} JS files. Saved to {args.out}")
