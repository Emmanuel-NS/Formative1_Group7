# Pharma Time-Series Pipeline — Formative 1 (GRP7)

End-to-end time-series pipeline for pharmaceutical daily sales forecasting: **EDA & modeling (Colab)**, **PostgreSQL + MongoDB**, **FastAPI CRUD**, and **prediction script**.

## Project structure

```
Formative1_GRP7/
├── app/                    # FastAPI application (Task 3)
│   ├── main.py             # API entry point
│   ├── config.py           # Environment configuration
│   ├── database.py         # PostgreSQL + MongoDB connections
│   ├── preprocessing.py    # Feature engineering (Task 4)
│   ├── schemas.py          # Request/response models
│   └── repositories/       # SQL and MongoDB data access
├── notebooks/              # Google Colab notebook (Task 1)
├── sql/                    # PostgreSQL schema, queries, ERD (Task 2)
├── mongo/                  # MongoDB design + sample documents (Task 2)
├── scripts/
│   ├── load_data.py        # Load salesdaily.csv into both DBs
│   └── run_queries.py      # Print example query results for report
├── predict_pipeline.py     # End-to-end forecast script (Task 4)
├── data/                   # Place salesdaily.csv here
├── pharma_demand_model.pkl # Download from Colab after Task 1
├── requirements.txt
└── .env.example
```

## Prerequisites

- Python 3.10+
- Free **PostgreSQL** cloud instance (Supabase, Aiven, Neon, etc.)
- Free **MongoDB Atlas** cluster
- `salesdaily.csv` from [Kaggle Pharma Sales Data](https://www.kaggle.com/datasets/milanzdravkovic/pharma-sales-data)
- `pharma_demand_model.pkl` from the Colab notebook (Task 1)

## Setup

### 1. Clone and install

```bash
git clone <your-repo-url>
cd Formative1_GRP7
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2. Configure environment

```bash
copy .env.example .env
# Edit .env with your PostgreSQL and MongoDB Atlas credentials
```

### 3. Add data files

- Put `salesdaily.csv` in `data/`
- Put `pharma_demand_model.pkl` in the project root (after running Colab)

### 4. Initialize databases

```bash
python scripts/load_data.py
```

### 5. Run example queries (for PDF report screenshots)

```bash
python scripts/run_queries.py
```

### 6. Start the API

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000/docs** for interactive Swagger UI.

## API endpoints (Task 3)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Check API + database connectivity |
| POST | `/api/records` | Create record in **PostgreSQL + MongoDB** |
| GET | `/api/records/{id}` | Get record by date (`YYYY-MM-DD`) or PostgreSQL id |
| PUT | `/api/records/{id}` | Update record in both databases |
| DELETE | `/api/records/{id}` | Delete from both databases |
| GET | `/api/records/latest` | Latest timestamped record |
| GET | `/api/records/range?start_date=&end_date=` | Records in date range |

### Example: create a record

```bash
curl -X POST http://127.0.0.1:8000/api/records ^
  -H "Content-Type: application/json" ^
  -d "{\"sale_date\":\"2019-12-30\",\"categories\":{\"M01AB\":10,\"M01AE\":5,\"N02BA\":20,\"N02BE\":100,\"N05B\":15,\"N05C\":12,\"R03\":30,\"R06\":25}}"
```

## Prediction pipeline (Task 4)

With the API running:

```bash
python predict_pipeline.py
```

Expected output:

```
Predicted N02BE demand for next day: 420.00 units
```

## Task 1A-1B Draft Summary

The dataset used for this project is the Kaggle pharmaceutical daily sales time series. It spans roughly **2014 to 2019** and has **daily granularity** with one observation per calendar day. The target variable is **N02BE daily demand**, while the other ATC categories are used as supporting variables for analysis and feature engineering.

Missing values and calendar gaps were handled by reindexing the data to a complete daily date range, applying **time-based linear interpolation** to numeric columns, and using **forward-fill** for any remaining edge cases. This was chosen to preserve the chronological structure of the series and keep the time index regular for lag and moving-average features.

The five analytical questions explored in Task 1B were:

1. **Long-term trend**: Is N02BE demand increasing or decreasing over time?
2. **Cross-category correlation**: Do other ATC categories move together with N02BE demand?
3. **Lag effects**: How strongly do 1-day, 3-day, 7-day, 14-day, and 30-day lags relate to today’s demand?
4. **7-day moving average**: How does a short rolling average smooth daily volatility?
5. **Seasonal / monthly surges**: Are there months with clearly higher demand, and how do 7-day and 30-day moving averages compare?

## Task 2 Draft Summary

For Task 2, the same pharmaceutical sales dataset was modeled in two database formats. The PostgreSQL design uses a normalized structure with separate tables for daily records, category-level sales, and medicine references so the time series can be queried cleanly and expanded later. The MongoDB design stores each day as a single document with a nested `categories` object, which makes it easier to read or update a full daily snapshot at once.

The database work also includes supporting artifacts for the report: an ERD for the relational model, SQL schema scripts, a MongoDB collection design, sample documents, and example queries for both systems. The main goal is to show how the same time-series data can support both relational and document-based storage patterns.

## Task checklist

| Task | Location | Status |
|------|----------|--------|
| 1A–1C EDA & modeling | `notebooks/pharma_time_series_eda_modeling.ipynb` | Run in Colab |
| 2A SQL schema + ERD | `sql/schema.sql`, `sql/ERD.md` | Ready |
| 2B MongoDB design | `mongo/README.md`, `mongo/sample_documents.json` | Ready |
| 2C Example queries | `sql/queries.sql`, `scripts/run_queries.py` | Ready |
| 3 CRUD API | `app/main.py` | Ready |
| 4 Forecast script | `predict_pipeline.py` | Ready |

## Team workflow

1. **Person A** — Run Colab, export model, write Task 1 report section
2. **Person B** — Set up PostgreSQL (Supabase), run schema + queries
3. **Person C** — Set up MongoDB Atlas, verify documents
4. **Person D** — FastAPI testing, `predict_pipeline.py`, README

Each member should make **at least 4 commits** with clear messages.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `Can't connect to PostgreSQL` | Check `.env` credentials; whitelist your IP on Supabase/Aiven |
| `MongoDB SSL error` | Use full Atlas connection string with `mongodb+srv://` |
| `Model not found` | Download `pharma_demand_model.pkl` from Colab |
| `Not enough history` | Run `python scripts/load_data.py` first |
| `404 on /api/records/latest` | Database is empty — load CSV data |

## License

Academic project — dataset © Milan Zdravković (CC BY-NC 4.0).
