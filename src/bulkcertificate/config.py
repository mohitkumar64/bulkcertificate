"""Application configuration from environment variables."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
STORAGE_PATH = os.getenv("STORAGE_PATH", "./storage")
TEMPLATE_PATH = os.getenv("TEMPLATE_PATH", str(BASE_DIR / "templates" / "certificate.svg"))
CELERY_WORKER_CONCURRENCY = int(os.getenv("CELERY_WORKER_CONCURRENCY", "3"))

