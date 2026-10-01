import json
import os
from datetime import datetime
from typing import Any, Dict, List

import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv


load_dotenv()


def _database_config() -> Dict[str, Any]:
    return {
        "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", "1234"),
        "database": os.getenv("MYSQL_DATABASE", "validation_db"),
    }


def get_connection():
    return mysql.connector.connect(**_database_config())


def check_connection() -> bool:
    connection = None
    try:
        connection = get_connection()
        return connection.is_connected()
    except Error:
        return False
    finally:
        if connection is not None and connection.is_connected():
            connection.close()


def _parse_default_value(data_type: str, value: str | None) -> Any:
    if value is None:
        return None

    normalized_type = data_type.lower()
    if normalized_type in {"int", "integer"}:
        return int(value)
    if normalized_type in {"float", "double", "decimal", "number"}:
        return float(value)
    if normalized_type in {"bool", "boolean"}:
        return value.strip().lower() in {"1", "true", "yes", "y"}
    if normalized_type in {"list", "array", "json"}:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return [item.strip() for item in value.split(",") if item.strip()]
    return value


def load_active_rule_pipeline() -> List[Dict[str, Any]]:
    """Load the latest active version of each active rule from MySQL.

    Rules execute in rule_id order because the supplied schema has no sequence
    column. Parameters use validation_rule_parameters.default_value.
    """
    query = """
        SELECT
            r.rule_id,
            r.rule_code,
            m.method_id,
            v.version_id,
            m.method_path,
            p.param_name,
            p.data_type,
            p.default_value,
            p.is_required
        FROM validation_rules AS r
        JOIN validation_rule_versions AS v
          ON v.rule_id = r.rule_id
         AND v.status = 'active'
         AND v.version_id = (
             SELECT MAX(v2.version_id)
             FROM validation_rule_versions AS v2
             WHERE v2.rule_id = r.rule_id
               AND v2.status = 'active'
         )
        JOIN validation_rule_methods AS m ON m.version_id = v.version_id
        LEFT JOIN validation_rule_parameters AS p ON p.method_id = m.method_id
        WHERE r.status = 'active'
        ORDER BY r.rule_id, m.method_id, p.param_id
    """

    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query)

        pipeline_by_rule: Dict[int, Dict[str, Any]] = {}
        for row in cursor.fetchall():
            rule_id = row["rule_id"]
            rule = pipeline_by_rule.setdefault(
                rule_id,
                {
                    "rule_id": row["rule_id"],
                    "rule_code": row["rule_code"],
                    "method_id": row["method_id"],
                    "version_id": row["version_id"],
                    "method_path": row["method_path"],
                    "parameters": {},
                },
            )
            if row["param_name"] is not None and row["default_value"] is not None:
                rule["parameters"][row["param_name"]] = _parse_default_value(
                    row["data_type"], row["default_value"]
                )
            elif row["param_name"] is not None and row["is_required"] == "Y":
                raise ValueError(
                    f"Required parameter '{row['param_name']}' has no default value "
                    f"for rule {row['rule_code']}"
                )

        return list(pipeline_by_rule.values())
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def list_active_rules() -> List[Dict[str, Any]]:
    query = """
        SELECT r.rule_id, r.rule_code, r.rule_name, r.description,
               r.severity_level, c.category_name
        FROM validation_rules AS r
        LEFT JOIN validation_categories AS c ON c.category_id = r.category_id
        WHERE r.status = 'active'
        ORDER BY r.rule_id
    """

    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query)
        return cursor.fetchall()
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def get_active_rule(rule_id: str) -> Dict[str, Any] | None:
    query = """
        SELECT r.rule_id, r.rule_code, r.rule_name, r.description,
               r.severity_level, c.category_name
        FROM validation_rules AS r
        LEFT JOIN validation_categories AS c ON c.category_id = r.category_id
        WHERE r.status = 'active'
          AND (r.rule_code = %s OR CAST(r.rule_id AS CHAR) = %s)
        LIMIT 1
    """

    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, (rule_id, rule_id))
        return cursor.fetchone()
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def list_validation_logs(limit: int, offset: int) -> List[Dict[str, Any]]:
    query = """
        SELECT l.log_id AS id,
               l.request_id AS record_id,
               r.rule_code AS rule_id,
               CASE WHEN l.failed_record_count = 0 THEN TRUE ELSE FALSE END AS passed,
               CASE
                   WHEN l.failed_record_count = 0 THEN NULL
                   ELSE CONCAT('Validation failed for ', l.failed_record_count, ' record(s)')
               END AS message,
               l.ended_at AS created_at
        FROM validation_logic_logs AS l
        JOIN validation_rules AS r ON r.rule_id = l.rule_id
        ORDER BY l.ended_at DESC, l.log_id DESC
        LIMIT %s OFFSET %s
    """

    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, (limit, offset))
        return cursor.fetchall()
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def find_active_rule_metadata(rule_code: str, method_path: str) -> Dict[str, int]:
    query = """
        SELECT r.rule_id, m.method_id, v.version_id
        FROM validation_rules AS r
        JOIN validation_rule_versions AS v
          ON v.rule_id = r.rule_id AND v.status = 'active'
        JOIN validation_rule_methods AS m ON m.version_id = v.version_id
        WHERE r.rule_code = %s
          AND r.status = 'active'
          AND m.method_path = %s
        ORDER BY v.version_id DESC
        LIMIT 1
    """

    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, (rule_code, method_path))
        row = cursor.fetchone()
        if row is None:
            raise ValueError(
                f"No active database metadata found for rule '{rule_code}' "
                f"and method '{method_path}'"
            )
        return {
            "rule_id": row["rule_id"],
            "method_id": row["method_id"],
            "version_id": row["version_id"],
        }
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def write_validation_log(
    *,
    rule_id: int,
    method_id: int,
    version_id: int,
    request_id: str,
    input_record_count: int,
    passed_record_count: int,
    failed_record_count: int,
    started_at: datetime,
    ended_at: datetime,
    triggered_by: str = "api",
) -> None:
    if failed_record_count == 0:
        quarantine_status = "passed"
        execution_status = "success"
    elif passed_record_count == 0:
        quarantine_status = "discarded"
        execution_status = "failed"
    else:
        quarantine_status = "quarantined"
        execution_status = "partial"

    query = """
        INSERT INTO validation_logic_logs (
            rule_id, method_id, version_id, request_id,
            input_record_count, passed_record_count, failed_record_count,
            quarantine_status, status, started_at, ended_at, triggered_by
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            query,
            (
                rule_id,
                method_id,
                version_id,
                request_id,
                input_record_count,
                passed_record_count,
                failed_record_count,
                quarantine_status,
                execution_status,
                started_at,
                ended_at,
                triggered_by,
            ),
        )
        connection.commit()
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()