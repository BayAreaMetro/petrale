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
This process creates csv files:
* parcels.csv
* buildings.csv
* households.csv
* jobs.csv
* residential_units????
These are then processed in the BAUS preprocessing model


---------

NOTES

Start with reprocessed assessor data (MVP). Each counties parcels are collected, cleaned, and put into a consistent coding system. For 2010 this was processed by Synthicity and inhouse using early 2011 assessors’ data (2005 for Marin). For 2015 this is being processed by the BASIS project using 2018 assessors’ data. 
Bring in CoStar data for commercial buildings and apartments; these replace assessor values completely. This database is proprietary and of fairly high quality though some locations require manual editing to ensure a partial match.
Bring in Redfin residential transaction data for ownership housing. This is a subset of recent sales. Can be about the same quality as assessors or a bit better. Have played with a mix of replacing assessors’ data (where a Redfin record exists) or replacing only missing values or assessors’ records.
Add in additional buildings (government, schools, institutional). These are not represented by any of the above datasets; Mike has built a list. 
Enhance missing CoStar values with assessor data? This optional step doubles back and fills in missing CoStar values. Doesn’t produce much improvement historically. 
Impute deed restricted units in pre-processing module in BAUS
Impute missing housing unit values in pre-processing module in BAUS
Impute missing commercial space values in pre-processing module in BAUS
Impute housing units: add additional units to existing residential buildings to meet adjusted zonal census totals

Impute commercial space: add additional square feet using the additional buildings table to meet zonal job totals (this is more rare but matters in a few spots)
Place households in housing units in pre-processing module in BAUS
Place jobs in commercial space in pre-processing module in BAUS
Run diagnostics
