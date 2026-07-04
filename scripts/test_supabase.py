"""Test Supabase PostgreSQL connection only."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine, text
from app.config import POSTGRES_URL, POSTGRES_USER, POSTGRES_HOST, POSTGRES_DATABASE

print("Testing Supabase PostgreSQL...")
print(f"  Host: {POSTGRES_HOST}")
print(f"  User: {POSTGRES_USER}")
print(f"  Database: {POSTGRES_DATABASE}")

try:
    engine = create_engine(POSTGRES_URL, pool_pre_ping=True)
    with engine.connect() as conn:
        one = conn.execute(text("SELECT 1")).scalar()
        tables = conn.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' ORDER BY table_name"
            )
        ).fetchall()
    print("SUCCESS: Connected to Supabase PostgreSQL")
    print(f"  SELECT 1 => {one}")
    if tables:
        print("  Existing tables:", [t[0] for t in tables])
    else:
        print("  No tables yet (run: python scripts/load_data.py)")
except Exception as exc:
    print("FAILED:", exc)
    raise SystemExit(1)
