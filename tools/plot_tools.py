#!/usr/bin/python3

import os
import time
from typing import List, Dict, Any, Optional

import pandas as pd
import matplotlib.pyplot as plt

# Base dir = project root (one level above tools/)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
FIG_DIR = os.path.join(BASE_DIR, "figures")


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
        rows: List of row dicts (e.g. output from run_duckdb_query["rows"]).
        columns: List of column names (e.g. run_duckdb_query["columns"]).
        kind: Type of plot. One of: "hist", "scatter".
        x: Column name for x-axis.
        y: Column name for y-axis (required for scatter).
        title: Optional plot title.
        log_x: Whether to use log scale on x.
        log_y: Whether to use log scale on y.
        bins: Number of bins for histograms.

    Returns:
        dict with:
            - image_path: path to the saved PNG file
            - kind: plot kind
            - x: x column
            - y: y column (if any)
            - n_points: number of data points used
    """
    if not rows:
        raise ValueError("No data rows provided for plotting.")

    df = pd.DataFrame(rows)

    # Validate requested columns
    for col in [x, y]:
        if col is not None and col not in df.columns:
            raise ValueError(f"Requested column '{col}' not found in data. Available: {list(df.columns)}")

    os.makedirs(FIG_DIR, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    fname = f"{kind}_{x}" + (f"_vs_{y}" if y else "") + f"_{timestamp}.png"
    out_path = os.path.join(FIG_DIR, fname)

    plt.figure(figsize=(8, 6))

    if kind == "hist":
        # Histogram of a single numeric column
        data = pd.to_numeric(df[x], errors="coerce").dropna()
        if data.empty:
            raise ValueError(f"No valid numeric data found in column '{x}' for histogram.")
        plt.hist(data, bins=bins)
        plt.xlabel(x)
        plt.ylabel("Count")

    elif kind == "scatter":
        if y is None:
            raise ValueError("Scatter plot requires both x and y.")
        x_data = pd.to_numeric(df[x], errors="coerce")
        y_data = pd.to_numeric(df[y], errors="coerce")
        mask = x_data.notna() & y_data.notna()
        if mask.sum() == 0:
            raise ValueError(f"No valid numeric data found for scatter plot with '{x}' and '{y}'.")
        plt.scatter(x_data[mask], y_data[mask], alpha=0.6)
        plt.xlabel(x)
        plt.ylabel(y)

    else:
        raise ValueError(f"Unsupported plot kind '{kind}'. Supported kinds: 'hist', 'scatter'.")

    if title:
        plt.title(title)

    if log_x:
        plt.xscale("log")
    if log_y:
        plt.yscale("log")

    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()

    return {
        "image_path": out_path,
        "kind": kind,
        "x": x,
        "y": y,
        "n_points": len(df),
    }

