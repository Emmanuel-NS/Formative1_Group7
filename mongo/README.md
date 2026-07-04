# MongoDB Collection Design (Task 2)

## Collection: `daily_sales`

Each document stores a **rich daily snapshot** of all ATC category sales — flexible for time-series API reads without joins.

### Document schema

| Field | Type | Description |
|-------|------|-------------|
| `record_id` | string | Primary business key (`YYYY-MM-DD`) |
| `sale_date` | string (ISO date) | Timestamp anchor |
| `total_demand` | float | Sum of all category units |
| `categories` | object | Map of ATC code → units sold |
| `source` | string | Data provenance |
| `created_at` | datetime | Insert timestamp |
| `updated_at` | datetime | Last update (optional) |

### Indexes

- `{ sale_date: 1 }` — date-range queries
- `{ record_id: 1 }` unique — CRUD by ID

See `mongo/sample_documents.json` for examples.
