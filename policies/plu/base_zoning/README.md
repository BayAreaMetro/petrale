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
* Hybrid index files: used to build hybrid base zoning by selecting more reasonable allowed development type and intensity data from PBA40 versus BASIS. 

Interim outputs: multiple versions of hybrid zoning aimed to help evaluate BASIS data for each zoning attribute, and to construct the hybrid index used for UrbanSim. Please see [README.md](hybrid_index/README.md) for details on interim hybrid zoning.

Final output: [index_urbansim_heuristics.csv](hybrid_index/idx_urbansim_heuristics.csv).

### [dev_capacity_calculation_module.py](dev_capacity_calculation_module.py)
Calculate effective development intensity (refer to the [effective_max_dua](https://github.com/UDST/bayarea_urbansim/blob/0fb7776596075fa7d2cba2b9fbc92333354ba6fa/baus/variables.py#L808) and [effective_max_far](https://github.com/UDST/bayarea_urbansim/blob/0fb7776596075fa7d2cba2b9fbc92333354ba6fa/baus/variahttps://mtcdrive.box.com/s/vbbhb3vs230krbmyhr2ma4d03qaqec7obles.py#L852) calculations) for PBA40 and BASIS and compare the results. Uses different hybrid versions of BASIS BOC data as generated from the previous step.

Input:
* various versions of "p10_plu_boc" hybrid data generated from the previous step

Output:
* various versions of development capacity, including both based on PBA40 zoning and hybrid zoning.  

### [create_heuristic_hybrid_index.py](create_heuristic_hybrid_index.py)
Input:
* various verions of interim hybrid zoning
Output:
* heuristic version of urbansim hybrid zoning

Please see [README.md](hybrid_index/README.md) for details on the process.

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