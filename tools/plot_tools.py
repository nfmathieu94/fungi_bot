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
    hue: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a simple plot from tabular data.

    Args:
        rows: List of row dicts (typically from run_duckdb_query["data"]["rows"]).
        columns: List of column names (run_duckdb_query["data"]["columns"]).
        kind: Type of plot. One of: "hist", "scatter", "box".
        x: Column name for x-axis.
        y: Column name for y-axis (required for "scatter" and "box").
        title: Optional plot title.
        log_x: Whether to use log scale on x-axis.
        log_y: Whether to use log scale on y-axis.
        bins: Number of bins for histograms.
        hue: Optional column name used for grouping/colors (for "scatter" and "box").

    Returns:
        ADK-style result dict:
        {
          "status": "success" | "error",
          "data": {
            "image_path": str,
            "kind": str,
            "x": str,
            "y": str | None,
            "hue": str | None,
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
        for col in [x, y, hue]:
            if col is not None and col not in df.columns:
                return _error(
                    f"Requested column '{col}' not found in data. "
                    f"Available: {list(df.columns)}"
                )

        os.makedirs(FIG_DIR, exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        fname_parts = [kind, x]
        if y:
            fname_parts.append(f"vs_{y}")
        if hue:
            fname_parts.append(f"by_{hue}")
        fname = "_".join(fname_parts) + f"_{timestamp}.png"
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

            if hue is not None:
                # Color by category in hue
                categories = df.loc[mask, hue].astype(str)
                # Assign a color index per category
                cat_codes, uniques = pd.factorize(categories)
                scatter = plt.scatter(
                    x_data[mask],
                    y_data[mask],
                    c=cat_codes,
                    alpha=0.6,
                )
                # Add a legend with category labels
                handles, _ = scatter.legend_elements(num=len(uniques))
                plt.legend(handles, list(uniques), title=hue)
            else:
                plt.scatter(x_data[mask], y_data[mask], alpha=0.6)

            plt.xlabel(x)
            plt.ylabel(y)

        elif kind == "box":
            if y is None:
                return _error("Box plot requires both x (category) and y (numeric).")

            y_num = pd.to_numeric(df[y], errors="coerce")
            # Keep rows with valid numeric y
            plot_df = df.copy()
            plot_df[y] = y_num
            plot_df = plot_df.dropna(subset=[y])

            if plot_df.empty:
                return _error(
                    f"No valid numeric data found in column '{y}' for box plot."
                )

            if hue is not None:
                # Grouped boxplot: hue as additional category dimension
                # For simplicity, build a combined category for x+hue
                plot_df["_group"] = plot_df[x].astype(str) + " | " + plot_df[hue].astype(
                    str
                )
                plot_df.boxplot(column=y, by="_group", rot=90)
                plt.xlabel(f"{x} | {hue}")
            else:
                plot_df.boxplot(column=y, by=x, rot=90)
                plt.xlabel(x)

            plt.ylabel(y)
            plt.suptitle("")  # Remove default pandas boxplot title

        else:
            return _error(
                f"Unsupported plot kind '{kind}'. Supported kinds: 'hist', 'scatter', 'box'."
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
                "hue": hue,
                "n_points": len(df),
            }
        )
    except Exception as e:
        return _error(str(e))

