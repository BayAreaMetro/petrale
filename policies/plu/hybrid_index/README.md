
For each of the plu/boc variables (allowed development types and intensities), we have a set of BASIS data and a set of data used for PBA40.

In order to determine if the BASIS data set is usable for a given variable for a given jurisdiction, we try to estimate the effect of using the BASIS data
for that variable on UrbanSim development capacity.

In Draft Blueprint, this is done by calculating capacity effects for each variable (via [script 2](../2_calculate_juris_basis_pba40_capacity_metrics.py),
and then creating a heuristic-based hybrid index (via [script 3](../3_create_heuristic_hybrid_idx.py), which indicates using BASIS data for a
given variable and a given jurisdiction if (and only if) the capacity is not affected too much (determined by a threshold for percentage change).

In Final Blueprint, the BASIS team received feedback from stakeholders and, along with updating BASIS BOC lookup table, made [recommendations](hybrid_idx_update_10192020.csv) on updating the hybrid index used in Draft Blueprint. Based on this, we created a new set of hybrid index (via [hybrid_index_fb_revision](../hybrid_index_fb_revision.ipynb) which updates the hybrid index and tracks if a jurisdiction's following zoning attributes have been updated: max_far, max_dua, residential_devType, nonresidential_devType).

Thus, the files in this directory are:

* [idx_urbansim_heuristic.csv](idx_urbansim_heuristic.csv): created by [script 3](../3_create_heuristic_hybrid_idx.py), heuristic-driven hybrid index configuration for which BASIS variables to use for each jurisdiction
* [idx_urbansim_heuristic.log](idx_urbansim_heuristic.csv): debug log created by [script 3](../3_create_heuristic_hybrid_idx.py)
* [idx_urbansim.csv](idx_urbansim.csv): the same as idx_urbansim_heuristic.csv but with manual edits. This is used to build the hybrid base zoning as Draft Blueprint input.
* [hybrid_idx_update_10192020.csv](hybrid_idx_update_10192020.csv): recommendations from the BASIS team on updating Draft Blueprint hybrid index.
* [idx_urbansim_fb_10192020.csv](idx_urbansim_fb_10192020.csv): created by [hybrid_index_fb_revision](../hybrid_index_fb_revision.ipynb), updating [idx_urbansim.csv](idx_urbansim.csv) based on [recommendations](hybrid_idx_update_10192020.csv). The fields 'updated_max_dua_idx', 'updated_max_far_idx', 'updated_res_blgType_idx', 'updated_nonres_blgType_idx' indicate if the relevant zoning attributes were updated. 'updated_res_blgType_idx' being True indicates one or more updates in 'HS_idx', 'HT_idx', 'HM_idx', or 'MR_idx'; 'updated_nonres_blgType_idx' being True indicates one or more updates in the 'OF_idx', 'HO_idx', 'SC_idx', 'IL_idx', 'IW_idx', 'IH_idx', 'RS_idx', 'RB_idx', 'MR_idx', 'MT_idx', 'ME_idx'.


