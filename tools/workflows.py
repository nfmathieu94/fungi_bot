from typing import Dict, Any
import pandas as pd

from .sql_tools import run_duckdb_query
from .stats_tools import summarize_numeric_columns, compute_correlation
from .plot_tools import make_plot
from .history_helpers import AnalysisRecord
from .history_store import save_analysis_record, list_analysis_history, get_analysis_record

def _success(data: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to wrap successful workflow results in ADK-style envelope."""
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

# Testing added history helper to this function 
# Will incorporate the same thing in other workflows after 
def assembly_quality_overview(limit: int = 1000) -> Dict[str, Any]:
    """
    High-level workflow for summarizing assembly quality using asm_stats.

    Steps:
      1. Query N50 and TOTAL_LENGTH from asm_stats with a LIMIT.
      2. Summarize N50 and TOTAL_LENGTH with basic stats.
      3. Compute Pearson correlation between N50 and TOTAL_LENGTH.
      4. Generate:
          - Histogram of N50 (log-scaled x-axis).
          - Scatter plot of N50 vs TOTAL_LENGTH (log-scaled axes).
      5. Return a structured summary including:
          - row_count
          - numeric summaries
          - correlation info
          - plot metadata and image paths
          - any sub-step error messages, without failing the whole workflow.
          - analysis_record: structured summary for long-term history.

    Args:
        limit: Maximum number of rows to pull from asm_stats.

    Returns:
        ADK-style result dict:
        {
          "status": "success" | "error",
          "data": {
            "limit": int,
            "row_count": int,
            "summaries": {...} or None,
            "summaries_error": str or None,
            "correlation": {...} or None,
            "correlation_error": str or None,
            "plots": {
              "n50_hist": {...} or None,
              "n50_hist_error": str or None,
              "n50_vs_total_scatter": {...} or None,
              "n50_vs_total_scatter_error": str or None
            },
            "analysis_record": {...} or None,
            "history_save_status": "success" | "error" | None,
            "history_save_error": str | None
          } | None,
          "error_message": str | None
        }
    """
    # ---- 1) Query data ----
    sql = f"""
    SELECT N50, TOTAL_LENGTH
    FROM asm_stats
    LIMIT {limit}
    """

    query_res = run_duckdb_query(sql=sql, max_rows=limit)
    if query_res.get("status") != "success":
        # If we can't even get the data, fail the workflow.
        return _error(
            f"Failed to query asm_stats: {query_res.get('error_message', 'unknown error')}"
        )

    qdata = query_res.get("data") or {}
    rows = qdata.get("rows", [])
    columns = qdata.get("columns", [])
    row_count = qdata.get("row_count", 0)

    # Prepare containers for results and potential errors
    summaries = None
    summaries_error = None
    correlation = None
    correlation_error = None
    n50_hist = None
    n50_hist_error = None
    n50_vs_total_scatter = None
    n50_vs_total_scatter_error = None

    # ---- 2) Summaries ----
    if rows:
        summ_res = summarize_numeric_columns(
            rows=rows,
            columns=columns,
            column_names=["N50", "TOTAL_LENGTH"],
        )
        if summ_res.get("status") == "success":
            # NOTE: using key "summaries" to match your docstring
            summaries = (summ_res.get("data") or {}).get("summaries") or \
                        (summ_res.get("data") or {}).get("summary")
        else:
            summaries_error = summ_res.get("error_message")
    else:
        summaries_error = "No rows returned from asm_stats for summarization."

    # ---- 3) Correlation ----
    if rows:
        corr_res = compute_correlation(
            rows=rows,
            columns=columns,
            x="N50",
            y="TOTAL_LENGTH",
            method="pearson",
        )
        if corr_res.get("status") == "success":
            correlation = corr_res.get("data")
        else:
            correlation_error = corr_res.get("error_message")
    else:
        correlation_error = "No rows returned from asm_stats to compute correlation."

    # ---- 4) Plots ----
    if rows:
        # 4a) N50 histogram
        hist_res = make_plot(
            rows=rows,
            columns=columns,
            kind="hist",
            x="N50",
            title="N50 distribution",
            log_x=True,
            bins=50,
        )
        if hist_res.get("status") == "success":
            n50_hist = hist_res.get("data")
        else:
            n50_hist_error = hist_res.get("error_message")

        # 4b) Scatter plot N50 vs TOTAL_LENGTH
        scatter_res = make_plot(
            rows=rows,
            columns=columns,
            kind="scatter",
            x="N50",
            y="TOTAL_LENGTH",
            title="N50 vs total assembly length",
            log_x=True,
            log_y=True,
        )
        if scatter_res.get("status") == "success":
            n50_vs_total_scatter = scatter_res.get("data")
        else:
            n50_vs_total_scatter_error = scatter_res.get("error_message")
    else:
        n50_hist_error = "No rows returned from asm_stats to generate plots."
        n50_vs_total_scatter_error = n50_hist_error

    # ---- 5) Build analysis_record and save to local history ----
    analysis_record_dict = None
    history_save_status: str | None = None
    history_save_error: str | None = None

    if row_count > 0:
        # Safely extract stats for the summary
        n50_stats = (summaries or {}).get("N50", {}) if isinstance(summaries, dict) else {}
        total_stats = (summaries or {}).get("TOTAL_LENGTH", {}) if isinstance(summaries, dict) else {}

        n_genomes = n50_stats.get("count", row_count)
        median_n50 = n50_stats.get("median")
        median_total_length = total_stats.get("median")

        corr_val = None
        if isinstance(correlation, dict):
            corr_val = correlation.get("correlation")

        # Human-readable one-liner summary
        pieces = [f"Assembly quality overview for {n_genomes} genomes."]
        if median_n50 is not None:
            pieces.append(f"Median N50 ≈ {median_n50}.")
        if median_total_length is not None:
            pieces.append(f"Median total assembly length ≈ {median_total_length}.")
        if corr_val is not None:
            pieces.append(f"Pearson correlation between N50 and total length ≈ {corr_val}.")
        summary_text = " ".join(pieces)

        # Figure paths: pull from the plot tool outputs (which are dicts from make_plot)
        figure_paths: list[str] = []
        if isinstance(n50_hist, dict):
            path = n50_hist.get("image_path")
            if path:
                figure_paths.append(path)
        if isinstance(n50_vs_total_scatter, dict):
            path = n50_vs_total_scatter.get("image_path")
            if path:
                figure_paths.append(path)

        result_stats = {
            "n_genomes": n_genomes,
            "row_count": row_count,
            "median_n50": median_n50,
            "median_total_length": median_total_length,
            "correlation_n50_vs_total_length": corr_val,
        }

        record = AnalysisRecord.create(
            workflow_name="assembly_quality_overview",
            params={"limit": limit},
            summary_text=summary_text,
            result_stats=result_stats,
            figure_paths=figure_paths,
            tags=["asm_stats", "assembly_quality", "N50", "TOTAL_LENGTH"],
        )
        analysis_record_dict = record.to_dict()

        # Save to local analysis_history.duckdb
        save_res = save_analysis_record(analysis_record_dict)
        history_save_status = save_res.get("status")
        history_save_error = save_res.get("error_message")

    # ---- 6) Collect everything into a single result ----
    result_data: Dict[str, Any] = {
        "limit": limit,
        "row_count": row_count,
        "summaries": summaries,
        "summaries_error": summaries_error,
        "correlation": correlation,
        "correlation_error": correlation_error,
        "plots": {
            "n50_hist": n50_hist,
            "n50_hist_error": n50_hist_error,
            "n50_vs_total_scatter": n50_vs_total_scatter,
            "n50_vs_total_scatter_error": n50_vs_total_scatter_error,
        },
        "analysis_record": analysis_record_dict,
        "history_save_status": history_save_status,
        "history_save_error": history_save_error,
    }

    return _success(result_data)



def genome_lifestyle_overview(
    min_species_per_guild: int = 5,
    max_genomes_per_guild: int = 200,
) -> Dict[str, Any]:
    """
    Summarize how genome size (TOTAL_LENGTH) and assembly contiguity (N50)
    vary across ecological guilds/lifestyles.

    Expected schema (adjust SQL if your column names differ):
      - asm_stats:
          SPECIES, TOTAL_LENGTH, N50, ...
      - funguild:
          SPECIES, guild, ...

    Steps:
      1. Join asm_stats with funguild by SPECIES.
      2. Filter to guilds with at least min_species_per_guild distinct species.
      3. Limit to at most max_genomes_per_guild genomes per guild.
      4. Compute per-guild summary stats for TOTAL_LENGTH and N50.
      5. Create boxplots:
         - TOTAL_LENGTH by guild
         - N50 by guild
      6. Return stats + plot paths in an ADK-style envelope.
    """
    # --- 1) Join asm_stats + funguild ---
    # Note: we SELECT f.guild AS guild to ensure the column name is 'guild' in the result.
    sql = f"""
    WITH joined AS (
      SELECT
        a.SPECIES,
        f.guild AS guild,
        a.TOTAL_LENGTH,
        a.N50
      FROM asm_stats a
      JOIN funguild f
        ON a.SPECIES = f.SPECIES
      WHERE a.TOTAL_LENGTH IS NOT NULL
        AND a.N50 IS NOT NULL
        AND f.guild IS NOT NULL
    ),
    annotated AS (
      SELECT
        *,
        COUNT(DISTINCT SPECIES) OVER (PARTITION BY guild) AS species_per_guild,
        ROW_NUMBER() OVER (PARTITION BY guild ORDER BY TOTAL_LENGTH DESC) AS rn
      FROM joined
    )
    SELECT *
    FROM annotated
    WHERE species_per_guild >= {min_species_per_guild}
      AND rn <= {max_genomes_per_guild}
    """

    query_result = run_duckdb_query(sql, max_rows=100000)
    if query_result["status"] == "error":
        return _error(f"SQL query failed in genome_lifestyle_overview: {query_result['error_message']}")

    data = query_result["data"]
    rows = data["rows"]
    if not rows:
        return _error("No rows returned after filtering by guild and species thresholds.")

    df = pd.DataFrame(rows)

    required_cols = {"guild", "TOTAL_LENGTH", "N50", "SPECIES"}
    missing = required_cols - set(df.columns)
    if missing:
        return _error(
            f"Expected columns {required_cols} in joined result, but missing {missing}. "
            f"Adjust the SQL or column names in genome_lifestyle_overview."
        )

    # --- 2) Compute per-guild summary stats ---
    stats_by_guild: Dict[str, Any] = {}

    for guild, gdf in df.groupby("guild"):
        n_genomes = int(len(gdf))
        n_species = int(gdf["SPECIES"].nunique())

        # Convert to numeric safely
        tl = pd.to_numeric(gdf["TOTAL_LENGTH"], errors="coerce").dropna()
        n50 = pd.to_numeric(gdf["N50"], errors="coerce").dropna()

        if tl.empty or n50.empty:
            # Skip guilds with no valid numeric data
            continue

        stats_by_guild[guild] = {
            "n_genomes": n_genomes,
            "n_species": n_species,
            "total_length": {
                "mean": float(tl.mean()),
                "median": float(tl.median()),
                "min": float(tl.min()),
                "max": float(tl.max()),
            },
            "n50": {
                "mean": float(n50.mean()),
                "median": float(n50.median()),
                "min": float(n50.min()),
                "max": float(n50.max()),
            },
        }

    if not stats_by_guild:
        return _error("No guilds had valid numeric TOTAL_LENGTH and N50 values.")

    # --- 3) Prepare data for plotting ---
    plot_df = df.copy()
    plot_df["TOTAL_LENGTH"] = pd.to_numeric(plot_df["TOTAL_LENGTH"], errors="coerce")
    plot_df["N50"] = pd.to_numeric(plot_df["N50"], errors="coerce")
    plot_df = plot_df.dropna(subset=["TOTAL_LENGTH", "N50", "guild"])

    plot_rows = plot_df.to_dict(orient="records")
    plot_cols = list(plot_df.columns)

    # --- 4) Create boxplots using existing make_plot tool ---

    # TOTAL_LENGTH by guild (log_y often helpful for genome sizes)
    tl_plot = make_plot(
        rows=plot_rows,
        columns=plot_cols,
        kind="box",
        x="guild",
        y="TOTAL_LENGTH",
        title="Genome size (TOTAL_LENGTH) by guild",
        log_y=True,
    )

    if tl_plot["status"] == "error":
        tl_path = None
    else:
        tl_path = tl_plot["data"]["image_path"]

    # N50 by guild (log_y helpful if range is wide)
    n50_plot = make_plot(
        rows=plot_rows,
        columns=plot_cols,
        kind="box",
        x="guild",
        y="N50",
        title="Assembly contiguity (N50) by guild",
        log_y=True,
    )

    if n50_plot["status"] == "error":
        n50_path = None
    else:
        n50_path = n50_plot["data"]["image_path"]

    # --- 5) Return combined result ---
    return _success(
        {
            "params": {
                "min_species_per_guild": min_species_per_guild,
                "max_genomes_per_guild": max_genomes_per_guild,
            },
            "n_rows": int(len(plot_df)),
            "n_guilds": int(len(stats_by_guild)),
            "guild_stats": stats_by_guild,
            "plots": {
                "total_length_boxplot": tl_path,
                "n50_boxplot": n50_path,
            },
        }
    )

