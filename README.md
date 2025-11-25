# FungiBot - Agentic SQL Analysis System for Fungal Genomes

FungiBot is an agent built using Google ADK that enables natural language
queries over a DuckDB database containing ~3000 fungal genomes.

## Project Goals
- Query a large fungal-genomics SQL database using natural language.
- Run analyses (stats, summaries, filtering).
- Generate visualizations (Python & R/ggplot2).
- Automate multi-step workflows using agentic tools.

## Technologies
- Google ADK (Agent Development Kit)
- DuckDB (local SQL analytics)
- Python 3.10+
- HPC compute environment

## Structure
- fungi_bot/
- agent.py # Main ADK agent definition
- sql_tools.py # SQL query tools (added later)
- database/ # DuckDB database files (ignored)

## Setup
- conda create -n adk python=3.10
- conda activate adk
- pip install google-adk duckdb pandas

## Running
adk run
