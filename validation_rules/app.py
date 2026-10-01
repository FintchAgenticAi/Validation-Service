from pathlib import Path
import sys
import importlib
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field

from validation_rules.database import (
    check_connection,
    get_active_rule,
    find_active_rule_metadata,
    list_active_rules,
    list_validation_logs,
    load_active_rule_pipeline,
    write_validation_log,
)


ROOT_DIR = Path(__file__).resolve().parent
PARENT_DIR = str(ROOT_DIR.parent)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)


# =============================================================================
# FASTAPI APP INITIALIZATION & SWAGGER METADATA
# =============================================================================
app = FastAPI(
    title="Validation Rules Service API",
    description="""
    **Silver Zone Validation Engine API**

    This service executes automated business rules and data integrity checks on financial ingestion payloads.

    * **Integrity Checks:** Non-null validation.
    * **Business Rules:** Maximum-length and allowed-values checks.
    * **Quarantine Handling:** Separates clean records from corrupted rows.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# =============================================================================
# PYDANTIC SCHEMAS FOR SWAGGER UI
# =============================================================================


class FinancialRecord(BaseModel):
    market_timestamp: Optional[str] = Field(
        default="2026-08-04 10:00:00", description="Timestamp of transaction"
    )
    asset_symbol: Optional[str] = Field(default="AAPL", description="Ticker or ISIN identifier")
    price: Optional[float] = Field(default=185.50, description="Numerical transaction price")
    currency: Optional[str] = Field(default="USD", description="ISO 4217 Currency Code")

    class Config:
        json_schema_extra = {
            "example": {
                "market_timestamp": "2026-08-04 10:00:00",
                "asset_symbol": "AAPL",
                "price": 185.50,
                "currency": "USD",
            }
        }


class RuleConfiguration(BaseModel):
    rule_code: str = Field(description="Unique code from validation_rules DB")
    method_path: str = Field(description="Python class path to execute")
    parameters: Dict[str, Any] = Field(description="Dynamic rule parameters")
    rule_id: Optional[int] = None
    method_id: Optional[int] = None
    version_id: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "rule_code": "VR_001_NULL_CHECK",
                "method_path": "validation_rules.rules.business.VR_001_null_check.MandatoryNullCheck",
                "parameters": {"mandatory_columns": ["market_timestamp", "asset_symbol", "price"]},
            }
        }


class ValidationRequest(BaseModel):
    request_id: str = Field(default="REQ-2026-001", description="Unique batch processing request ID")
    records: List[Dict[str, Any]] = Field(description="List of raw ingestion JSON records")
    rule_pipeline: Optional[List[RuleConfiguration]] = Field(
        default=None,
        description="Optional rule sequence; omitted means load active rules from MySQL",
    )

    class Config:
        json_schema_extra = {
            "example": {
                                "request_id": "REQ-2026-0805-002",
                                "records": [
                                        {
                                                "market_timestamp": "2026-08-05 10:00:00",
                                                "asset_symbol": "AAPL",
                                                "price": 185.5,
                                                "currency": "USD",
                                        },
                                        {
                                                "market_timestamp": "2026-08-05 10:01:00",
                                                "asset_symbol": "VERY_LONG_INVALID_SYMBOL_NAME",
                                                "price": 200.0,
                                                "currency": "USD",
                                        },
                                        {
                                                "market_timestamp": None,
                                                "asset_symbol": "MSFT",
                                                "price": 420.0,
                                                "currency": "EUR",
                                        },
                                        {
                                                "market_timestamp": "2026-08-05 10:03:00",
                                                "asset_symbol": "GOOGL",
                                                "price": 175.25,
                                                "currency": "INVALID_CURRENCY",
                                        },
                                ],
                                "rule_pipeline": [
                                        {
                                                "rule_code": "VR_001_NULL_CHECK",
                                                "method_path": "validation_rules.rules.business.VR_001_null_check.MandatoryNullCheck",
                                                "parameters": {"mandatory_columns": ["market_timestamp", "asset_symbol", "price"]},
                                        },
                                        {
                                            "rule_code": "VR_002_MAX_LENGTH_CHECK",
                                            "method_path": "validation_rules.rules.business.VR_002_max_length.MaxLengthCheck",
                                            "parameters": {"target_column": "asset_symbol", "max_length": 5},
                                        },
                                        {
                                            "rule_code": "VR_003_ALLOWED_ENUM_CHECK",
                                            "method_path": "validation_rules.rules.business.VR_003_allowed_values.AllowedValuesCheck",
                                            "parameters": {"target_column": "currency", "allowed_values": ["USD", "EUR", "GBP"]},
                                        },
                                ],
            }
        }


class ValidationResponse(BaseModel):
    request_id: str
    overall_status: str = Field(description="'PASSED', 'PARTIAL_QUARANTINE', or 'ALL_DISCARDED'")
    total_scanned: int
    passed_count: int
    quarantined_count: int
    passed_records: List[Dict[str, Any]]
    quarantined_records: List[Dict[str, Any]]
    execution_metrics: List[Dict[str, Any]]


class BatchRecord(BaseModel):
    record_id: str
    data: Dict[str, Any]


class BatchValidationRequest(BaseModel):
    records: List[BatchRecord]
    check_ids: List[str]


class BatchValidationError(BaseModel):
    rule_id: str
    message: str


class BatchValidationResult(BaseModel):
    record_id: str
    passed: bool
    errors: List[BatchValidationError]


class BatchValidationResponse(BaseModel):
    results: List[BatchValidationResult]


# =============================================================================
# ENDPOINTS
# =============================================================================


@app.get("/api/v1/validation/rules", tags=["Validation Rules"])
def get_rules():
    """Returns all active validation rules."""
    try:
        rules = list_active_rules()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Unable to load validation rules: {exc}")
    return [
        {
            "rule_id": rule["rule_code"],
            "name": rule["rule_name"],
            "description": rule["description"],
        }
        for rule in rules
    ]


@app.get("/api/v1/validation/rules/{rule_id}", tags=["Validation Rules"])
def get_rule(rule_id: str):
    """Returns one active validation rule by numeric ID or rule code."""
    try:
        rule = get_active_rule(rule_id)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Unable to load validation rule: {exc}")
    if rule is None:
        raise HTTPException(status_code=404, detail=f"Validation rule '{rule_id}' was not found")
    return {
        "rule_id": rule["rule_code"],
        "name": rule["rule_name"],
        "description": rule["description"],
    }


@app.get("/health", tags=["System Health"])
def health_check():
    """Returns operational status of the Validation Service API."""
    database_status = "HEALTHY" if check_connection() else "UNAVAILABLE"
    return {
        "status": "HEALTHY" if database_status == "HEALTHY" else "DEGRADED",
        "service": "Validation Rules Service",
        "zone": "Silver",
        "database": database_status,
    }


@app.post(
    "/api/v1/validation/batch",
    response_model=BatchValidationResponse,
    status_code=status.HTTP_200_OK,
    tags=["Validation Execution Engine"],
)
def execute_batch_validation(payload: BatchValidationRequest):
    """Validates each record against the selected active rules."""
    if not payload.records:
        raise HTTPException(status_code=400, detail="Payload contains no data records.")
    if not payload.check_ids:
        raise HTTPException(status_code=400, detail="check_ids must contain at least one rule.")

    try:
        active_pipeline = load_active_rule_pipeline()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Unable to load rules from MySQL: {exc}")

    requested_ids = set(payload.check_ids)
    selected_pipeline = [
        rule for rule in active_pipeline
        if rule["rule_code"] in requested_ids or str(rule["rule_id"]) in requested_ids
    ]
    if len(selected_pipeline) != len(requested_ids):
        available_ids = {rule["rule_code"] for rule in active_pipeline}
        available_ids.update(str(rule["rule_id"]) for rule in active_pipeline)
        unknown_ids = sorted(requested_ids - available_ids)
        raise HTTPException(status_code=404, detail=f"Unknown validation rule(s): {unknown_ids}")

    results = []
    for record in payload.records:
        validation = execute_validation_pipeline(
            ValidationRequest(
                request_id=record.record_id,
                records=[record.data],
                rule_pipeline=[RuleConfiguration(**rule) for rule in selected_pipeline],
            )
        )
        errors = [
            BatchValidationError(
                rule_id=item.get("failed_rule_code", "unknown"),
                message=f"Validation failed for rule {item.get('failed_rule_code', 'unknown')}",
            )
            for item in validation.quarantined_records
        ]
        results.append(
            BatchValidationResult(
                record_id=record.record_id,
                passed=not errors,
                errors=errors,
            )
        )
    return BatchValidationResponse(results=results)


@app.get("/api/v1/validation/logs", tags=["Validation Logs"])
def get_logs(
    limit: int = Query(default=50, gt=0),
    offset: int = Query(default=0, ge=0),
):
    """Returns recent validation execution logs."""
    try:
        return list_validation_logs(limit=limit, offset=offset)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Unable to load validation logs: {exc}")


@app.post(
    "/api/v1/validation/execute",
    response_model=ValidationResponse,
    status_code=status.HTTP_200_OK,
    tags=["Validation Execution Engine"],
)
def execute_validation_pipeline(payload: ValidationRequest):
    """
    **Executes the Business Rule & Integrity Validation Pipeline.**

    1. Converts incoming payload into a Pandas DataFrame.
    2. Dynamically loads rule classes from parameters.
    3. Evaluates dataset against the configured null, max-length, and allowed-values rules.
    4. Segregates clean records (for Gold Zone) from quarantined rows (for error logging).
    """
    if not payload.records:
        raise HTTPException(status_code=400, detail="Payload contains no data records.")

    rule_pipeline = payload.rule_pipeline
    if rule_pipeline is None:
        try:
            rule_pipeline = [RuleConfiguration(**rule) for rule in load_active_rule_pipeline()]
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"Unable to load rules from MySQL: {exc}")

    raw_df = pd.DataFrame(payload.records)
    current_valid_df = raw_df.copy()
    quarantined_df = pd.DataFrame()
    metrics_log = []

    for rule_config in rule_pipeline:
        started_at = datetime.now()
        try:
            if not (rule_config.rule_id and rule_config.method_id and rule_config.version_id):
                metadata = find_active_rule_metadata(
                    rule_config.rule_code,
                    rule_config.method_path,
                )
                rule_config.rule_id = metadata["rule_id"]
                rule_config.method_id = metadata["method_id"]
                rule_config.version_id = metadata["version_id"]

            module_name, class_name = rule_config.method_path.rsplit(".", 1)
            module = importlib.import_module(module_name)
            rule_class = getattr(module, class_name)
            rule_instance = rule_class()

            passed_df, failed_df, metrics = rule_instance.apply(current_valid_df, rule_config.parameters)

            if not failed_df.empty:
                failed_df["failed_rule_code"] = rule_config.rule_code
                quarantined_df = pd.concat([quarantined_df, failed_df], ignore_index=True)

            current_valid_df = passed_df
            metrics_log.append(metrics)

            if rule_config.rule_id and rule_config.method_id and rule_config.version_id:
                write_validation_log(
                    rule_id=rule_config.rule_id,
                    method_id=rule_config.method_id,
                    version_id=rule_config.version_id,
                    request_id=payload.request_id,
                    input_record_count=metrics["total_scanned"],
                    passed_record_count=metrics["passed_count"],
                    failed_record_count=metrics["failed_count"],
                    started_at=started_at,
                    ended_at=datetime.now(),
                )

            if current_valid_df.empty:
                break

        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Execution error on rule {rule_config.rule_code}: {str(exc)}",
            )

    passed_count = len(current_valid_df)
    quarantined_count = len(quarantined_df)

    if quarantined_count == 0:
        overall_status = "PASSED"
    elif passed_count > 0:
        overall_status = "PARTIAL_QUARANTINE"
    else:
        overall_status = "ALL_DISCARDED"

    return ValidationResponse(
        request_id=payload.request_id,
        overall_status=overall_status,
        total_scanned=len(raw_df),
        passed_count=passed_count,
        quarantined_count=quarantined_count,
        passed_records=current_valid_df.to_dict(orient="records"),
        quarantined_records=quarantined_df.to_dict(orient="records") if not quarantined_df.empty else [],
        execution_metrics=metrics_log,
    )