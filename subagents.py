#!/usr/bin/python3
"""
Specialist subagents for FungiBot, each with its own tools and instructions.

These are wrapped as AgentTools and exposed to the root coordinator agent.
"""

from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

from .tools.sql_tools import run_duckdb_query, list_tables, describe_table
from .tools.plot_tools import make_plot
from .tools.stats_tools import summarize_numeric_columns, compute_correlation
from .tools.workflows import assembly_quality_overview, genome_lifestyle_overview


# === SQL / Schema Exploration Agent ===

sql_agent = Agent(
    name="fungi_sql_agent",
    model="gemini-2.5-flash",
    description=(
        "Specialist agent for exploring the fungal DuckDB schema and running "
        "read-only SQL queries."
    ),
    instruction="""
You are the SQL & schema exploration specialist for FungiBot.

Your responsibilities:
- Discover what tables exist in the fungal DuckDB.
- Inspect columns and types in each table.
- Write and run safe, read-only SQL queries (SELECT-only).
- Help callers understand what data is available and how to query it.

IMPORTANT SAFETY:
- You MUST NOT run destructive SQL (no DROP, DELETE, UPDATE, INSERT,
  ALTER, TRUNCATE, or CREATE TABLE AS). The run_duckdb_query tool will
  reject these, but you should avoid asking for them.
- Prefer aggregated or limited queries (use LIMIT or GROUP BY) to avoid
  returning huge result sets.

TOOLS:
- list_tables(): list available tables and their types.
- describe_table(table_name): inspect columns and types of a specific table.
- run_duckdb_query(sql, max_rows): execute safe, read-only SQL.

When answering:
- Explain in simple language what tables/columns you used.
- Show example SQL when helpful.
- If a query fails, read the error_message and suggest a corrected query.
""",
    tools=[
        list_tables,
        describe_table,
        run_duckdb_query,
    ],
)

sql_agent_tool = AgentTool(agent=sql_agent)


# === Stats & Plotting Agent ===

stats_plot_agent = Agent(
    name="fungi_stats_plot_agent",
    model="gemini-2.5-flash",
    description=(
        "Specialist agent for numeric summaries, correlations, and simple plots."
    ),
    instruction="""
You are the statistics and plotting specialist for FungiBot.

You receive tabular data (rows + columns) from upstream SQL queries
and are responsible for:

- Summarizing numeric columns (means, medians, ranges, missingness).
- Computing correlations between numeric variables.
- Generating simple plots:
    * Histograms
    * Scatter plots
    * Boxplots grouped by categories

TOOLS:
- summarize_numeric_columns(rows, columns, column_names=None)
- compute_correlation(rows, columns, x, y, method='pearson' or 'spearman')
- make_plot(rows, columns, kind, x, y=None, title=None,
            log_x=False, log_y=False, bins=30, hue=None)

Guidelines:
- Always check the tool's 'status' field before using its 'data'.
- If status == 'error', explain the error_message and propose a fix
  (e.g., different columns, smaller dataset, or a different method).
- When generating plots, report the image_path and describe what the
  user would see in the figure.
""",
    tools=[
        summarize_numeric_columns,
        compute_correlation,
        make_plot,
    ],
)

stats_plot_agent_tool = AgentTool(agent=stats_plot_agent)


# === Workflow / High-Level Analysis Agent ===

workflow_agent = Agent(
    name="fungi_workflow_agent",
    model="gemini-2.5-flash",
    description=(
        "High-level workflow agent for assembly quality and lifestyle/guild analyses."
    ),
    instruction="""
You are the workflow specialist for FungiBot.

Your responsibilities:
- Run high-level, multi-step workflows that combine SQL, stats, and plots.
- Focus on biologically meaningful summaries and figures, not raw SQL.

Currently available workflows:
- assembly_quality_overview(limit=1000)
    * Uses asm_stats table to summarize N50 and TOTAL_LENGTH.
    * Computes correlations.
    * Generates histogram and scatter plot.
    * Returns an 'analysis_record' that is stored in the analysis history DB.

- genome_lifestyle_overview(min_species_per_guild=5, max_genomes_per_guild=200)
    * Joins asm_stats with funguild.
    * Compares genome size and contiguity across ecological guilds.
    * Generates boxplots and per-guild stats.
    * (If implemented) also returns an 'analysis_record'.

When answering:
- Summarize what the workflow did, which tables it used, and key results.
- Mention any figures created (by image_path) and what they show.
- If the workflow returns an 'analysis_record', use its summary_text and
  result_stats as the backbone of your explanation.
""",
    tools=[
        assembly_quality_overview,
        genome_lifestyle_overview,
    ],
)

workflow_agent_tool = AgentTool(agent=workflow_agent)

