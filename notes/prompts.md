# Working Prompts

The following questions were used to check added 
agent tools.

## Testing Query

`[user]: What tables exist in the database? Use list_tables to answer.`

`[fungi_bot]: The database contains the following tables: `aa_frequency`, 
`asm_stats`, `cazy`, `cazy_overview`, `chrom_info`, `codon_frequency`, 
`funguild`, `gene_exons`, `gene_info`, `gene_pairwise_distances`, `gene_proteins`, 
`gene_transcripts`, `gene_trna`, `idp`, `idp_summary`, `merops`, 
`mmseqs_orthogroup_cluster_count`, `mmseqs_orthogroup_clusters`, `pfam`, `pfam_UoT`, 
`prosite`, `signalp`, `species`, `targetp`, and `tmhmm`.`

## Plotting Test

[user]: Use run_duckdb_query to select N50 and GC_PERCENT from asm_stats and then use make_plot 
to create a scatter plot ('scatter') with x = N50 and y = GC_PERCENT. Tell me the 
image_path and briefly describe what the plot shows.


## Stats Test

[user]: Use run_duckdb_query to select N50 and GC_PERCENT from asm_stats (with a LIMIT if needed). Then use compute_correlation with method="pearson" to measure the correlation between N50 and GC_PERCENT. Check status at each step, then report the correlation and interpret its strength and direction.

[user]: Use run_duckdb_query to select N50 and TOTAL_LENGTH from asm_stats with a reasonable LIMIT (e.g. 1000). Then use summarize_numeric_columns on the result to summarize both columns. Check the status fields. Finally, explain the summaries in plain language.

## Workflow Test

### Assembly Comparison

[user]: Give me a high-level overview of assembly quality using asm_stats, including
summary statistics for N50 and TOTAL_LENGTH, a correlation between them,
and at least one plot. Use assembly_quality_overview and explain the results.

### Genome and Lifestyle Comparison

[user]: Use your genome_lifestyle_overview workflow to compare genome size and N50
across ecological guilds. Then summarize which guilds tend to have larger genomes
or more contiguous assemblies, and tell me the boxplot image paths.
