# Validation Rules Service

![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.x-4479A1?logo=mysql&logoColor=white)

FastAPI service for validating financial ingestion records against database-configured business and integrity rules.

The service loads active rules and their parameters from MySQL, executes Python rule classes dynamically, separates passed records from quarantined records, and writes execution logs back to MySQL.

## Features

- Database-backed validation rule catalog and versioning
- Dynamic rule pipeline execution
- Batch validation with selected rule IDs
- Quarantine reporting for failed records
- Validation execution metrics and logs
- OpenAPI documentation through Swagger UI and ReDoc

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn asgi:app --reload
```

Open `http://127.0.0.1:8000/docs` to explore and call the API.

## Requirements

- Python 3.10 or newer
- MySQL 8.x (or a compatible MySQL server)
- An existing `validation_db` schema containing the validation tables used by the seed scripts

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a `.env` file in the project root when the default database settings are not suitable:

```dotenv
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your-password
MYSQL_DATABASE=validation_db
```

The application defaults are host `127.0.0.1`, port `3306`, user `root`, database `validation_db`, and password `1234`. Change the default password before using the service outside a local development environment.

## Database Setup

The repository contains two seed files for different rule catalog versions. Apply **one** seed file to an initialized `validation_db` schema; do not apply both to the same database unless you have verified that their rule codes and schema constraints are compatible.

For the current database-backed pipeline used by the API examples:

```sql
SOURCE database_seed.sql;
```

The seed data registers the initial executable rules, active versions, Python method paths, and default parameters. `rules_seed.sql` is an extended alternative catalog containing the broader `VR_001` through `VR_013` rule set.

Ensure the database schema and its validation tables exist before applying a seed file. The seed files populate data; they do not create the schema.

## Running the Service

From the project root:

```powershell
uvicorn asgi:app --reload
```

The service is available at `http://127.0.0.1:8000`.

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- Health check: `http://127.0.0.1:8000/health`

## API Endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Reports service and database status |
| `GET` | `/api/v1/validation/rules` | Lists active validation rules |
| `GET` | `/api/v1/validation/rules/{rule_id}` | Gets an active rule by numeric ID or rule code |
| `POST` | `/api/v1/validation/execute` | Executes a configured or database-loaded pipeline |
| `POST` | `/api/v1/validation/batch` | Validates records against selected active rules |
| `GET` | `/api/v1/validation/logs` | Returns recent execution logs with pagination |

## Example: Execute a Pipeline

When `rule_pipeline` is omitted, active rules and their parameters are loaded from MySQL.

```powershell
$body = @{
    request_id = "REQ-2026-001"
    records = @(
        @{
            market_timestamp = "2026-08-05 10:00:00"
            asset_symbol = "AAPL"
            price = 185.50
            currency = "USD"
        }
    )
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
    -Uri http://127.0.0.1:8000/api/v1/validation/execute `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

The response includes `overall_status`, counts, `passed_records`, `quarantined_records`, and per-rule `execution_metrics`. Possible overall statuses are `PASSED`, `PARTIAL_QUARANTINE`, and `ALL_DISCARDED`.

## Project Structure

```text
asgi.py                         ASGI application entry point
requirements.txt                Python dependencies
database_seed.sql               Initial executable rule configuration
rules_seed.sql                  Extended validation rule catalog
validation_rules/
  app.py                        FastAPI application and endpoints
  database.py                   MySQL access and rule/log persistence
  base/base_rule.py             Base interface for validation rules
  engine/integrity_validator.py Rule pipeline engine
  rules/business/               Individual validation rule implementations
```

Each rule implements `BaseValidationRule.apply()` and returns passed records, failed records, and execution metrics.

## Example: Batch Validation

Use `check_ids` with either active rule codes or numeric rule IDs returned by the rules endpoint.

```json
{
    "records": [
        {
            "record_id": "REC-001",
            "data": {
                "market_timestamp": "2026-08-05 10:00:00",
                "asset_symbol": "AAPL",
                "price": 185.5,
                "currency": "USD"
            }
        }
    ],
    "check_ids": ["VR_001", "VR_002"]
}
```

Each result reports whether the record passed and lists the rules that failed.

## Error Responses

- `400 Bad Request`: missing records or an empty rule selection
- `404 Not Found`: requested rule does not exist or is not active
- `500 Internal Server Error`: rule execution failed
- `503 Service Unavailable`: MySQL is unavailable or rule metadata cannot be loaded

