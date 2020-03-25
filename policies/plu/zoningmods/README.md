## This script aims to - 
* create a hybrid base zoning PLU data for base-year parcels as a part of the UrbanSim basemap
* analyze the development capacity of various PBA50 zoningmod scenarios; focus on certain types of parcels, e.g., vacant parcels, parcels with a investment to land ratio (ILR), etc.

## Key components and steps
### PBA50 Zoningmods development capacity 
* merge the hybrid parcel data (Blueprint Option 2) with BASIS BOC data
* merge the data with PBA zoningmod data
* merge the data with BASIS building data
* calculate the development capacity - non-resident square footage and residential units - for each zoningmod scenario at the county and jurisdiction levels

## Data sources
* [03_06_2020_parcels_geography (p10 - PBA50 zoningmod mapping)](https://mtcdrive.app.box.com/file/633053917892)
* [zoningmod scenarios](https://github.com/BayAreaMetro/bayarea_urbansim/tree/master/data)
* [p10_boc_opt_B_v1d_geo (BASIS BOC)](https://mtcdrive.app.box.com/file/639116002730)
* p_hb (hybrid Blueprint Option 2 parcel)
* b_hb (BASIS building)