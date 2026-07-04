"""Quick connectivity test for PostgreSQL, MongoDB, model file, and CSV data."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import MODEL_PATH, POSTGRES_DATABASE, POSTGRES_HOST


def check_csv():
    csv_path = ROOT / "data" / "salesdaily.csv"
    if csv_path.exists():
        print(f"[OK] CSV found: {csv_path}")
        return True
    print(f"[MISSING] CSV not found: {csv_path}")
    print("       Download from Kaggle and place in data/salesdaily.csv")
    return False


def check_model():
    model_path = Path(MODEL_PATH)
    if not model_path.is_absolute():
        model_path = ROOT / model_path
    if model_path.exists():
        print(f"[OK] Model found: {model_path}")
        try:
            import joblib
            artifacts = joblib.load(model_path)
            print(f"     Experiment: {artifacts.get('best_experiment', 'unknown')}")
            print(f"     Features: {len(artifacts.get('feature_columns', []))}")
        except Exception as exc:
            print(f"[WARN] Model file exists but failed to load: {exc}")
        return True
    print(f"[MISSING] Model not found: {model_path}")
    print("       Run Colab notebook and download pharma_demand_model.pkl")
    return False


def check_postgres():
    try:
        from app.database import ping_postgres
        ping_postgres()
        print(f"[OK] PostgreSQL connected ({POSTGRES_HOST} / {POSTGRES_DATABASE})")
        return True
    except Exception as exc:
        print(f"[FAIL] PostgreSQL: {exc}")
        return False


def check_mongodb():
    try:
        from app.database import ping_mongodb
        ping_mongodb()
        print("[OK] MongoDB connected")
        return True
    except Exception as exc:
        print(f"[FAIL] MongoDB: {exc}")
        return False


def main():
    print("=" * 60)
    print("PHARMA PIPELINE - CONNECTIVITY TEST")
    print("=" * 60)
    results = {
        "csv": check_csv(),
        "postgres": check_postgres(),
        "mongodb": check_mongodb(),
        "model": check_model(),
    }
    print("=" * 60)
    passed = sum(results.values())
    print(f"Passed: {passed}/{len(results)}")
    if not results["csv"]:
        print("\nNext: add data/salesdaily.csv then run: python scripts/load_data.py")
    elif results["postgres"] and results["mongodb"]:
        print("\nNext: python scripts/load_data.py")
    if results["postgres"] and results["mongodb"] and results["model"]:
        print("Then: uvicorn app.main:app --reload")
        print("Then: python predict_pipeline.py")
    return 0 if results["postgres"] and results["mongodb"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
