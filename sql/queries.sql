-- Task 2: Example PostgreSQL queries (run after loading data via scripts/load_data.py)

-- Query 1: Latest daily record with category breakdown
SELECT
    dr.record_id,
    dr.sale_date,
    dr.total_demand,
    m.medicine_id,
    m.name,
    cs.units_sold
FROM daily_records dr
JOIN category_sales cs ON dr.record_id = cs.record_id
JOIN medicines m ON cs.medicine_id = m.medicine_id
WHERE dr.sale_date = (SELECT MAX(sale_date) FROM daily_records)
ORDER BY cs.units_sold DESC;

-- Query 2: Records within a date range
SELECT
    dr.sale_date,
    dr.total_demand,
    SUM(CASE WHEN cs.medicine_id = 'N02BE' THEN cs.units_sold ELSE 0 END) AS n02be_units
FROM daily_records dr
LEFT JOIN category_sales cs ON dr.record_id = cs.record_id
WHERE dr.sale_date BETWEEN DATE '2017-01-01' AND DATE '2017-01-31'
GROUP BY dr.record_id, dr.sale_date, dr.total_demand
ORDER BY dr.sale_date;

-- Query 3: Monthly average demand for top category (N02BE)
SELECT
    EXTRACT(YEAR FROM dr.sale_date)::INT  AS yr,
    EXTRACT(MONTH FROM dr.sale_date)::INT AS mo,
    ROUND(AVG(cs.units_sold)::NUMERIC, 2) AS avg_n02be_units
FROM daily_records dr
JOIN category_sales cs ON dr.record_id = cs.record_id
WHERE cs.medicine_id = 'N02BE'
GROUP BY EXTRACT(YEAR FROM dr.sale_date), EXTRACT(MONTH FROM dr.sale_date)
ORDER BY yr, mo;

-- Query 4: Top 5 days by total pharmacy demand
SELECT sale_date, total_demand
FROM daily_records
ORDER BY total_demand DESC
LIMIT 5;
