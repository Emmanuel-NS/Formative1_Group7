"""Application configuration loaded from environment variables."""

import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# PostgreSQL (Supabase, Aiven, Neon, local)
POSTGRES_HOST = os.getenv("POSTGRES_HOST", os.getenv("MYSQL_HOST", "localhost"))
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", os.getenv("MYSQL_PORT", "5432")))
POSTGRES_USER = os.getenv("POSTGRES_USER", os.getenv("MYSQL_USER", "postgres"))
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", os.getenv("MYSQL_PASSWORD", ""))
POSTGRES_DATABASE = os.getenv(
    "POSTGRES_DATABASE", os.getenv("MYSQL_DATABASE", "pharma_timeseries")
)

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "pharma_timeseries")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "daily_sales")

API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
MODEL_PATH = os.getenv("MODEL_PATH", str(BASE_DIR / "models" / "pharma_demand_model.pkl"))

POSTGRES_URL = (
    f"postgresql+psycopg2://{POSTGRES_USER}:{quote_plus(POSTGRES_PASSWORD)}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DATABASE}"
)
