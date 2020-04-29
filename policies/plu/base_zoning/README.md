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
* ['p10_plu_boc_allAttrs.csv'](https://mtcdrive.box.com/s/4eaas345rl3ivg8ulwpa5v4i3cvbx1ay) which contains 4 groups of p10 attributes: 
	* basic attributes, e.g. PARCEL_ID, ACRES, COUNTY, JURIS, NO_DEV
	* allowed development type, i.e. '1/0' binary value of 14 development types, for both PBA40 and BASIS
	* development intensity, i.e. max_dua, max_far, max_height, for both PBA40 and BASIS

#### 2_dev_type_hybrid_modification.ipynb

Input:
* raw PBA40 and BASIS zoning data: 'p10_plu_boc_allAttrs.csv' from the previous step
* hybrid index files: used to build hybrid base zoning by selecting more 'reasonable' allowed development type and intensity data from PBA40 versus BASIS. Four versions:
	* [hybrid_0] (no index file) only fill in missing BASIS allowed development type data with PBA40 data, keep all other BASIS type and intensity data
	* [hybrid 1] ['idx_BASIS_intensity_all.csv'](https://github.com/BayAreaMetro/petrale/blob/master/policies/plu/base_zoning/hybrid_index/idx_BASIS_intensity_all.csv): keep all BASIS intensity data, replace all BASIS allowed development type data with PBA40 allowed development types
	* [hybrid_2] ['idx_BASIS_intensity_partial.csv'](https://github.com/BayAreaMetro/petrale/blob/master/policies/plu/base_zoning/hybrid_index/idx_BASIS_intensity_partial.csv): replace all BASIS allowed development type data with PBA40 allowed development types, replace BASIS intensity data for some jurisdictions with PBA40 data based on capacity comparison analysis at jurisdiction level as illustrated [here for residential](https://public.tableau.com/profile/yuqi6946#!/vizhome/Residential_UNIT_20200428_hybrid_1/Notes) (max_dua hybrid) and [here for non-residential](https://public.tableau.com/profile/yuqi6946#!/vizhome/Nonresidential_SQFT_20200428_hybrid_1/BASISMAX_FARdataquality?publish=yes) (max_far hybrid). If a jurisdiction uses PBA40 data for both max_dua and max_far, its 'max_height' index is also 'PBA40'.
	* [hybrid_3] ['idx_BASIS_devType_intensity_partial.csv'](https://github.com/BayAreaMetro/petrale/blob/master/policies/plu/base_zoning/hybrid_index/idx_BASIS_devType_intensity_partial.csv): replace BASIS intensity data for some jurisdictions with PBA40 data following the same methodology as in 'hybrid_2'. Replace BASIS allowed development type data for some jurisdictions with PBA40 allowed development types following this rule: use BASIS data of *HM, MR, RS, OF* for certain jurisdictions based on the BASIS data quality for each of the four types as illustrated [here](https://public.tableau.com/profile/yuqi6946#!/vizhome/devType_comparison_20200428/HM_comp?publish=yes); for the other development types, use PBA40 for all jurisdictions.

Output:
* [hybrid 0] ['p10_plu_boc_fill_naType.csv'](https://mtcdrive.box.com/s/x35fp65pv2lautamq15b4s0mfj3tr8l7): filled in BASIS missing allowed development type data with PBA40 data
* [hybrid 1] ['p10_plu_boc_BASIS_intensity_all.csv'](https://mtcdrive.box.com/s/xdwi6m00htngm65rvyu1ul8uenyflryc): replace BASIS all allowed development type data with PBA40 data
* [hybrid_2] (in progress)
* [hybrid_3] (in progress)
* ['devType_comparison.csv'](https://mtcdrive.box.com/s/mtjogl2fqf25yx7cxy6azrv587mo4itf): compares BASIS vs. PBA40 allowed development type data at parcel level. Each parcel falls into one of the following types for each [development type]:
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
	* ['devCapacity_allAttrs_fill_naType.csv'](https://mtcdrive.box.com/s/huty80u1m7lxlh20j1d2s8w1n9ny75bz): development capacity with PBA40 and hybrid_0 BASIS zoning data at parcel level - residential units, non-residential thousand sqft, number of employees
* [hybrid 1]
	* ['devCapacity_allAttrs_pba40Type.csv'](https://mtcdrive.box.com/s/09tbye86qs5kydhckoii53eitlac3my3): development capacity with PBA40 and hybrid_1 BASIS zoning data at parcel level - residential units, non-residential thousand sqft, number of employees
	* ['devIntensity_BASIS_intensity_all.csv'](https://mtcdrive.box.com/s/32hunczdkugk44iqw224ejozchutojd1): raw intensity (max_dua, max_far, max_height) and calculated effective intensity from both PBA40 and BASIS 
* [hybrid_2] (in progress)
* [hybrid_3] (in progress)

## Data sources  
* 'p10_table', 'blg10.csv' retrieved from [smelt.gdb](https://mtcdrive.app.box.com/folder/106699591369): p10 parcel and building
* ['2015_03_06_zoning_parcels.csv'](https://mtcdrive.app.box.com/folder/103451630229): parcel10 to pba40 basezoning code
* ['zoning_lookup.csv'](github.com/BayAreaMetro/bayarea_urbansim/blob/master/data/zoning_lookup.csv): pba40 basezoning plu
* ['p10_boc_opt_b_v1d_tbl'](https://mtcdrive.app.box.com/file/647477715461): BASIS BOC
* ['p10_pba50_attr_20200416.csv'](https://mtcdrive.app.box.com/file/654543170007): planned zoningmod scenarios
