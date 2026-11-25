from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# backend/
BASE_DIR = Path(__file__).resolve().parent.parent
# repository root
ROOT_DIR = BASE_DIR.parent

load_dotenv(BASE_DIR / ".env")


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
USE_EMBEDDINGS = _env_bool("USE_EMBEDDINGS", True)

DB_PATH = Path(os.getenv("DB_PATH", str(BASE_DIR / "data" / "sales_agent.db")))
if not DB_PATH.is_absolute():
    DB_PATH = (BASE_DIR / DB_PATH).resolve()

KNOWLEDGE_DIR = Path(
    os.getenv("KNOWLEDGE_DIR", str(ROOT_DIR / "data" / "knowledge"))
).resolve()

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]

ALLOW_DEMO_RESET = _env_bool("ALLOW_DEMO_RESET", True)

# Local neural voice service (Kokoro-82M). Optional: the UI falls back to the
# browser voice if it is not running.
TTS_URL = os.getenv("TTS_URL", "http://127.0.0.1:8100").rstrip("/")
TTS_ENABLED = _env_bool("TTS_ENABLED", True)
