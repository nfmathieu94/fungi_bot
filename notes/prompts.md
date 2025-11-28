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

`[user]: Use run_duckdb_query to select N50 and GC_PERCENT from asm_stats and then use make_plot 
to create a scatter plot ('scatter') with x = N50 and y = GC_PERCENT. Tell me the 
image_path and briefly describe what the plot shows.`

`[fungi_bot]: The scatter plot showing N50 versus GC_PERCENT has been saved to 
`/bigdata/stajichlab/nmath020/adk_projects/fungi_bot/figures/scatter_N50_vs_GC_PERCENT_20251128_092655.png`. 
The plot displays the distribution of GC_PERCENT across a wide range of N50 values, 
with the N50 axis on a logarithmic scale. It appears there is a cluster of points with N50 values 
ranging from approximately 10^4 to 10^7, and GC_PERCENT values mostly between 40% and 60%, with some outliers.`
