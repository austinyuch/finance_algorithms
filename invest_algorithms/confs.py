"""Application configuration.

Security-sensitive settings are read from environment variables with safe
defaults, so production deployments can lock things down without code changes.
"""

import os
from pathlib import Path


def _env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def _env_origins(name: str) -> list[str]:
    """Comma-separated allowlist of CORS origins. Empty by default (no cross-origin access)."""
    raw = os.getenv(name, "")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


# Bind to loopback by default; set API_HOST=0.0.0.0 explicitly for cloud hosting.
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "2224"))

dic_api = {
    "site_name": "API Algorithms",
    "description": "Algorithms Service",
    "host": API_HOST,
    "port": API_PORT,
    "reload": _env_bool("API_RELOAD", False),  # 正式佈署時用 False 比較穩定
    "workers": int(os.getenv("API_WORKERS", "1")),  # 開 multiprocess
    "log_level": os.getenv("API_LOG_LEVEL", "info").lower(),
}

# Application log level (Python logging). Default INFO; avoid DEBUG in production.
GLOBAL_LOG_LEVEL = os.getenv("GLOBAL_LOG_LEVEL", "INFO").upper()

# CORS allowlist. Explicit origins only — never "*" together with credentials.
lst_origins = _env_origins("API_CORS_ORIGINS")

PATH_SRC = Path(__file__).resolve().parents[0]
PATH_LOG_FOLDER = PATH_SRC.joinpath("logs")
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "14"))
