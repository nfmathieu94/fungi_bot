#!/usr/bin/python3

import os
from typing import List, Dict, Any

import duckdb

# Path to your DuckDB file
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "function.duckdb")


def run_duckdb_query(sql: str, max_rows: int = 1000) -> Dict[str, Any]:
    """
    Run a read-only SQL query against the fungal DuckDB database.

    Args:
        sql: SQL query string (SELECT or other read-only query).
        max_rows: Maximum number of rows to return.

    Returns:
        dict with:
            - columns: list of column names
            - rows: list of row dicts (col_name -> value)
            - row_count: number of rows returned
    """

    lowered = f" {sql.lower()} "
    forbidden = [" drop ", " delete ", " update ", " insert ", " alter ", " truncate "]
    if any(word in lowered for word in forbidden):
        raise ValueError("Destructive SQL (DROP/DELETE/UPDATE/INSERT/ALTER/TRUNCATE) is not allowed.")

    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"DuckDB file not found at {DB_PATH}")

    con = duckdb.connect(DB_PATH, read_only=True)

    try:
        cursor = con.execute(sql)
        data = cursor.fetchmany(max_rows)
        col_names = [d[0] for d in cursor.description] if cursor.description else []

        rows: List[Dict[str, Any]] = [
            {col_names[i]: value for i, value in enumerate(row)}
            for row in data
        ]

        return {
            "columns": col_names,
            "rows": rows,
            "row_count": len(rows),
        }
    finally:
        con.close()

def list_tables() -> Dict[str, Any]:
    """
    List all tables in the DuckDB database using information_schema.tables.

    Returns:
        dict with:
            - tables: list of {table_name, table_type}
    """
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"DuckDB file not found at {DB_PATH}")

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
        return {
            "tables": [
                {cols[i]: value for i, value in enumerate(row)}
                for row in rows
            ]
        }
    finally:
        con.close()


def describe_table(table_name: str, max_columns: int = 200) -> Dict[str, Any]:
    """
    Describe columns for a given table (name + data type).

    Args:
        table_name: Name of the table in the main schema.
        max_columns: Safety cap on number of columns.

    Returns:
        dict with:
            - table_name
            - columns: list of {column_name, data_type}
    """
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"DuckDB file not found at {DB_PATH}")

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
        return {
            "table_name": table_name,
            "columns": [
                {cols[i]: value for i, value in enumerate(row)}
                for row in rows
            ]
        }
    finally:
        con.close()

