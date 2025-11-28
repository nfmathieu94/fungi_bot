from google.adk.agents import Agent
from .tools.sql_tools import run_duckdb_query, list_tables, describe_table
from .tools.plot_tools import make_plot
from .tools.stats_tools import summarize_numeric_columns, compute_correlation

root_agent = Agent(
    name="fungi_bot",
    model="gemini-2.5-flash",
    instruction="""
    - summarize_numeric_columns(rows, columns, column_names=None)
      - Use after run_duckdb_query.
      - Pass rows = query_result["data"]["rows"], columns = query_result["data"]["columns"].
      - Optionally specify column_names to focus on particular numeric columns.
      - On success, data: { "summaries": { <col>: {count, mean, std, min, max, median, n_missing}, ... } }
    - compute_correlation(rows, columns, x, y, method="pearson")
      - Use after run_duckdb_query when the user asks about relationships between two numeric variables.
      - Pass rows = query_result["data"]["rows"], columns = query_result["data"]["columns"], and x, y column names.
      - On success, data: { "x", "y", "method", "correlation", "n_points" }
    - For numeric summaries (e.g. "what is the distribution of N50?"), use summarize_numeric_columns after fetching data.
    - For relationships (e.g. "is N50 correlated with GC content?"), use compute_correlation after fetching the relevant columns.
    - Always check the status field before using data from any tool.""",
    tools=[
        run_duckdb_query,
        list_tables,
        describe_table,
        make_plot,
        summarize_numeric_columns,
        compute_correlation,
    ],
)
