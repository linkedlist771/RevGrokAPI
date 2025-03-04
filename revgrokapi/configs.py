from pathlib import Path
import os
ROOT = Path(__file__).parent.parent
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True, parents=True)

DOCS_USERNAME = "claude-backend"
DOCS_PASSWORD = "20Wd!!!!"


DEFAULT_TOKENIZER = "cl100k_base"
USE_TOKEN_SHORTEN = True


DATA_DIR = ROOT / "data"

DB_PATH = DATA_DIR / "db.sqlite3"
DB_URL = f"sqlite://{DB_PATH}"

POE_OPENAI_LIKE_API_KEY = "sk-poe-api-dfascvu2"

GROK_CLIENT_LIMIT_CHECKS_INTERVAL_MINUTES = 1 * 60

PROXIES = {}


# PROXIES = {
#     "http": "http://127.0.0.1:7890",
#     "https": "http://127.0.0.1:7890",
# } if not os.environ.get("PRODUCTION") else None

if __name__ == "__main__":
    print(ROOT)
