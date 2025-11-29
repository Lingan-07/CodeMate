from fastapi import FastAPI, Request
from urllib.parse import parse_qs
from pathlib import Path
import json

# parser
from parser.repo_parser import parse_repo, save_index

# summarizer
from utils.summarize import summarize_code

# semantic search
from utils.search_engine import search
from utils.vector_index import build_vector_index

app = FastAPI()

# -------------------------------------------------------------
# HOME
# -------------------------------------------------------------
@app.get("/")
def home():
    return {"status": "CodeMate is running 🚀"}


# -------------------------------------------------------------
# ZOHO BOT ENDPOINT
# -------------------------------------------------------------
@app.post("/bot")
async def handle_bot_message(request: Request):

    raw = await request.body()
    body_str = raw.decode("utf-8")
    parsed = parse_qs(body_str)

    # extract user + text
    user_json_str = parsed.get("user", ["{}"])[0]
    text = parsed.get("text", [""])[0]

    # parse user info
    try:
        user_data = json.loads(user_json_str)
    except:
        user_data = {"first_name": "Developer"}

    username = user_data.get("first_name", "Developer")
    message = text.lower().strip()

    # ---------------------------------------------------------
    # BASIC COMMANDS
    # ---------------------------------------------------------
    if message.startswith("hi") or message.startswith("hello"):
        return {"text": f"Hey {username}! 👋 CodeMate is online!"}

    if message == "help":
        return {"text":
            "**CodeMate Commands**\n\n"
            "• `summarize <file>` → Summaries any file\n"
            "• `search <query>` → Semantic code search\n"
            "• `index repo` → Instructions to index repo\n"
            "• `/index_repo?path=<your_repo_path>` → Build codemap\n"
            "• `/build_index` → Build vector index for semantic search\n"
        }

    # ---------------------------------------------------------
    # INSTRUCTION TO INDEX REPO
    # ---------------------------------------------------------
    if message.startswith("index repo"):
        return {
            "text": (
                "To index your repo, open browser and run:\n"
                "`/index_repo?path=C:/path/to/project`\n"
                "This will generate codemap.json"
            )
        }

    # ---------------------------------------------------------
    # SUMMARIZE FILE
    # ---------------------------------------------------------
    if message.startswith("summarize"):
        parts = message.split(" ", 1)
        if len(parts) < 2:
            return {"text": "Usage: summarize <filename>"}

        target_file = parts[1].strip()

        # check codemap
        codemap_path = Path("codemap.json")
        if not codemap_path.exists():
            return {"text": "❌ No codemap found. Run `/index_repo` first."}

        codemap = json.loads(codemap_path.read_text(encoding="utf-8"))

        # search file
        for f in codemap["files"]:
            if "short_name" not in f:
                continue

            if f["short_name"].lower() == target_file.lower():
                file_path = f["file"]

                try:
                    code = Path(file_path).read_text(encoding="utf-8")
                except:
                    return {"text": f"❌ Unable to read file: {file_path}"}

                summary = summarize_code(target_file, code)
                return {"text": f"**Summary of {target_file}:**\n\n{summary}"}

        return {"text": f"❌ File not found: {target_file}"}

    # ---------------------------------------------------------
    # SEMANTIC SEARCH
    # ---------------------------------------------------------
    if message.startswith("search") or message.startswith("where"):
        query = (
            message.replace("search", "")
            .replace("where", "")
            .strip()
        )

        results, err = search(query)

        if err:
            return {"text": err}

        response = f"🔍 **Top results for:** `{query}`\n\n"
        for score, item in results:
            response += f"- `{item['short_name']}` (score: **{round(score, 2)}**)\n"

        return {"text": response}

    # ---------------------------------------------------------
    # UNKNOWN COMMAND
    # ---------------------------------------------------------
    return {"text": "I didn't understand that. Type `help` to see commands."}


# -------------------------------------------------------------
# INDEX REPO (GET + POST)
# -------------------------------------------------------------
@app.api_route("/index_repo", methods=["GET", "POST"])
async def index_repo(path: str):
    idx = parse_repo(path)
    save_index(idx, "codemap.json")

    return {
        "status": "indexed",
        "root": idx["root"],
        "files_indexed": len(idx["files"])
    }


# -------------------------------------------------------------
# BUILD VECTOR INDEX (for semantic search)
# -------------------------------------------------------------
@app.get("/build_index")
def build_vec_index():
    index = build_vector_index()
    return {"status": "vector index built", "entries": len(index)}


# -------------------------------------------------------------
# VIEW CODEMAP
# -------------------------------------------------------------
@app.get("/codemap")
def get_codemap():
    codemap_path = Path("codemap.json")
    if not codemap_path.exists():
        return {"error": "codemap.json not found."}

    return json.loads(codemap_path.read_text(encoding="utf-8"))
