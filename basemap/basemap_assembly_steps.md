# Basemap Assembly Steps
The basemap is a geodatabase containing the region's parcels, buildings, households, and jobs in the baseyear (2015 for PBA50). It is built in two major stages:
1. The assembly and cleaning of raw dataset. This is done through manual data cleaning in excel and python scripts in ArcGIS Pro and is described here.
2. Imputation of missing data to conform to regional totals. This is done through python scripts integrated into Bay Area UrbanSim and is described at http://bayareametro.github.io/bayarea_urbansim/input_data/.

## Assemble and Clean Parcel Geometry
* Parcel information comes from each of the nine counties
* The information comes as parcels polygons and onee or more attribute tables that can be joined ot the polygons
* Most parcels have a one-to-one relationship with their attributes so you can see the attributes as describing as "pseudo-building" in that multiple buildings on a parcel are combined into one record
* However, sometimes the relationship is one-to-many with multiple buildings or condos per parcel
* Note that some parcels are stacked (i.e., miultiple identical copies on top of each other. This is a common way to represent parcels. IN this case, the attributes may need to be joined before any duplicate parcel polys are deleted
## ETL Parcel Atttribute Data
1.
## Add Additional Building Information
* costar
* add_building.csv
## Impute and Clean




## BASIS Processing
The BASIS team produces three files: parcel geometry, parcel attributes, and buildings. 

## Basemap Enhancement

### Schools


### Additional Buildings


### Commercial Real Estate


### Fill In Missing Values Using xxxx






### Tag Parcels with Zones
zone_id, taz22, maz, school districts
