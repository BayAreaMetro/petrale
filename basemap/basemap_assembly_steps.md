# Basemap Assembly Steps
The basemap is a geodatabase containing the region's parcels, buildings, households, and jobs in the baseyear (2015 for PBA50). It is built in two major stages:
1. The assembly and cleaning of raw dataset. This is done through manual data cleaning in excel and python scripts in ArcGIS Pro and is described here.
2. Imputation of missing data to conform to regional totals. This is done through python scripts integrated into Bay Area UrbanSim and is described at http://bayareametro.github.io/bayarea_urbansim/input_data/.

## Start with Assessors Parcel Data
Each county's parcels (i.e., polygons denoting each property) and their attributes (i.e., the assessors role containing info used to value each property) are collected from the county assessor or another source. To bring this data into one system, the polys are reprojected into a common projection system and the attributes are put into a consistent coding system. This process produces two products:
* A set of polygons that represent each separate area of land ownership. Ideally, these "tile" each county, meaning cover entirely without overlap so that the sum of the areas of the polys equals the area of the county. In reality this is a complicated by various factors. Neighboring parcels may overlap a bit from poor drawing and this is often OK if it isn't extreme. Parcels may also cover water areas (e.g., the Bay) or not cover particular lakes. They generally don't cover public right of ways (unless they do as in Sonoma County). Very problematic is that some assessors offices build stacks of polys to represent multiple ownership records associated with one piece of land (e.g., condos). They key is to get the parcels to more or less represent the land area of each county in a manner consistent enough that it can be compared to the total amount of land in the county for QA/QC. These parcels are where buildings can be built in the model so errors can have large impacts on capacity.
* A set of records indicating buildings or pseudo-buildings. This is fairly straightforward for most parcels as there is one poly and one attribute record in the raw data indicating a piece of land and the building that is on it. The goal is to get as much info as needed to describe each building from its attributes in the assessors file (e.g., number of housing units, size, age, asssessed value, last sale price). However, many buildings of interest are more complicated. In some cases, there will be multiple buildings associated with a single parcel and coded as a single record that combines information from each building (a pseudo-building). Mostly we have carried these forward as is from the assessors data. An opposite situation will see multiple records indicating multiple building or housing units associated with a single parcel. Some of these can be kept as is since we allow multiple building per parcel in the model basemap. However, condos are often set up so one record represents a housing unit that is attached to a stacked poly. Ideally these are summed up and attached to the single poly used in the land parcel map discussed above. Care must be taken to properly treat any values that are already summarized. Tis is messy and varies by county and sometimes within a county. Key is to step back and remember that the record was built to assess values for taxation but we need to move things around to get a physical map of sturctures and housing units. 


For 2010 this was processed by Synthicity and inhouse using early 2011 assessors’ data (2005 for Marin). For 2015 this is being processed by the BASIS project using 2018 assessors’ data.


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

Start with reprocessed assessor data (MVP). 
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
