**[zoningmodcat_update.py](zoningmodcat_update.py)**: update the 'parcels_geography' file to incorporate [upzoning parameters](https://github.com/BayAreaMetro/bayarea_urbansim/blob/datatypes_dict/data/%5Bmod_date%5D_parcels_geography_dict.csv) into Draft Blueprint.

Inputs:
* [jurisId.csv](https://github.com/BayAreaMetro/petrale/blob/master/zones/jurisdictions/juris_county_id.csv): map jurisdiction name to jurisdiction ID
* [07_11_2019_parcels_geography.csv](https://mtcdrive.app.box.com/file/653711913275): Horizon parcels_geography.csv input
* [p10_pba50_attr_20200416](https://mtcdrive.box.com/s/zkxaf4gxn47oe716r4wqrp1raqfq8lhy): Draft Blueprint strategy geographies mapped to p10 PARCEL_ID
* [p10_geo_shp.shp](https://mtcdrive.app.box.com/folder/110544749604): (option) for dissolve parcels at pba50 zoningmodcat level

Output: 
* [2020_04_17_parcels_geography.csv](https://mtcdrive.box.com/s/ryolqxotqq2wh805vfjqhf0a7xf29051)

**[parcel_BlueprintGeos_index.py](parcel_BlueprintGeos_index.py)**: map p10 PARCEL_ID to Draft Blueprint strategy geographies. Used for generating geography-level Urbansim output summaries based on parcel-level output.

Inputs:
* p10_PDA_06112020.csv (M:\Data\GIS layers\Blueprint Land Use Strategies\ID_idx\p10_PDA_06112020.csv): created in ArcGIS through spatial join of [p10 polygons](M:\Data\GIS layers\UrbanSim smelt\2020 03 12\smelt.gdb) and [Draft Blueprint growth geography polygons](http://opendata.mtc.ca.gov/datasets/priority-development-areas-current?geometry=-129.633%2C36.372%2C-114.945%2C39.406
* [p10_pba50_attr_20200416](https://mtcdrive.box.com/s/zkxaf4gxn47oe716r4wqrp1raqfq8lhy): Draft Blueprint strategy geographies (except for PDAs) mapped to p10 PARCEL_ID
  
Outputs (M:\Data\GIS layers\Blueprint Land Use Strategies\ID_idx):
* pda_id_2020.csv
* hra_id_2020.csv
* tra_id_2020_s202122.csv

**[pba50zoningmod_capacity_calculation.ipynb](pba50zoningmod_capacity_calculation.ipynb)**: calculate PBA50 Zoningmods development capacity - non-resident square footage and residential units - for a specified zoningmod scenario at the county and jurisdiction levels. Include capacity on certain types of parcels, e.g., vacant parcels, parcels with a investment to land ratio (ILR).

Inputs:
* [03_06_2020_parcels_geography (p10 - PBA50 zoningmod mapping)](https://mtcdrive.app.box.com/file/633053917892)
* [zoningmod scenarios](https://github.com/BayAreaMetro/bayarea_urbansim/tree/master/data)
* [p10_boc_opt_B_v1d_geo (BASIS BOC)](https://mtcdrive.app.box.com/file/639116002730)
* p_hb (hybrid Blueprint Option 2 parcel)
* b_hb (BASIS building)
