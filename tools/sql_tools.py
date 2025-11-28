#!/usr/bin/python3

import os
from typing import List, Dict, Any

import duckdb

# Path to your DuckDB file
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "function.duckdb")


def _success(data: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to wrap successful tool results in ADK-style envelope."""
    return {
        "status": "success",
        "data": data,
        "error_message": None,
    }


def _error(message: str) -> Dict[str, Any]:
    """Helper to wrap error results in ADK-style envelope."""
    return {
        "status": "error",
        "data": None,
        "error_message": message,
    }


def run_duckdb_query(sql: str, max_rows: int = 1000) -> Dict[str, Any]:
    """
    Run a read-only SQL query against the fungal DuckDB database.

    Args:
        sql: SQL query string. Should be a SELECT or other read-only query.
        max_rows: Maximum number of rows to return.

    Returns:
        ADK-style result dict:
        {
          "status": "success" | "error",
          "data": {
            "columns": [str, ...],
            "rows": [ {col: value, ...}, ... ],
            "row_count": int
          } | None,
          "error_message": str | None
        }

    Behavior:
        - Rejects destructive SQL (DROP/DELETE/UPDATE/INSERT/ALTER/TRUNCATE).
        - On any error, returns status="error" with an error_message instead of raising.
    """
    try:
        if not os.path.exists(DB_PATH):
            return _error(f"DuckDB file not found at {DB_PATH}")

        lowered = f" {sql.lower()} "
        forbidden = [" drop ", " delete ", " update ", " insert ", " alter ", " truncate "]
        if any(word in lowered for word in forbidden):
            return _error("Destructive SQL (DROP/DELETE/UPDATE/INSERT/ALTER/TRUNCATE) is not allowed.")

        con = duckdb.connect(DB_PATH, read_only=True)
        try:
            cursor = con.execute(sql)
            data = cursor.fetchmany(max_rows)
            col_names = [d[0] for d in cursor.description] if cursor.description else []

            rows: List[Dict[str, Any]] = [
                {col_names[i]: value for i, value in enumerate(row)}
                for row in data
            ]

            return _success(
                {
                    "columns": col_names,
                    "rows": rows,
                    "row_count": len(rows),
                }
            )
        finally:
            con.close()
    except Exception as e:
        return _error(str(e))


def list_tables() -> Dict[str, Any]:
    """
    List all tables in the DuckDB database using information_schema.tables.

    Returns:
        ADK-style result dict:
        {
          "status": "success" | "error",
          "data": {
            "tables": [ {"table_name": str, "table_type": str}, ... ]
          } | None,
          "error_message": str | None
        }
    """
    try:
        if not os.path.exists(DB_PATH):
            return _error(f"DuckDB file not found at {DB_PATH}")

        con = duckdb.connect(DB_PATH, read_only=True)
        try:
            sql = """
            SELECT table_name, table_type
            FROM information_schema.tables
            WHERE table_schema = 'main'
            ORDER BY table_name
            """
            cursor = con.execute(sql)
            rows = cursor.fetchall()
            cols = [d[0] for d in cursor.description]

            table_rows = [
                {cols[i]: value for i, value in enumerate(row)}
                for row in rows
            ]

            return _success({"tables": table_rows})
        finally:
            con.close()
    except Exception as e:
        return _error(str(e))


def describe_table(table_name: str, max_columns: int = 200) -> Dict[str, Any]:
    """
    Describe columns for a given table in the 'main' schema.

    Args:
        table_name: Name of the table.
        max_columns: Safety cap on number of columns returned.

    Returns:
        ADK-style result dict:
        {
          "status": "success" | "error",
          "data": {
            "table_name": str,
            "columns": [ {"column_name": str, "data_type": str}, ... ]
          } | None,
          "error_message": str | None
        }
    """
    try:
        if not os.path.exists(DB_PATH):
            return _error(f"DuckDB file not found at {DB_PATH}")

        con = duckdb.connect(DB_PATH, read_only=True)
        try:
            sql = """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'main'
              AND table_name = ?
            ORDER BY ordinal_position
            """
            cursor = con.execute(sql, [table_name])
            rows = cursor.fetchmany(max_columns)
            cols = [d[0] for d in cursor.description]

            col_rows = [
                {cols[i]: value for i, value in enumerate(row)}
                for row in rows
            ]

            return _success(
                {
                    "table_name": table_name,
                    "columns": col_rows,
                }
            )
        finally:
            con.close()
    except Exception as e:
        return _error(str(e))

