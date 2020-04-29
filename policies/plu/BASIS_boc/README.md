### Purposes 
* QA/QC BASIS BOC data (base zoning data collected through BASIS) by comparing it with PBA40 PLU data (base zoning data used in PBA40)
* build and examine various versions of hybrid PBA40-BOC base zoning data by comparing their implied development capacity (in residential units and non-residential sqft)

### Steps
#### 1_PLU_BOC_data_combine.ipynb
Merge and clean several data sets.

Input (please see data sources below):
* p10 parcels
* pba40 zoning lookup, pba40 zoning-parcel mapping
* basis boc (mapped to p10 'PARCEL_ID')
* pba50 zoningmod (contains 'nodev' parcels, i.e. nondevelopable parcels)

Output:
* ['p10_plu_boc_allAttrs.csv'](https://mtcdrive.app.box.com/file/659036313452) which contains 4 groups of p10 attributes: 
	* basic attributes, e.g. PARCEL_ID, ACRES, COUNTY, JURIS, NO_DEV
	* allowed development type, i.e. '1/0' binary value of 14 development types, for both PBA40 and BASIS
	* development intensity, i.e. max_dua, max_far, max_height, for both PBA40 and BASIS

#### 2_dev_type_hybrid_modification.ipynb

Input:
* raw PBA40 and BASIS zoning data: 'p10_plu_boc_allAttrs.csv' from the previous step
* hybrid index files: used to build hybrid base zoning by selecting more 'reasonable' allowed development type and intensity data from PBA40 versus BASIS. [Three versions](https://mtcdrive.box.com/s/j1rws9z619k8mx45eute7lcxt84flhvq):
	* [hybrid 1] 'idx_BASIS_intensity_all.csv': keep all BASIS intensity data, replace all BASIS allowed development type data with PBA40 allowed development types
	* [hybrid_2] 'idx_BASIS_intensity_partial.csv' (in progress): replace BASIS intensity data for some jurisdictions with PBA40 data, replace all BASIS allowed development type data with PBA40 allowed development types
	* [hybrid_3] 'idx_BASIS_devType_intensity_partial.csv' (in progress): replace BASIS intensity data for some jurisdictions with PBA40 data, replace BASIS allowed development type data for some jurisdictions with PBA40 allowed development types

Output:
* [hybrid 0] ['p10_plu_boc_fill_naType.csv'](https://mtcdrive.app.box.com/file/659049771128): filled in BASIS missing allowed development type data with PBA40 data
* [hybrid 1] ['p10_plu_boc_pba40Type.csv'](https://mtcdrive.app.box.com/file/659051027629): replace BASIS all allowed development type data with PBA40 data
* [hybrid_2] (in progress)
* [hybrid_3] (in progress)
* ['devType_comparison.csv'](https://mtcdrive.app.box.com/file/659047511568): compares BASIS vs. PBA40 allowed development type data at parcel level. Each parcel falls into one of the following types for each [development type]:
    * 'both allow': the type of development is allowed in both PBA40 PLU data and BASIS BOC data
    * 'only pba40 allow'
    * 'only basis allow'
    * 'both not allow'
    * 'missing BASIS BOC' (but developable according to pba50_zoningmod)
    * 'not developable' (parcels cannot be developed)
    * 'other' (missing PBA40 data)

#### 3_dev_capacity_calculation.ipynb
Calculate effective development intensity (refer to the [effective_max_dua](https://github.com/UDST/bayarea_urbansim/blob/0fb7776596075fa7d2cba2b9fbc92333354ba6fa/baus/variables.py#L808) and [effective_max_far](https://github.com/UDST/bayarea_urbansim/blob/0fb7776596075fa7d2cba2b9fbc92333354ba6fa/baus/variables.py#L852) calculations) for PBA40 and BASIS and compare the results. Uses different hybrid versions of BASIS BOC data as generated from the previous step.

Input:
* various versions of "p10_plu_boc" hybrid data generated from the previous step

Output:
* [hybrid 0] 
	* ['devCapacity_allAttrs_fill_naType.csv'](https://mtcdrive.app.box.com/file/659049771128): development capacity with PBA40 and hybrid_0 BASIS zoning data at parcel level - residential units, non-residential thousand sqft, number of employees
* [hybrid 1]
	* ['devCapacity_allAttrs_pba40Type.csv'](https://mtcdrive.app.box.com/file/659053674261): development capacity with PBA40 and hybrid_1 BASIS zoning data at parcel level - residential units, non-residential thousand sqft, number of employees
	* ['devIntensity_pba40Type.csv'](https://mtcdrive.app.box.com/file/659057164065): raw intensity (max_dua, max_far, max_height) and calculated effective intensity from both PBA40 and BASIS 
* [hybrid_2] (in progress)
* [hybrid_3] (in progress)

## Data sources  
* 'p10_table', 'blg10.csv' retrieved from [smelt.gdb](https://mtcdrive.app.box.com/folder/106699591369): p10 parcel and building
* ['2015_03_06_zoning_parcels.csv'](https://mtcdrive.app.box.com/folder/103451630229): parcel10 to pba40 basezoning code
* ['zoning_lookup.csv'](github.com/BayAreaMetro/bayarea_urbansim/blob/master/data/zoning_lookup.csv): pba40 basezoning plu
* ['p10_boc_opt_b_v1d_tbl'](https://mtcdrive.app.box.com/file/647477715461): BASIS BOC
* ['2020_04_14_parcels_geography.csv'](https://mtcdrive.app.box.com/folder/103451630229): planned zoningmod scenarios
