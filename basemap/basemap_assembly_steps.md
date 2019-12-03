# Basemap Assembly Steps
The basemap is a geodatabase containing the region's parcels, buildings, households, and jobs in the baseyear (2015 for PBA50). It is built in two major stages:
1. The assembly and cleaning of raw dataset. This is done through manual data cleaning in excel and python scripts in ArcGIS Pro and is described here.
2. Imputation of missing data to conform to regional totals. This is done through python scripts integrated into Bay Area UrbanSim and is described at http://bayareametro.github.io/bayarea_urbansim/input_data/.

## Start with Assessors Parcel Data
The process begins by taking a poly map and associated info from the assessor in each of the nine counties. These data has been processed to 


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



### Output the Resultant Data to the H5
This process creates csv file with 
