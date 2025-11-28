#!/usr/bin/python3

import os
from typing import List, Dict, Any, Optional

import pandas as pd


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


def summarize_numeric_columns(
    rows: List[Dict[str, Any]],
    columns: List[str],
    column_names: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Compute basic summary statistics for numeric columns.

    Args:
        rows: List of row dicts (typically from run_duckdb_query["data"]["rows"]).
        columns: List of column names (run_duckdb_query["data"]["columns"]).
        column_names: Optional subset of column names to summarize. If None,
                      summarize all numeric columns.

    Returns:
        ADK-style result dict:
        {
          "status": "success" | "error",
          "data": {
            "summaries": {
               <column_name>: {
                  "count": int,
                  "mean": float,
                  "std": float,
                  "min": float,
                  "max": float,
                  "median": float,
                  "n_missing": int
               },
               ...
            }
          } | None,
          "error_message": str | None
        }
    """
    try:
        if not rows:
            return _error("No data rows provided for summarization.")

        df = pd.DataFrame(rows)

        # If user specified columns, restrict to those
        if column_names is not None:
            missing = [c for c in column_names if c not in df.columns]
            if missing:
                return _error(
                    f"Requested columns {missing} not found in data. "
                    f"Available: {list(df.columns)}"
                )
            df = df[column_names]

        # Keep only numeric columns
        num_df = df.apply(pd.to_numeric, errors="coerce")
        numeric_cols = [
            c for c in num_df.columns if pd.api.types.is_numeric_dtype(num_df[c])
        ]
        if not numeric_cols:
            return _error("No numeric columns available for summarization.")

        summaries: Dict[str, Dict[str, Any]] = {}

        for col in numeric_cols:
            series = num_df[col]
            non_na = series.dropna()
            if non_na.empty:
                # Skip columns with no valid numeric data
                continue

            summaries[col] = {
                "count": int(non_na.count()),
                "mean": float(non_na.mean()),
                "std": float(non_na.std(ddof=1)) if non_na.count() > 1 else 0.0,
                "min": float(non_na.min()),
                "max": float(non_na.max()),
                "median": float(non_na.median()),
                "n_missing": int(series.isna().sum()),
            }

        if not summaries:
            return _error("No numeric columns contained valid data for summarization.")

        return _success({"summaries": summaries})
    except Exception as e:
        return _error(str(e))


def compute_correlation(
    rows: List[Dict[str, Any]],
    columns: List[str],
    x: str,
    y: str,
    method: str = "pearson",
) -> Dict[str, Any]:
    """
    Compute correlation between two numeric columns.

    Args:
        rows: List of row dicts (typically from run_duckdb_query["data"]["rows"]).
        columns: List of column names (run_duckdb_query["data"]["columns"]).
        x: Name of the first column.
        y: Name of the second column.
        method: Correlation method; one of "pearson", "spearman".

    Returns:
        ADK-style result dict:
        {
          "status": "success" | "error",
          "data": {
            "x": str,
            "y": str,
            "method": str,
            "correlation": float,
            "n_points": int
          } | None,
          "error_message": str | None
        }
    """
    try:
        if not rows:
            return _error("No data rows provided for correlation.")

        df = pd.DataFrame(rows)

        for col in [x, y]:
            if col not in df.columns:
                return _error(
                    f"Requested column '{col}' not found in data. "
                    f"Available: {list(df.columns)}"
                )

        x_data = pd.to_numeric(df[x], errors="coerce")
        y_data = pd.to_numeric(df[y], errors="coerce")
        mask = x_data.notna() & y_data.notna()
        if mask.sum() < 2:
            return _error(
                f"Not enough valid numeric data to compute correlation between '{x}' and '{y}'."
            )

        valid_df = pd.DataFrame({x: x_data[mask], y: y_data[mask]})

        method = method.lower()
        if method not in ("pearson", "spearman"):
            return _error(f"Unsupported method '{method}'. Use 'pearson' or 'spearman'.")

        corr = valid_df[x].corr(valid_df[y], method=method)

        return _success(
            {
                "x": x,
                "y": y,
                "method": method,
                "correlation": float(corr),
                "n_points": int(mask.sum()),
            }
        )
    except Exception as e:
        return _error(str(e))

