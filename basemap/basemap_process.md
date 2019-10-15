# Basemap Development Process

The goal of basemap development is to have a representation of what is where at a point in time close to the current year. Most fundamentally, information about the the types of households and jobs within each MAZ is needed to provide the Travel Model with the locations of trip origins and destinations. Ideally, the basemap also includes additional higher resolution data (i.e., parcels, buildings) that is helpful in understanding the likelihood of future growth in households and/or jobs in each MAZ. I will briefly review the different datasets used in this process and then discuss two approaches to processing the data for use in exploratory analysis and urban modeling.

Many datasets provide information for the basemap:
* Parcels: polygons representing land ownership. There are just over 2 million of these and, in theory, they completely tile the region (in reality, they often overlap or leave gaps). The parcels vary in size form huge (e.g., most of the Presidio) to quite small. Tha majority are single family home lots but we are the least interested in those.
* Assessors' data: attributes that can be attached to the parcels. These describe characteristics of the building(s) on each parcel. Each county has a different format. They provide a lot of info on single family homes where there is a simple relationship of one home per parcel. When there multiple buildings on a parcel they can be represented by combinging them all into one mega-building or listing them separately. Sometime multiple buildings are also represented by stacking multiple identical parcels on top of each other, each with its own assessors' record. This is most common with condos.
* Buildings: points or polygons representing indiviudal structures. There is often one building per parcel but there can also be none or multiple (up to 100s, rarely). We don't have all of these in the region. We do have almost all commerical structures (including apartments) represented as points from Costar. We also have a growing proportion of building footprints from Open Stree Map.
* Ancillary data: aerial or satellite photography can provide info on whether or not a location has buildings
* Zones: Travel Model 2 has two nested zone systems. There as around 45K MAZs that are aggregations of census blocks. There are around 4500 TAZs (new system) that are modified census tracts.
* Establishments: point locations of each business location with a count of employees and a sectoral classification.
* External control totals: 

In the previous two Bay Area UrbanSim modeling rounds, the basemap process resulted in a map of (fairly) clean parcels that included collapsed data on all the buildings on the parcel. HHs and jobs were placed on the parcel/buildings and each parcel/building was in only one zone (i.e., one of 1454 old TAZs). I think we want to move to a new approach for this because Travel Model 2 has many more zones, there is inreasing data available, and the simplification in the old approach dissallowed some desirably analysis. The two new approaches require the same data cleaning and integration process but diverge in terms of data structure. They are:
* MicroMicro: Represent all buildings explicitly (either from CoStar/OSM or by using point devised from the parcels). Households and jobs are placed in these buildings. Buildings can only be in one MAZ and that is the one their inhabitants are summarized into. A building is also on parcel. The parcel information is used by the developer model when considering (re)development. A parcel can have multiple buildings and be in multiple MAZs.
* Synthetic pseudo-parcels: Sort of the reverse. 

Issues:
* scale and timeliness of census data
