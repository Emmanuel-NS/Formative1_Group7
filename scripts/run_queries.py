"""Run and print example PostgreSQL + MongoDB queries for the report (Task 2)."""

import sys
from pathlib import Path

from sqlalchemy import text

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.database import get_mongo_collection, postgres_session


def run_sql_queries():
    print("\n" + "=" * 60)
    print("POSTGRESQL QUERY RESULTS")
    print("=" * 60)

    queries = {
        "Q1 Latest record": """
            SELECT dr.sale_date, dr.total_demand, cs.medicine_id, cs.units_sold
            FROM daily_records dr
            JOIN category_sales cs ON dr.record_id = cs.record_id
            WHERE dr.sale_date = (SELECT MAX(sale_date) FROM daily_records)
            ORDER BY cs.units_sold DESC
            LIMIT 5
        """,
        "Q2 Date range (Jan 2017)": """
            SELECT dr.sale_date, dr.total_demand
            FROM daily_records dr
            WHERE dr.sale_date BETWEEN DATE '2017-01-01' AND DATE '2017-01-31'
            ORDER BY dr.sale_date
            LIMIT 10
        """,
        "Q3 Monthly avg N02BE": """
            SELECT EXTRACT(YEAR FROM dr.sale_date)::INT AS yr,
                   EXTRACT(MONTH FROM dr.sale_date)::INT AS mo,
                   ROUND(AVG(cs.units_sold)::NUMERIC, 2) AS avg_n02be
            FROM daily_records dr
            JOIN category_sales cs ON dr.record_id = cs.record_id
            WHERE cs.medicine_id = 'N02BE'
            GROUP BY EXTRACT(YEAR FROM dr.sale_date), EXTRACT(MONTH FROM dr.sale_date)
            ORDER BY yr, mo
            LIMIT 12
        """,
    }

    with postgres_session() as session:
        for title, query in queries.items():
            print(f"\n--- {title} ---")
            rows = session.execute(text(query)).mappings().all()
            for row in rows:
                print(dict(row))


def run_mongo_queries():
    print("\n" + "=" * 60)
    print("MONGODB QUERY RESULTS")
    print("=" * 60)

    collection = get_mongo_collection()

    print("\n--- Q1 Latest record ---")
    latest = collection.find_one(sort=[("sale_date", -1)])
    if latest:
        latest.pop("_id", None)
        print(latest)

    print("\n--- Q2 Date range (Jan 2017) ---")
    for doc in collection.find(
        {"sale_date": {"$gte": "2017-01-01", "$lte": "2017-01-31"}}
    ).sort("sale_date", 1).limit(5):
        print({"sale_date": doc["sale_date"], "total_demand": doc["total_demand"]})

    print("\n--- Q3 Aggregation: monthly avg N02BE ---")
    pipeline = [
        {
            "$project": {
                "year": {"$substr": ["$sale_date", 0, 4]},
                "month": {"$substr": ["$sale_date", 5, 2]},
                "n02be": "$categories.N02BE",
            }
        },
        {"$group": {"_id": {"year": "$year", "month": "$month"}, "avg_n02be": {"$avg": "$n02be"}}},
        {"$sort": {"_id.year": 1, "_id.month": 1}},
        {"$limit": 12},
    ]
    for row in collection.aggregate(pipeline):
        print(row)


def main():
    run_sql_queries()
    run_mongo_queries()


if __name__ == "__main__":
    main()
