## This script aims to - 
* evaluate the BASIS BOC data (zoning data collected through BASIS) by comparing the build-out-capacity of the Bay Area land under BASIS BOC scheme versus PBA40 planned land use scheme
* visualize BASIS allowed development type to assist with QA/QC
* analyze the build-out-capacity of certain types of parcels, e.g., vacant parcels, parcels with a investment to land ratio (ILR), etc. 
* analyze the build-out-capacity of various zoningmod scenarios

## Key components and steps
### BASIS BOC data evaluation
* merge p10 (parcel data used in PBA40) with PLU10 (planned land use data used in PBA40)
* merge p10 data with BASIS BOC (build-out-capacity data collected in the BASIS process, to be used as planned land use in PBA50)
* merge the data with b10 (building data used in PBA40) to assign parcel characteristics, e.g. vacancy, ILR, etc.
* calculate the build-out-capacity for all parcels as well as various parcel groups at the county and jurisdiction levels
### BOC_PLU_comp_mapping
* merge p10 (parcel data used in PBA40) with PLU10 (planned land use data used in PBA40)
* merge p10 data with BASIS BOC allowed development type
* category each parcel into one of the following types for each [development type](https://github.com/BayAreaMetro/petrale/blob/master/incoming/dv_buildings_det_type_lu.csv)
    * 'both allow': the type of development is allowed in both PBA40 PLU data and BASIS BOC data
    * 'only pba40 allow'
    * 'only basis allow'
    * 'both not allow'
    * 'missing BASIS BOC' (but PBA40 data is available)
    * 'other' (missing PBA40 data)
### PBA50 Zoningmod scenario evaluation
* merge the hybrid parcel data (Blueprint Option 2) with BASIS BOC data
* merge the data with PBA zoningmod data
* merge the data with BASIS building data
* calculate the build-out-capacity for each zoningmod scenarios at the county and jurisdiction levels

## Data sources
Data sets used in this script are located in either the Box folder ['Bay Area UrbanSim 1.5 > PBA50 > Input Data Analysis'](https://mtcdrive.app.box.com/folder/106560772938) or the UrbanSim Github folder ['data'](https://github.com/BayAreaMetro/bayarea_urbansim/tree/master/data). 
* [p10](https://mtcdrive.app.box.com/folder/106871371254)
* [b10](https://mtcdrive.app.box.com/file/633052759622)
* [2020_03_06_zoning_parcels (p10 - PBA40 zoning_id mapping)](https://mtcdrive.app.box.com/file/633053926869)
* [zoning_lookup (PBA40 zoning_id - planned land use mapping)](https://github.com/BayAreaMetro/bayarea_urbansim/blob/master/data/zoning_lookup.csv)
* [p10_boc_v3_geo_tbl_20200311 (BASIS BOC)](https://mtcdrive.app.box.com/folder/106871371254)
* p_hb (hybrid Blueprint Option 2 parcel)
* b_hb (BASIS building)
* [03_06_2020_parcels_geography (p10 - PBA50 zoningmod mapping)](https://mtcdrive.app.box.com/file/633053917892)
* [zoningmod scenarios](https://github.com/BayAreaMetro/bayarea_urbansim/tree/master/data)
