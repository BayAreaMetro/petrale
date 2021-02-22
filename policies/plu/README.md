## Scripts to build hybrid base zoning PLU


### Purpose
* QA/QC BASIS BOC data (zoning data collected through BASIS) by comparing it with PBA40 PLU data (zoning data used in PBA40)
* build and examine various versions of hybrid BASIS/PBA40 zoning by comparing their implied development capacity (in residential units and non-residential sqft)

### Steps

#### [1_PLU_BOC_data_combine.py](1_PLU_BOC_data_combine.py)
Merge and clean several data sets.

Input:
* [UrbanSim parcels](https://mtcdrive.box.com/s/hnwpcw97tqqga1ngvcs5oct5av2j1ine)
* [PBA40 parcel to zoning id](https://mtcdrive.box.com/s/ir65mdbytf2lpjx8i41j7lpxqm4r1ujm) and [zoning id to zoning definition ("zoning_lookup")](https://github.com/BayAreaMetro/bayarea_urbansim/blob/master/data/zoning_lookup.csv)
* [parcel to BASIS zoning definition](https://mtcdrive.box.com/s/eqqlfmwvgac87f703kwrt0imrsqcp9iv)
* [zoning mod](https://mtcdrive.box.com/s/zkxaf4gxn47oe716r4wqrp1raqfq8lhy) (contains 'nodev' parcels, i.e. nondevelopable parcels)

Output:
* [p10_plu_boc_allAttrs.csv](https://mtcdrive.box.com/s/1xkp87rvcr7qpolfnpv16j5losj3f48y): parcels joined with PBA40 and BASIS zoning information (allowed development types and intensities) and nodev flag. Contains 4 groups of p10 attributes: 
   * basic attributes, e.g. PARCEL_ID, ACRES, COUNTY, JURIS, NO_DEV
   * allowed development type, i.e. '1/0' binary value of 14 development types, for both PBA40 and BASIS, along with aggregated 'allow residential' and 'allow non-residential' for each parcel
   * development intensity, i.e. max_dua, max_far, max_height, for both PBA40 and BASIS
* [devType_comparison.csv](https://mtcdrive.box.com/s/vbbhb3vs230krbmyhr2ma4d03qaqec7o): compares BASIS vs. PBA40 allowed development type data at parcel level. Each parcel falls into one of the following types for each [development type]:
    * 'both allow': the type of development is allowed in both PBA40 PLU data and BASIS BOC data
    * 'only pba40 allow'
    * 'only basis allow'
    * 'both not allow'
    * 'missing BASIS' (but has PBA40 data and deemed developable by pba50_zoningmod)
    * 'missing PBA40' (missing PBA40 data)
    * 'not developable' (parcels cannot be developed)

#### 1b [import_filegdb_layers.py](../../../utilities/import_filegdb_layers.py)

This script is helpful for merging the output of the previous script, ``p10_plu_boc_allAttrs.csv``, with the p10 parcel geographies into a geodatabase.
This one takes a while to run.  I copied the version I created here: ``M:\Data\GIS layers\UrbanSim_BASIS_zoning\UrbanSim_BASIS_zoning.gdb``

#### 1c [create_jurisdiction_map.py](create_jurisdiction_map.py)

This takes the previous gdb along with an accompanying ArcGIS project file (``M:\Data\GIS layers\UrbanSim_BASIS_zoning\UrbanSim_BASIS_zoning.aprx``)
and creates pdf maps of BASIS vs PBA40 data by jurisdiction.  See [Jurisdiction Maps BASISvsPBA40 box folder](https://mtcdrive.box.com/s/e2qck5p03sd53q0rxg91x1wphw6zg766).

#### [2_calculate_juris_basis_pba40_capacity_metrics.py](2_calculate_juris_basis_pba40_capacity_metrics.py)

For each of the plu/boc variables (allowed development types and intensities), we have a set of BASIS data and a set of data used for PBA40.

In order to determine if the BASIS data set is usable for a given variable X for a given jurisdiction, the script does the following:
* Using PBA40 data for all variables other than *X* and BASIS data for *X*, calculate several metrics including dwelling unit capacity of a jurisdiction (for residential variables), nonresidential square footage capacity of a jurisdiction (for nonresidential variables)
* Output those metrics for visualization with [juris_basis_pba40_capacity_metrics.twb](juris_basis_pba40_capacity_metrics.twb), which includes a threshold parameter for choosing a heuristic to use to determine how much difference in the capacity metric is OK

Input:
* ``p10_plu_boc_allAttrs.csv``: parcels joined with PBA40 and BASIS zoning information (allowed development types as well as intensities) and nodev flag from [1_PLU_BOC_data_combine.py](1_PLU_BOC_data_combine.py)

Output:
* [juris_basis_pba40_capacity_metrics.csv](https://mtcdrive.box.com/s/5tuil7p7vz4pzp0zet2bo185obd2wzsx): capacity metrics for each jurisdiction for each variable
* [juris_basis_pba40_capacity_metrics.log](https://mtcdrive.box.com/s/ihety0t5b9n3ad72obvkyulzt4n9xgti): debug log

#### [3_create_heuristic_hybrid_index.py](3_create_heuristic_hybrid_index.py)

Creates the heuristic hybrid index given a threshold argument.

Input:
* ``juris_basis_pba40_capacity_metrics.csv``: capacity metrics for each jurisdiction for each variable from [2_calculate_juris_basis_pba40_capacity_metrics.py](2_calculate_juris_basis_pba40_capacity_metrics.py)
* *heuristic threshold*: Input argument between 0 and 1, denoting acceptable percent difference between BASIS and PBA40 capacity metrics to accept BASIS data for a given variable for a given jurisdiction.

Output:
* [hybrid_index/idx_urbansim_heuristic.csv](hybrid_index/idx_urbansim_heuristic.csv), heuristic-driven hybrid index configuration for which BASIS variables to use for each jurisdiction

#### [dev_capacity_calculation_module.py](dev_capacity_calculation_module.py)
Module with methods to calculate 
* effective development capacity (refer to the [effective_max_dua](https://github.com/UDST/bayarea_urbansim/blob/0fb7776596075fa7d2cba2b9fbc92333354ba6fa/baus/variables.py#L808) and [effective_max_far](https://github.com/UDST/bayarea_urbansim/blob/0fb7776596075fa7d2cba2b9fbc92333354ba6fa/baus/variables.py#L852) calculations)
* raw development capacity (built-out capacity based on zoning)
* net development capacity (development capacity excluding parcels with certain characteristics)

#### [4_create_hybrid_urbansim_input.py](4_create_hybrid_urbansim_input.py)

Now that we have a hybrid config, let's create the input files for UrbanSim!

Input:
*  ``p10_plu_boc_allAttrs.csv``: parcels joined with PBA40 and BASIS zoning information (allowed development types as well as intensities) and nodev flag from [1_PLU_BOC_data_combine.py](1_PLU_BOC_data_combine.py)
* [hybrid_index/idx_urbansim_heuristic.csv](hybrid_index/idx_urbansim_heuristic.csv): hybrid configuration.  Will probably change when we have manual edits to but starting with heuristic version for now.

Output:

* ``p10_plu_boc_hybrid.csv``, parcel dataset with hybrid intensity/allowed development type columns
* ``zoning_parcels_pba50.csv``, maps parcels to a zoning id
* ``zoning_lookup_pba50.csv``, maps zoning id to characteristics (intensity and allowed development type)

#### [hybrid_index_fb_revision.ipynb](hybrid_index_fb_revision.ipynb)
Updates the hybrid index used in Draft Blueperint and tracks if the following zoning attributes have been updated for each jurisdiction.

Inputs:
* [``hybrid_index/idx_urbansim.csv``](hybrid_index/idx_urbansim.csv), hybrid index used to build Draft Blueprint hybrid base zoning input
* [``hybrid_index/hybrid_idx_update_10192020.csv``](hybrid_index/hybrid_idx_update_10192020.csv): BASIS recommendations on updating the hybrid index

Outputs:
* [``hybrid_index/idx_urbansim_fb_10192020.csv``](hybrid_index/idx_urbansim_fb_10192020.csv), updated hybrid index based on BASIS team's recommendation. To be used to construct Final Blueprint hybrid base zoning input. In addition to indexes, this file also has the following fields: 'updated_max_dua_idx', 'updated_max_far_idx', 'updated_res_blgType_idx', 'updated_nonres_blgType_idx'. They indicate if the relevant zoning attributes were updated. 'updated_res_blgType_idx' being True suggests one or more updates in 'HS_idx', 'HT_idx', 'HM_idx', or 'MR_idx'; 'updated_nonres_blgType_idx' being True indicates one or more updates in 'OF_idx', 'HO_idx', 'SC_idx', 'IL_idx', 'IW_idx', 'IH_idx', 'RS_idx', 'RB_idx', 'MR_idx', 'MT_idx', or 'ME_idx'.

## Scripts to build new zoningmods for certain scenarios

#### [build_EIR_zoningmods.ipynb](build_EIR_zoningmods.ipynb)

Generate new zoningmods for EIR based on Final Blueprint zoningmods files and new EIR assumptions.

Input:
* ``EIR_zoningmods.gdb\p10_pba50_coc_tbl_v2_02172021``, dBASE table of p10 parcels with 'coc_id' tagging indicating if the parcel is located within communities of concern
* ``p10_pba50_FBP_attr_20201110.csv``, parcel-level geographies tagging for Final Blueprint
* ``zoning_mods_24.csv``, Final Blueprint zoningmods lookup table
* ``juris_county_id.csv``, jurisdiction name - county_id crosswalk

Output:
* ``p10_pba50_cocid.csv``, p10 parcel_id - coc_id tagging crosswalk
* ``p10_pba50_EIR_attr_[date].csv``, parcel-level geographies tagging for EIR (note that this file still contains the taggings for previous plans and scenarios)
* ``zoning_mods_26_[date].csv``, zoningmods lookup table for EIR Alt1 (s26)


## Scripts/files to visualize zoningmod and compare development capacity between different zoningmod scenarios/versions

#### [calculate_upzoning_capacity.py](calculate_upzoning_capacity.py)

Calculate the raw and net zoned development capacity under certain zoningmod scenario, and compare the calculated capacity with BAUS run output for the same zoningmod scenario at TAZ and jurisdiction levels.

Input:
* ``p10.csv``, parcels with PARCEL_ID, ACRES attributes
* ``zoning_parcels_hybrid_pba50.csv``, p10 combined with zoning_id data output by 4_create_hybrid_urbansim_input.py
* ``zoning_lookup_hybrid_pba50.csv``, lookup table of zoning_id to allowable development types and intensities
* ``p10_pba50_attr.csv``, p10 combined with zoningmods categories data
* ``parcel_to_taz1454sub.csv``, p10 mapped to 1454 TAZ

Output: 
* ``compare_juris_capacity.csv``, jurisdiction-level development capacity metrics
* ``compare_taz_capacity.csv``, TAZ-level development capacity metrics

Output development capacity metrics:
* Calculated_RAW_CAPACITY for basezoning: 'zoned_du_basezoning', 'zoned_Ksqft_basezoning', 'job_spaces_basezoning'
* Calculated_RAW_CAPACITY for zoningmods: 'zoned_du_[zmods_scenario]', 'zoned_Ksqft_[zmods_scenario]', 'job_spaces_basezoning_[zmods_scenario]'
* Calculated_NET_CAPACITY for basezoning: 'zoned_du_vacant_basezoning', 'zoned_Ksqft_vacant_basezoning', 'job_spaces_vacant_basezoning', 'zoned_du_underbuild_basezoning', 'zoned_Ksqft_underbuild_basezoning', 'job_spaces_underbuild_basezoning', 'zoned_du_underbuild_noProt_basezoning', 'zoned_Ksqft_underbuild_noProt_basezoning', 'job_spaces_underbuild_noProt_basezoning'
* Calculated_NET_CAPACITY for zoningmods: 'zoned_du_vacant_[zmods_scenario]', 'zoned_Ksqft_vacant_[zmods_scenario]', 'job_spaces_vacant_[zmods_scenario]', 'zoned_du_underbuild_[zmods_scenario]', 'zoned_Ksqft_underbuild_[zmods_scenario]', 'job_spaces_underbuild_[zmods_scenario]', 'zoned_du_underbuild_noProt_[zmods_scenario]', 'zoned_Ksqft_underbuild_noProt_[zmods_scenario]', 'job_spaces_underbuild_noProt_[zmods_scenario]'

Output these metrics for visualization with:
* [development_capacity_comparison_DB.twb](development_capacity_comparison_DB.twb) for Draft Blueprint
* [development_capacity_comparison_FB.twb](development_capacity_comparison_FB.twb) for Final Blueprint

#### [zoningmods_map.py](zoningmods_map.py)
Dissolve parcels by zoningmodcat (``pba50zoningmodcat`` for Draft Blueprint and ``fbpzoningm`` for Final Blueprint), visualize the dissolved geographies with zoningmod parameters.

Input:
* ``p10.shp``, p10 parcels shapefile
* ``parcels_geography.csv``, p10 PARCEL_ID mapped to zoningmodcat
* ``zoning_mods_[zmods_scenario].csv``, zoningmodcat mapped to zoningmod parameters

Output:
* ``p10_zoningmods_[zmods_scenario].shp``, shapefile of parcels dissolved by zoningmodcat with zoningmods attribute.


## Scripts to update other plu-related UrbanSim input files

#### [update_parcels_geography.py](update_parcels_geography.py) 
Update the 'parcels_geography' file to incorporate [upzoning parameters](https://github.com/BayAreaMetro/bayarea_urbansim/blob/datatypes_dict/data/%5Bmod_date%5D_parcels_geography_dict.csv) into Draft Blueprint.

Inputs:
* [jurisId.csv](https://github.com/BayAreaMetro/petrale/blob/master/zones/jurisdictions/juris_county_id.csv): map jurisdiction name to jurisdiction ID
* [07_11_2019_parcels_geography.csv](https://mtcdrive.app.box.com/file/653711913275): Horizon parcels_geography.csv input
* [p10_pba50_attr_20200416](https://mtcdrive.box.com/s/zkxaf4gxn47oe716r4wqrp1raqfq8lhy): Draft Blueprint strategy geographies mapped to p10 PARCEL_ID
* pda_id_2020.csv (M:\Data\GIS layers\Blueprint Land Use Strategies\ID_idx): PARCEL_ID mapped to the most recent Draft Blueprint PDAs (see below **parcel_BlueprintGeos_index.py**).

Output: 
* [2020_04_17_parcels_geography.csv](https://mtcdrive.box.com/s/ryolqxotqq2wh805vfjqhf0a7xf29051) - without the new pda_id. This file was used in Draft Blueprint runs.
* [2020_07_10_parcels_geography.csv](https://mtcdrive.box.com/s/kh1xccmwwq8unqx699i3hgw0jwusyj49) - with the new pda_id named as 'pda_id_pba50' while the old pda_id was kept and named as 'pda_id_pba40'.

#### [parcel_BlueprintGeos_index.py](parcel_BlueprintGeos_index.py)
Map p10 PARCEL_ID to Draft Blueprint strategy geographies. Used for generating geography-level Urbansim output summaries based on parcel-level output.

Inputs:
* p10_PDA_06112020.csv (M:\Data\GIS layers\Blueprint Land Use Strategies\ID_idx\p10_PDA_06112020.csv): created in ArcGIS through spatial join of **p10 polygons** (M:\Data\GIS layers\UrbanSim smelt\2020 03 12\smelt.gdb) and [Draft Blueprint growth geography polygons](http://opendata.mtc.ca.gov/datasets/priority-development-areas-current?geometry=-129.633%2C36.372%2C-114.945%2C39.406)
* [p10_pba50_attr_20200416](https://mtcdrive.box.com/s/zkxaf4gxn47oe716r4wqrp1raqfq8lhy): Draft Blueprint strategy geographies (except for PDAs) mapped to p10 PARCEL_ID
  
Outputs (M:\Data\GIS layers\Blueprint Land Use Strategies\ID_idx):
* pda_id_2020.csv

#### [update_zoning_parcels.py](update_zoning_parcels.py) 
Update the 'nodev' and 'juris_id' fields of Horizon 'zoning_parcels.csv'
input with Draft Blueprint value while keeping other Horizon zoning information (e.g. development types, development intensities). The output is used for Draft Blueprint runs until a new zoning_parcels input is created based on BASIS BOC data. (For more, please see [base_zoning folder](https://github.com/BayAreaMetro/petrale/tree/master/policies/plu/base_zoning)).

#### [check_conservation_easement_parcels.ipynb](check_conservation_easement_parcels.ipynb)
Identify parcels that are within California Conservation Easement but were still considered as "developable" in UrbanSim (reflected in the 'nodev' field of parcels_geography.csv input).
The output of this script will be an input of [update_parcels_geography.py](update_parcels_geography.py) to update the 'nodev' field.

#### [final_mix_zoning.ipynb](final_mix_zoning.ipynb)
Create parcel-level final zoning info that reflects the max_dua applied in the developer model in UrbanSim - the higher of basezoning max_dua and zoningmods dua_up; also label the source of final max_dua - 'base zoning' or 'zoningmods'.
The output can be joined to parcel geospacial layers to create maps.
