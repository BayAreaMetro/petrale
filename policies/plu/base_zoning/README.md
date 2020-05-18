## Purpose
* QA/QC BASIS BOC data (zoning data collected through BASIS) by comparing it with PBA40 PLU data (zoning data used in PBA40)
* build and examine various versions of hybrid BASIS/PBA40 zoning by comparing their implied development capacity (in residential units and non-residential sqft)

## Steps

### [1_PLU_BOC_data_combine.py](1_PLU_BOC_data_combine.py)
Merge and clean several data sets.

Input:
* [UrbanSim parcels](https://mtcdrive.box.com/s/hnwpcw97tqqga1ngvcs5oct5av2j1ine)
* [PBA40 parcel to zoning id](https://mtcdrive.box.com/s/ir65mdbytf2lpjx8i41j7lpxqm4r1ujm) and [zoning id to zoning definition ("zoning_lookup")](https://github.com/BayAreaMetro/bayarea_urbansim/blob/master/data/zoning_lookup.csv)
* [parcel to BASIS zoning definition](https://mtcdrive.box.com/s/eqqlfmwvgac87f703kwrt0imrsqcp9iv)
* [zoning mod](https://mtcdrive.box.com/s/zkxaf4gxn47oe716r4wqrp1raqfq8lhy) (contains 'nodev' parcels, i.e. nondevelopable parcels)

Output:
* [p10_plu_boc_allAttrs.csv](https://mtcdrive.box.com/s/d99i7rhcm14jtv3l403vjjskrnieckqb): parcels joined with PBA40 and BASIS zoning information (allowed development types and intensities) and nodev flag. Contains 4 groups of p10 attributes: 
   * basic attributes, e.g. PARCEL_ID, ACRES, COUNTY, JURIS, NO_DEV
   * allowed development type, i.e. '1/0' binary value of 14 development types, for both PBA40 and BASIS, along with aggregated 'allow residential' and 'allow non-residential' for each parcel
   * development intensity, i.e. max_dua, max_far, max_height, for both PBA40 and BASIS
* ['devType_comparison.csv'](https://mtcdrive.box.com/s/vbbhb3vs230krbmyhr2ma4d03qaqec7o): compares BASIS vs. PBA40 allowed development type data at parcel level. Each parcel falls into one of the following types for each [development type]:
    * 'both allow': the type of development is allowed in both PBA40 PLU data and BASIS BOC data
    * 'only pba40 allow'
    * 'only basis allow'
    * 'both not allow'
    * 'missing BASIS' (but has PBA40 data and deemed developable by pba50_zoningmod)
    * 'missing PBA40' (missing PBA40 data)
    * 'not developable' (parcels cannot be developed)

### 1b [import_filegdb_layers.py](../../../basemap/import_filegdb_layers.py)

This script is helpful for merging the output of the previous script, *p10_plu_boc_allAttrs.csv*, with the p10 parcel geographies into a geodatabase.
This one takes a while to run.  I copied the version I created here: ``M:\Data\GIS layers\UrbanSim_BASIS_zoning\UrbanSim_BASIS_zoning.gdb``

### 1c [create_jurisdiction_map.py](create_jurisdiction_map.py)

This takes the previous gdb along with an accompanying ArcGIS project file (``M:\Data\GIS layers\UrbanSim_BASIS_zoning\UrbanSim_BASIS_zoning.aprx``)
and creates pdf maps of BASIS vs PBA40 data by jurisdiction.  See [Jurisdiction Maps BASISvsPBA40 box folder](https://mtcdrive.box.com/s/e2qck5p03sd53q0rxg91x1wphw6zg766).

### [2_build_hybrid_zoning.py](2_build_hybrid_zoning.py)

Input:
* *p10_plu_boc_allAttrs.csv*: parcels joined with PBA40 and BASIS zoning information (allowed development types as well as intensities) and nodev flag from the previous step
* Hybrid index files: used to build hybrid base zoning by selecting more reasonable allowed development type and intensity data from PBA40 versus BASIS. Multiple versions to help construct the hybrid index used for UrbanSim:
   * *[hybrid_0]* (no index file) Use zoning data from BASIS except for where allowed development types information is missing -- then use PBA40
   * *[hybrid 1]* [idx_BASIS_intensity_all.csv](hybrid_index/idx_BASIS_intensity_all.csv): all zoning intensity from BASIS, all allowed development types from PBA40
   * *[hybrid_2]* [idx_BASIS_intensity_partial.csv](hybrid_index/idx_BASIS_intensity_partial.csv): use allowed development types from PBA40; use intensity information from BASIS for jurisdictions where that information looks reasonable based on capacity comparison analysis [posted here for residential](Residential_UNIT_hybrid_devTypes_only.twb) (max_dua hybrid) and [posted here for non-residential](Nonresidential_SQFT_hybrid_devTypes_only.twb) (max_far hybrid). If the configuration uses PBA40 data for both *max_dua* and *max_far*, then *max_height* will come from PBA40 configuration as well.
   * *[hybrid_3]* [idx_BASIS_devType_intensity_partial.csv](hybrid_index/idx_BASIS_devType_intensity_partial.csv): same as *[hybrid_2]* configuration but includes a mix of PBA40/BASIS sources for allowed development types as well.  Uses BASIS allowed development types for *HM, MR, RS, OF* for certain jurisdictions based on the BASIS data quality for each of the four types as illustrated [here](https://public.tableau.com/profile/yuqi6946#!/vizhome/devType_comparison_20200428/HM_comp?publish=yes); for the other development types, use PBA40 for all jurisdictions.
   * *[hybrid_4]*[idx_hybrid_devTypes.csv](hybrid_index/idx_hybrid_devTypes.csv): hybrid development types with all BASIS intensity attributes. The development type hybrid is based on [PBA40-BASIS development type comparison](devType_comparison.twb) generated by *1_PLU_BOC_data_combine.py*. Run this hybrid index to generate PBA40-Hybrid development capacity comparison for both [residential units](Residential_UNIT_hybrid_devTypes_only.twb) and [non-residential sqft](Nonresidential_SQFT_hybrid_devTypes_only.twb), which will be used to construct hybrid intensity attributes. 
   * **[hybrid_urbansim]**[idx_urbansim.csv](hybrid_index/idx_urbansim.csv): hybrid development types and intensities. 

Output:
* [hybrid 0] ['p10_plu_boc_fill_naType.csv'](https://mtcdrive.box.com/s/ewr0teoikz2irggb362fnfynfgh48zjn): filled in BASIS missing allowed development type data with PBA40 data
* [hybrid 1] ['p10_plu_boc_BASIS_intensity_all.csv'](https://mtcdrive.box.com/s/9x0hv9jtai6axf7q0jfn83qboxbrqvpv): replace BASIS all allowed development type data with PBA40 data
* [hybrid_2] ['p10_plu_boc_BASIS_intensity_partial.csv'](https://mtcdrive.box.com/s/e3kfygjta1rvqxixx0oarqi0qjiot1xg)
* [hybrid_3] ['p10_plu_boc_BASIS_devType_intensity_partial.csv'](https://mtcdrive.box.com/s/3rq0qersejrh5pnvijfd80e6b78dbf45)
* [hybrid_4] ['p10_plu_boc_hybrid_devTypes.csv'](https://mtcdrive.box.com/s/0fun7glfot0byf3zq0v7zfdbyzwub1jz)
* [hybrid_urbansim] ['p10_plu_boc_urbansim.csv'](https://mtcdrive.box.com/s/cfelcxie2ks01pqwq4ed6sbfbjhduh3w): p10 parcel (1,956,208 records) with all urbansim base zoining attributes which are PBA40-BASIS hybrid.
* **[zoning_parcels_pba50.csv]**(https://mtcdrive.box.com/s/rrsud2mkwr05nhrbl3iutphjqmapjqie): p10 parcel to urbansim base zoning ID mapping file. BAUS input.
* **[zoning_lookup_pba50.csv]**(https://mtcdrive.box.com/s/b97q1tyef5hbl02p67hm4ynx2t5n0i7g): urbansim base zoning ID to zoning attributes mapping. BAUS input.

### [3_dev_capacity_calculation.py](3_dev_capacity_calculation.py)
Calculate effective development intensity (refer to the [effective_max_dua](https://github.com/UDST/bayarea_urbansim/blob/0fb7776596075fa7d2cba2b9fbc92333354ba6fa/baus/variables.py#L808) and [effective_max_far](https://github.com/UDST/bayarea_urbansim/blob/0fb7776596075fa7d2cba2b9fbc92333354ba6fa/baus/variahttps://mtcdrive.box.com/s/vbbhb3vs230krbmyhr2ma4d03qaqec7obles.py#L852) calculations) for PBA40 and BASIS and compare the results. Uses different hybrid versions of BASIS BOC data as generated from the previous step.

Input:
* various versions of "p10_plu_boc" hybrid data generated from the previous step

Output:
* [hybrid 0] 
	* ['devCapacity_allAttrs_fill_naType.csv'](https://mtcdrive.box.com/s/huty80u1m7lxlh20j1d2s8w1n9ny75bz): development capacity with PBA40 and hybrid_0 BASIS zoning data at parcel level - residential units, non-residential thousand sqft, number of employees
* [hybrid 1]
	* ['devCapacity_allAttrs_pba40Type.csv'](https://mtcdrive.box.com/s/09tbye86qs5kydhckoii53eitlac3my3): development capacity with PBA40 and hybrid_1 BASIS zoning data at parcel level - residential units, non-residential thousand sqft, number of employees
* [hybrid_2]
	* ['devCapacity_allAttrs_BASIS_intensity_partial.csv'](https://mtcdrive.box.com/s/ce4tjx89egxuq263t08wdaegjbvvtv0d)
* [hybrid_3] 
	* ['devCapacity_allAttrs_BASIS_devType_intensity_partial.csv'](https://mtcdrive.box.com/s/qtysq31wvzudl9b9vjjz7etgm9i4z9se)
* [hybrid_4]
	* ['devCapacity_allAttrs_hybrid_devTypes.csv'](https://mtcdrive.box.com/s/ad5377dngbrsn30va6in654v2fx5id1b): this is the input of the jurisdiction-level development capacity in [residential units](Residential_UNIT_hybrid_devTypes_only.twb) and [non-residential sqft](Nonresidential_SQFT_hybrid_devTypes_only.twb).

### [4_net_dev_capacity_calculation.ipynb](https://github.com/BayAreaMetro/petrale/blob/master/policies/plu/base_zoning/4_net_dev_capacity_calculation.ipynb)

Identify parcel characteristics in order to calculate net development capacity based on the following criteria:
    * Vacant land
    * Under-built parcels, defined as parcels whose additional residential units (zoned units minus existing residential units and equivalent units of non-residential sqft) are at least 50% more than existing residential units
    * Parcels with high zoned capacity / existing capacity ratio
    * Parcels without buildings before the year 1940
    * Parcels smaller than or equal to a half acre cannot have single family homes (?)

Input:
* [UrbanSim parcels](https://mtcdrive.box.com/s/sgy1uorcgt7uhh29fja7v93c21ppiudq)
* [PBA40 UrbanSim buildings](https://mtcdrive.box.com/s/sgy1uorcgt7uhh29fja7v93c21ppiudq)
* Raw development capacity calculated from [3_dev_capacity_calculation.ipynb](3_dev_capacity_calculation.ipynb) under the preferred hybrid version. Current script uses [hybrid_3 raw capacity](https://mtcdrive.box.com/s/qtysq31wvzudl9b9vjjz7etgm9i4z9se).

Output:
* ['capacity_gross_net.csv'](https://mtcdrive.box.com/s/axhulwng5olq2jign52s0dwznmii59n7): development capacity in residential units, non-residential sqft and employment at parcel-level with parcels labelled in 'is_vacant', 'is_under_built', 'res_zoned_existing_ratio', 'nonres_zoned_existing_ratio', 'has_old_building', 'ILR' (investment-land value ratio).


### Tableau files
* ['devType_comparison.twb'](devType_comparison.twb) - data discrepancies in development types between PBA40 and BASIS
* ['Residential_UNIT_hybrid_devTypes_only.twb'](Residential_UNIT_hybrid_devTypes_only.twb) - compare PBA40 and hybrid 4 development capacity in residential units by jurisdiction
* ['Nonresidential_SQFT_hybrid_devTypes_only.twb'](Nonresidential_SQFT_hybrid_devTypes_only.twb) - compare BASIS and PBA40 development capacity in non-res sqft by jurisdiction
* Deprecated: 
	* ['Residential_UNIT_hybrid_0.twb'](Residential_UNIT_hybrid_0.twb) - compare BASIS and PBA40 development capacity in residential units by jurisdiction using [this data](https://mtcdrive.box.com/s/huty80u1m7lxlh20j1d2s8w1n9ny75bz) 
	* ['Non-residential_SQFT_hybrid_0.twb'](Nonresidential_SQFT_hybrid_0.twb) - compare BASIS and PBA40 development capacity in non-res sqft by jurisdiction using [this data](https://mtcdrive.box.com/s/huty80u1m7lxlh20j1d2s8w1n9ny75bz)
	* ['Residential_UNIT_hybrid_1.twb'](Residential_UNIT_hybrid_1.twb) - compare BASIS and PBA40 development capacity in residential units by jurisdiction using [this data](https://mtcdrive.box.com/s/09tbye86qs5kydhckoii53eitlac3my3) 
	* ['Non-residential_SQFT_hybrid_1.twb'](Nonresidential_SQFT_hybrid_1.twb) - compare BASIS and PBA40 development capacity in non-res sqft by jurisdiction using [this data](https://mtcdrive.box.com/s/09tbye86qs5kydhckoii53eitlac3my3)
