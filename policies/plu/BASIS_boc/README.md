## Purposes 
* evaluate the BASIS BOC data (zoning data collected through BASIS) by comparing the build-out-capacity of the Bay Area land under BASIS BOC scheme versus PBA40 planned land use scheme
* visualize BASIS allowed development type to assist with QA/QC
* analyze the build-out-capacity of certain types of parcels, e.g., vacant parcels, parcels with a investment to land ratio (ILR), etc. 

## Key components
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
* export the analysis results to [Box](https://mtcdrive.app.box.com/folder/107845568866) for visualization and inspection in ArcGIS

### BOC_PLU_dev_capacity_mapping
Map key base zoning attributes (PBA40 PLU and BASIS BOC) in five groups at the parcel level:
* BASIS selected allowed development types
	* Parcels where BASIS allows HM (multi-family development)
	* Parcels where BASIS allows MR (mixed-use) but doesn't allow HM
	* Compare BASIS and PBA40 values on HM
* Residential parcels MAX DUA (BASIS vs. PBA40 comparison) (2 layers)
* Residential parcels development capacity in units (BASIS vs. PBA40) (2 layers)
* Non-residential parcels development capacity in thousand sqft (BASIS vs. PBA40) (2 layers)
* Non-residential parcels development capacity in number of employees (BASIS vs. PBA40) (2 layers)
The resulting map is avalable on ArcGIS online for MTC internal reviews. Current version: 
https://mtc.maps.arcgis.com/home/item.html?id=97fdafa794af483eacffb82d08d3a57a

## Data sources
Data sets used in this script are located in either the Box folder ['Bay Area UrbanSim 1.5 > PBA50 > Input Data Analysis'](https://mtcdrive.app.box.com/folder/106560772938) or the UrbanSim Github folder ['data'](https://github.com/BayAreaMetro/bayarea_urbansim/tree/master/data). 
* [p10](https://mtcdrive.app.box.com/folder/106871371254)
* [b10](https://mtcdrive.app.box.com/file/633052759622)
* [2020_03_06_zoning_parcels (p10 - PBA40 zoning_id mapping)](https://mtcdrive.app.box.com/file/633053926869)
* [zoning_lookup (PBA40 zoning_id - planned land use mapping)](https://github.com/BayAreaMetro/bayarea_urbansim/blob/master/data/zoning_lookup.csv)
* [p10_boc_opt_B_v1d_geo (BASIS BOC)](https://mtcdrive.app.box.com/file/639116002730)
* p_hb (hybrid Blueprint Option 2 parcel)
* b_hb (BASIS building)

