# Development Projects Process

## 1. Data sources:
* Basemap parcels (p10_pba50 at m:\ )
* Costar data ( and at m:\
* Redfin data ( and and and at m:\
* Parcel processing data ( at m:\ )
* BASIS pipeline data (at portal)
* MTC manual pipeline (at [portal](https://arcgis.ad.mtc.ca.gov/portal/home/item.html?id=3a85a3dbfbbb44f3b9250930b685f570))
* Opportunity Sites:
* *  public land 
* * mall & office parks
* * incubator
* * ppa
* * manual oppsites

## 2. Process
The overall approach of producing the development project file is to:
* spatially join parcels to each point file of new buildings --[code](https://github.com/BayAreaMetro/petrale/blob/55f714d5353e345ca8c0955e32c7694cad6c8d50/basemap/development_projects.py#L286)--
* recompute all fields in each point file so that they exactly the same schema --[code](https://github.com/BayAreaMetro/petrale/blob/55f714d5353e345ca8c0955e32c7694cad6c8d50/basemap/development_projects.py#L289-L402)--
* clean out old fields --[code](https://github.com/BayAreaMetro/petrale/blob/55f714d5353e345ca8c0955e32c7694cad6c8d50/basemap/development_projects.py#L416-L428)--
* merge Manual pipeline, Costar, Redfin, Parcel processing data, BASIS pipeline data point files into one shapefile (pipeline) including only records w incl=1 --[code](https://github.com/BayAreaMetro/petrale/blob/55f714d5353e345ca8c0955e32c7694cad6c8d50/basemap/development_projects.py#L1229-L1237)--
* merge point file of opportunity sites with pipeline to form development_projects --[code](https://github.com/BayAreaMetro/petrale/blob/55f714d5353e345ca8c0955e32c7694cad6c8d50/basemap/development_projects.py#L1638-L1644)--
* run diagnostics
* if a parcel has multiple buildings added to it, change to "add" instead of "build" --[code](https://github.com/BayAreaMetro/petrale/blob/55f714d5353e345ca8c0955e32c7694cad6c8d50/basemap/development_projects.py#L2024-L2061)--
* export
* import again to fix data type --[code](https://github.com/BayAreaMetro/petrale/blob/55f714d5353e345ca8c0955e32c7694cad6c8d50/basemap/development_projects.py#L2111-L2186)--
* update building file --[code](https://github.com/BayAreaMetro/petrale/blob/55f714d5353e345ca8c0955e32c7694cad6c8d50/basemap/development_projects.py#L2200)--

