
For each of the plu/boc variables (allowed development types and intensities), we have a set of BASIS data and a set of data used for PBA40.

In order to determine if the BASIS data set is usable for a given variable for a given jurisdiction, we try to estimate the effect of using the BASIS data
for that variable on UrbanSim development capacity.

This is done by calculating capacity effects for each variable (via [script 2](../2_calculate_juris_basis_pba40_capacity_metrics.py),
and then creating a heuristic-based hybrid index (via [script 3](../3_create_heuristic_hybrid_idx.py), which indicates using BASIS data for a
given variable and a given jurisdiction if (and only if) the capacity is not affected too much (determined by a threshold for percentage change).

Thus, the files in this directory are:

* [idx_urbansim_heuristic.csv](idx_urbansim_heuristic.csv): created by [script 3](../3_create_heuristic_hybrid_idx.py), heuristic-driven hybrid index configuration for which BASIS variables to use for each jurisdiction
* [idx_urbansim_heuristic.log](idx_urbansim_heuristic.csv): debug log created by [script 3](../3_create_heuristic_hybrid_idx.py)
* idx_urbansim.csv: the same as idx_urbansim_heuristic.csv but with manual edits
