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

### 1b [import_filegdb_layers.py](../../../utilities/import_filegdb_layers.py)

This script is helpful for merging the output of the previous script, ``p10_plu_boc_allAttrs.csv``, with the p10 parcel geographies into a geodatabase.
This one takes a while to run.  I copied the version I created here: ``M:\Data\GIS layers\UrbanSim_BASIS_zoning\UrbanSim_BASIS_zoning.gdb``

### 1c [create_jurisdiction_map.py](create_jurisdiction_map.py)

This takes the previous gdb along with an accompanying ArcGIS project file (``M:\Data\GIS layers\UrbanSim_BASIS_zoning\UrbanSim_BASIS_zoning.aprx``)
and creates pdf maps of BASIS vs PBA40 data by jurisdiction.  See [Jurisdiction Maps BASISvsPBA40 box folder](https://mtcdrive.box.com/s/e2qck5p03sd53q0rxg91x1wphw6zg766).

### [2_calculate_juris_basis_pba40_capacity_metrics.py](2_calculate_juris_basis_pba40_capacity_metrics.py)

For each of the plu/boc variables (allowed development types and intensities), we have a set of BASIS data and a set of data used for PBA40.

In order to determine if the BASIS data set is usable for a given variable X for a given jurisdiction, the script does the following:
* Using PBA40 data for all variables other than *X* and BASIS data for *X*, calculate several metrics including dwelling unit capacity of a jurisdiction (for residential variables), nonresidential square footage capacity of a jurisdiction (for nonresidential variables)
* Output those metrics for visualization with [juris_basis_pba40_capacity_metrics.twb](juris_basis_pba40_capacity_metrics.twb), which includes a threshold parameter for choosing a heuristic to use to determine how much difference in the capacity metric is OK

Input:
* ``p10_plu_boc_allAttrs.csv``: parcels joined with PBA40 and BASIS zoning information (allowed development types as well as intensities) and nodev flag from [1_PLU_BOC_data_combine.py](1_PLU_BOC_data_combine.py)

Output:
* [juris_basis_pba40_capacity_metrics.csv](https://mtcdrive.box.com/s/5tuil7p7vz4pzp0zet2bo185obd2wzsx): capacity metrics for each jurisdiction for each variable
* [juris_basis_pba40_capacity_metrics.log](https://mtcdrive.box.com/s/ihety0t5b9n3ad72obvkyulzt4n9xgti): debug log

### [3_create_heuristic_hybrid_index.py](3_create_heuristic_hybrid_index.py)

Creates the heuristic hybrid index given a threshold argument.

Input:
* ``juris_basis_pba40_capacity_metrics.csv``: capacity metrics for each jurisdiction for each variable from [2_calculate_juris_basis_pba40_capacity_metrics.py](2_calculate_juris_basis_pba40_capacity_metrics.py)
* *heuristic threshold*: Input argument between 0 and 1, denoting acceptable percent difference between BASIS and PBA40 capacity metrics to accept BASIS data for a given variable for a given jurisdiction.

Output:
* [hybrid_index/idx_urbansim_heuristic.csv](hybrid_index/idx_urbansim_heuristic.csv), heuristic-driven hybrid index configuration for which BASIS variables to use for each jurisdiction

### [dev_capacity_calculation_module.py](dev_capacity_calculation_module.py)
Module with methods to calculate 
* effective development capacity (refer to the [effective_max_dua](https://github.com/UDST/bayarea_urbansim/blob/0fb7776596075fa7d2cba2b9fbc92333354ba6fa/baus/variables.py#L808) and [effective_max_far](https://github.com/UDST/bayarea_urbansim/blob/0fb7776596075fa7d2cba2b9fbc92333354ba6fa/baus/variables.py#L852) calculations)
* raw development capacity (built-out capacity based on zoning)
* net development capacity (development capacity excluding parcels with certain characteristics)

### [4_create_hybrid_urbansim_input.py](4_create_hybrid_urbansim_input.py)

Now that we have a hybrid config, let's create the input files for UrbanSim!

Input:
*  ``p10_plu_boc_allAttrs.csv``: parcels joined with PBA40 and BASIS zoning information (allowed development types as well as intensities) and nodev flag from [1_PLU_BOC_data_combine.py](1_PLU_BOC_data_combine.py)
* [hybrid_index/idx_urbansim_heuristic.csv](hybrid_index/idx_urbansim_heuristic.csv): hybrid configuration.  Will probably change when we have manual edits to but starting with heuristic version for now.

Output:

* ``p10_plu_boc_hybrid.csv``, parcel dataset with hybrid intensity/allowed development type columns
* ``zoning_parcels_pba50.csv``, maps parcels to a zoning id
* ``zoning_lookup_pba50.csv``, maps zoning id to characteristics (intensity and allowed development type)