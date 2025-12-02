#!/usr/bin/python3

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import duckdb

# Path to a separate DuckDB file JUST for analysis history
DB_PATH = Path(__file__).resolve().parents[1] / "database" / "analysis_history.duckdb"


def _ensure_db() -> duckdb.DuckDBPyConnection:
    """Open the analysis history DB and create the table if needed."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(DB_PATH), read_only=False)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS analysis_history (
            analysis_id       BIGINT,
            app_name          TEXT,
            user_id           TEXT,
            workflow_name     TEXT,
            created_at        TEXT,
            params_json       TEXT,
            summary_text      TEXT,
            result_stats_json TEXT,
            figure_paths_json TEXT,
            tags_json         TEXT
        )
        """
    )
    return conn


def _success(data: Any) -> Dict[str, Any]:
    return {"status": "success", "data": data, "error_message": None}


def _error(message: str) -> Dict[str, Any]:
    return {"status": "error", "data": None, "error_message": message}


def save_analysis_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Persist a single AnalysisRecord dict to the local analysis_history DuckDB.

    Expected record structure (from AnalysisRecord.to_dict()):
      {
        "type": "fungibot_analysis",
        "app_name": str,
        "user_id": str,
        "workflow_name": str,
        "created_at": str,
        "params": {...},
        "summary_text": str,
        "result_stats": {...},
        "figure_paths": [...],
        "tags": [...]
      }
    """
    try:
        conn = _ensure_db()

        params_json = json.dumps(record.get("params", {}))
        result_stats_json = json.dumps(record.get("result_stats", {}))
        figure_paths_json = json.dumps(record.get("figure_paths", []))
        tags_json = json.dumps(record.get("tags", []))

        # Manually compute the next analysis_id
        row = conn.execute(
            "SELECT COALESCE(MAX(analysis_id), 0) + 1 FROM analysis_history"
        ).fetchone()
        next_id = int(row[0]) if row is not None else 1

        conn.execute(
            """
            INSERT INTO analysis_history (
                analysis_id,
                app_name,
                user_id,
                workflow_name,
                created_at,
                params_json,
                summary_text,
                result_stats_json,
                figure_paths_json,
                tags_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                next_id,
                record.get("app_name"),
                record.get("user_id"),
                record.get("workflow_name"),
                record.get("created_at"),
                params_json,
                record.get("summary_text"),
                result_stats_json,
                figure_paths_json,
                tags_json,
            ],
        )

        conn.close()
        return _success({"analysis_id": next_id})

    except Exception as e:
        return _error(f"Failed to save analysis record: {e}")


def list_analysis_history(
    user_id: Optional[str] = None,
    workflow_name: Optional[str] = None,
    limit: int = 20,
) -> Dict[str, Any]:
    """
    List recent analyses, optionally filtered by user_id and/or workflow_name.
    """
    try:
        conn = _ensure_db()

        sql = """
        SELECT
            analysis_id,
            app_name,
            user_id,
            workflow_name,
            created_at,
            summary_text,
            params_json,
            result_stats_json,
            figure_paths_json,
            tags_json
        FROM analysis_history
        """
        conditions = []
        params: List[Any] = []

        if user_id:
            conditions.append("user_id = ?")
            params.append(user_id)
        if workflow_name:
            conditions.append("workflow_name = ?")
            params.append(workflow_name)

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(sql, params).fetchall()
        conn.close()

        records: List[Dict[str, Any]] = []
        for (
            analysis_id,
            app_name_v,
            user_id_v,
            wf_name_v,
            created_at_v,
            summary_text_v,
            params_json,
            result_stats_json,
            figure_paths_json,
            tags_json,
        ) in rows:
            records.append(
                {
                    "analysis_id": int(analysis_id),
                    "app_name": app_name_v,
                    "user_id": user_id_v,
                    "workflow_name": wf_name_v,
                    "created_at": created_at_v,
                    "summary_text": summary_text_v,
                    "params": json.loads(params_json) if params_json else {},
                    "result_stats": json.loads(result_stats_json) if result_stats_json else {},
                    "figure_paths": json.loads(figure_paths_json) if figure_paths_json else [],
                    "tags": json.loads(tags_json) if tags_json else [],
                }
            )

        return _success({"records": records})

    except Exception as e:
        return _error(f"Failed to list analysis history: {e}")


def get_analysis_record(analysis_id: int) -> Dict[str, Any]:
    """
    Retrieve a single analysis record by ID.
    """
    try:
        conn = _ensure_db()
        row = conn.execute(
            """
            SELECT
                analysis_id,
                app_name,
                user_id,
                workflow_name,
                created_at,
                summary_text,
                params_json,
                result_stats_json,
                figure_paths_json,
                tags_json
            FROM analysis_history
            WHERE analysis_id = ?
            """,
            [analysis_id],
        ).fetchone()
        conn.close()

        if row is None:
            return _error(f"No analysis found with id={analysis_id}")

        (
            analysis_id_v,
            app_name_v,
            user_id_v,
            wf_name_v,
            created_at_v,
            summary_text_v,
            params_json,
            result_stats_json,
            figure_paths_json,
            tags_json,
        ) = row

        record = {
            "analysis_id": int(analysis_id_v),
            "app_name": app_name_v,
            "user_id": user_id_v,
            "workflow_name": wf_name_v,
            "created_at": created_at_v,
            "summary_text": summary_text_v,
            "params": json.loads(params_json) if params_json else {},
            "result_stats": json.loads(result_stats_json) if result_stats_json else {},
            "figure_paths": json.loads(figure_paths_json) if figure_paths_json else [],
            "tags": json.loads(tags_json) if tags_json else [],
        }

        return _success({"record": record})

    except Exception as e:
        return _error(f"Failed to get analysis record: {e}")

