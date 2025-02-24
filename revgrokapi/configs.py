from pathlib import Path

ROOT = Path(__file__).parent.parent
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True, parents=True)

DOCS_USERNAME = "claude-backend"
DOCS_PASSWORD = "20Wd!!!!"


DEFAULT_TOKENIZER = "cl100k_base"
USE_TOKEN_SHORTEN = True


DATA_DIR = ROOT / "data"

DB_PATH =  DATA_DIR / "db.sqlite3"
DB_URL=f"sqlite://{DB_PATH}"

if __name__ == "__main__":
    print(ROOT)
