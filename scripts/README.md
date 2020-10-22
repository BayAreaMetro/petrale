This folder contains script to process UrbanSim and Travel Model run results.

#### [residential_lump_sum_summary.ipynb](residential_lump_sum_summary.ipynb)
Summarizes results of the **residential lump-sum account (subsidy funding)** strategy: aggreates county acctlogs; summarizes number of subsidized_units, funding spent, funding left, the timeline of development, along with the number of inclusionary_units and total residential_units that wouldn't have been built without the subsidy.

Inputs:
* `[runid]_acctlog_[county] Affordable Housing Bond_2050.csv`

Outputs:
* `acct_log_summary.csv` with the following fields: county, year, subsidized_units, inclusionary_units, deed_restricted_units

#### [office_lump_sum_summary.ipynb](office_lump_sum_summary.ipynb): summarizes results of the **office lump-sum account (subsidy funding)** strategy: aggreates county acctlogs; summarizes total non_residential_sqft created by the strategy, non_residential_sqft created by geography category (eg. `tra_id`), funding spent, funding left, and the timeline of development.

Inputs:
* `[runid]_acctlog_[county] Office Subsidy Bond_2050.csv`

Outputs:
* `office_lump_sum_acct_summary.csv` with the following fields: jurisdiction, year, non_residential_sqft, tra_id, parcel_id

#### [DR_distributions_cross_run_analysis.py](DR_distributions_cross_run_analysis.py): summarizes deed-restricted units 1) by source and year-built (public-land, preserved, inclusionary, subsidized, and at 5-year intervals) at county-level, and 2) by geography (county, jurisdiction, superdistrict, TAZ, HRA designation, displacement-risk designation). 

Inputs: 
* `2020_09_21_parcels_geography.csv`, `juris_county_id.csv`, `2020_08_17_parcel_to_taz1454sub.csv`, `taz_geography.csv`, `superdistricts.csv`: to map p10 PARCEL_ID to various geographic designations
* `[runid]_building_data_2020.csv`: UrbanSim Year 2050 buildings output table

Output:
An Excel file with two sets of tabs:
* tabs named `breakdown_[runid]_version`: breaks down DR units by county, source, and year-built; each UrbanSim run result has a separate tab.
* tabs named `dr_[geography]_all`: total DR units broken down by various types of geography; each tab contains multiple UrbanSim run results.
