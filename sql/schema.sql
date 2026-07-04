-- Pharma Time-Series Pipeline — PostgreSQL Schema (Task 2)
-- Dataset: Kaggle Pharma Sales Data (daily ATC category units sold)
-- Run against your Supabase/Aiven/Neon database (database must already exist).

-- Table 1: Medicine / ATC category reference
CREATE TABLE IF NOT EXISTS medicines (
    medicine_id   VARCHAR(10)  PRIMARY KEY,
    name          VARCHAR(120) NOT NULL,
    description   TEXT,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Table 2: One row per calendar day (time-series anchor)
CREATE TABLE IF NOT EXISTS daily_records (
    record_id     SERIAL       PRIMARY KEY,
    sale_date     DATE         NOT NULL UNIQUE,
    total_demand  NUMERIC(12, 2) NOT NULL DEFAULT 0,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_daily_records_sale_date ON daily_records (sale_date);

-- Table 3: Per-category demand metrics linked to each daily record
CREATE TABLE IF NOT EXISTS category_sales (
    metric_id     SERIAL       PRIMARY KEY,
    record_id     INTEGER      NOT NULL REFERENCES daily_records(record_id) ON DELETE CASCADE,
    medicine_id   VARCHAR(10)  NOT NULL REFERENCES medicines(medicine_id),
    units_sold    NUMERIC(12, 2) NOT NULL,
    UNIQUE (record_id, medicine_id)
);

CREATE INDEX IF NOT EXISTS idx_category_sales_medicine ON category_sales (medicine_id);

-- Seed ATC categories
INSERT INTO medicines (medicine_id, name, description) VALUES
    ('M01AB', 'M01AB', 'Anti-inflammatory — acetic acid derivatives'),
    ('M01AE', 'M01AE', 'Anti-inflammatory — propionic acid derivatives'),
    ('N02BA', 'N02BA', 'Analgesics — salicylic acid derivatives'),
    ('N02BE', 'N02BE', 'Analgesics — pyrazolones and anilides (Paracetamol)'),
    ('N05B',  'N05B',  'Psycholeptics — anxiolytics'),
    ('N05C',  'N05C',  'Psycholeptics — hypnotics and sedatives'),
    ('R03',   'R03',   'Drugs for obstructive airway diseases'),
    ('R06',   'R06',   'Antihistamines for systemic use')
ON CONFLICT (medicine_id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description;
