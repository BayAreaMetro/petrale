## Purposes
* Associate BluePrint zoning strategies (PBA50 zoningmods) with UrbanSim basemap (parcels). 
* Analyze the development capacity of various PBA50 zoningmod scenarios; focus on certain types of parcels, e.g., vacant parcels, parcels with a investment to land ratio (ILR), etc.

## Key components
### PBA50 zoningmod for parcels
* [zoningmodcat_update.ipynb](https://github.com/BayAreaMetro/petrale/blob/master/policies/plu/zoningmods/zoningmodcat_update.ipynb): update the 'parcels_geography' file to assign a 'pba50_zoningmodcat' to each parcel. 'pba50_zoningmodcat' represents the combination of multiple BluePrint strategies. 
#### Data sources
* [jurisId.csv]: map jurisdiction name to jurisdiction ID
* [07_11_2019_parcels_geography.csv]: old zoningmod file used in PBA40 and Horizon
* [p10_pba50_attr_20200407.csv]: BluePrint strategies coded into pba50 zoningmodcat
* [p10_geo_shp.shp](option): for dissolve parcels at pba50 zoningmodcat level

### PBA50 Zoningmods development capacity 
* merge the data with PBA zoningmod data
* merge the data with BASIS building data
* calculate the development capacity - non-resident square footage and residential units - for each zoningmod scenario at the county and jurisdiction levels
#### Data sources
* [03_06_2020_parcels_geography (p10 - PBA50 zoningmod mapping)](https://mtcdrive.app.box.com/file/633053917892)
* [zoningmod scenarios](https://github.com/BayAreaMetro/bayarea_urbansim/tree/master/data)
* [p10_boc_opt_B_v1d_geo (BASIS BOC)](https://mtcdrive.app.box.com/file/639116002730)
* p_hb (hybrid Blueprint Option 2 parcel)
* b_hb (BASIS building)
