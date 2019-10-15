# Basemap Assembly Steps

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


