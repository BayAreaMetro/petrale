**[update_parcels_geography.py](update_parcels_geography.py)**: update the 'parcels_geography' file to incorporate [upzoning parameters](https://github.com/BayAreaMetro/bayarea_urbansim/blob/datatypes_dict/data/%5Bmod_date%5D_parcels_geography_dict.csv) into Draft Blueprint.

Inputs:
* [jurisId.csv](https://github.com/BayAreaMetro/petrale/blob/master/zones/jurisdictions/juris_county_id.csv): map jurisdiction name to jurisdiction ID
* [07_11_2019_parcels_geography.csv](https://mtcdrive.app.box.com/file/653711913275): Horizon parcels_geography.csv input
* [p10_pba50_attr_20200416](https://mtcdrive.box.com/s/zkxaf4gxn47oe716r4wqrp1raqfq8lhy): Draft Blueprint strategy geographies mapped to p10 PARCEL_ID
* pda_id_2020.csv (M:\Data\GIS layers\Blueprint Land Use Strategies\ID_idx): PARCEL_ID mapped to the most recent Draft Blueprint PDAs (see below **parcel_BlueprintGeos_index.py**).

Output: 
* [2020_04_17_parcels_geography.csv](https://mtcdrive.box.com/s/ryolqxotqq2wh805vfjqhf0a7xf29051) - without the new pda_id. This file was used in Draft Blueprint runs.
* [2020_07_10_parcels_geography.csv](https://mtcdrive.box.com/s/kh1xccmwwq8unqx699i3hgw0jwusyj49) - with the new pda_id named as 'pda_id_pba50' while the old pda_id was kept and named as 'pda_id_pba40'.

**[parcel_BlueprintGeos_index.py](parcel_BlueprintGeos_index.py)**: map p10 PARCEL_ID to Draft Blueprint strategy geographies. Used for generating geography-level Urbansim output summaries based on parcel-level output.

Inputs:
* p10_PDA_06112020.csv (M:\Data\GIS layers\Blueprint Land Use Strategies\ID_idx\p10_PDA_06112020.csv): created in ArcGIS through spatial join of **p10 polygons** (M:\Data\GIS layers\UrbanSim smelt\2020 03 12\smelt.gdb) and [Draft Blueprint growth geography polygons](http://opendata.mtc.ca.gov/datasets/priority-development-areas-current?geometry=-129.633%2C36.372%2C-114.945%2C39.406)
* [p10_pba50_attr_20200416](https://mtcdrive.box.com/s/zkxaf4gxn47oe716r4wqrp1raqfq8lhy): Draft Blueprint strategy geographies (except for PDAs) mapped to p10 PARCEL_ID
  
Outputs (M:\Data\GIS layers\Blueprint Land Use Strategies\ID_idx):
* pda_id_2020.csv

**[update_zoning_parcels.py](update_zoning_parcels.py)**: update the 'nodev' and 'juris_id' fields of Horizon 'zoning_parcels.csv'
  input with Draft Blueprint value while keeping other Horizon zoning information (e.g. development types, development intensities). The output is used for Draft Blueprint runs until a new zoning_parcels input is created based on BASIS BOC data. (For more, please see [base_zoning folder](https://github.com/BayAreaMetro/petrale/tree/master/policies/plu/base_zoning)).