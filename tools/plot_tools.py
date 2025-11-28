#!/usr/bin/python3

import os
import time
from typing import List, Dict, Any, Optional

import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
FIG_DIR = os.path.join(BASE_DIR, "figures")


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


def make_plot(
    rows: List[Dict[str, Any]],
    columns: List[str],
    kind: str,
    x: str,
    y: Optional[str] = None,
    title: Optional[str] = None,
    log_x: bool = False,
    log_y: bool = False,
    bins: int = 30,
) -> Dict[str, Any]:
    """
    Create a simple plot from tabular data.

    Args:
        rows: List of row dicts (typically from run_duckdb_query["data"]["rows"]).
        columns: List of column names (run_duckdb_query["data"]["columns"]).
        kind: Type of plot. One of: "hist", "scatter".
        x: Column name for x-axis.
        y: Column name for y-axis (required for "scatter").
        title: Optional plot title.
        log_x: Whether to use log scale on x-axis.
        log_y: Whether to use log scale on y-axis.
        bins: Number of bins for histograms.

    Returns:
        ADK-style result dict:
        {
          "status": "success" | "error",
          "data": {
            "image_path": str,
            "kind": str,
            "x": str,
            "y": str | None,
            "n_points": int
          } | None,
          "error_message": str | None
        }
    """
    try:
        if not rows:
            return _error("No data rows provided for plotting.")

        df = pd.DataFrame(rows)

        # Validate requested columns
        for col in [x, y]:
            if col is not None and col not in df.columns:
                return _error(
                    f"Requested column '{col}' not found in data. "
                    f"Available: {list(df.columns)}"
                )

        os.makedirs(FIG_DIR, exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        fname = f"{kind}_{x}" + (f"_vs_{y}" if y else "") + f"_{timestamp}.png"
        out_path = os.path.join(FIG_DIR, fname)

        plt.figure(figsize=(8, 6))

        if kind == "hist":
            data = pd.to_numeric(df[x], errors="coerce").dropna()
            if data.empty:
                return _error(f"No valid numeric data found in column '{x}' for histogram.")
            plt.hist(data, bins=bins)
            plt.xlabel(x)
            plt.ylabel("Count")

        elif kind == "scatter":
            if y is None:
                return _error("Scatter plot requires both x and y.")
            x_data = pd.to_numeric(df[x], errors="coerce")
            y_data = pd.to_numeric(df[y], errors="coerce")
            mask = x_data.notna() & y_data.notna()
            if mask.sum() == 0:
                return _error(
                    f"No valid numeric data found for scatter plot with '{x}' and '{y}'."
                )
            plt.scatter(x_data[mask], y_data[mask], alpha=0.6)
            plt.xlabel(x)
            plt.ylabel(y)

        else:
            return _error(
                f"Unsupported plot kind '{kind}'. Supported kinds: 'hist', 'scatter'."
            )

        if title:
            plt.title(title)

        if log_x:
            plt.xscale("log")
        if log_y:
            plt.yscale("log")

        plt.tight_layout()
        plt.savefig(out_path)
        plt.close()

        return _success(
            {
                "image_path": out_path,
                "kind": kind,
                "x": x,
                "y": y,
                "n_points": len(df),
            }
        )
    except Exception as e:
        return _error(str(e))

