# Development Projects Process

## 1. Data sources:
* Basemap parcels (p10_pba50 at [smelt](https://mtcdrive.box.com/s/036crj8h6naqg016l079g0coybv8jsal) geodatabase)
* MTC manual pipeline (at [portal](https://arcgis.ad.mtc.ca.gov/portal/home/item.html?id=3a85a3dbfbbb44f3b9250930b685f570))
* Costar data (cs1115 and cs1620 at [smelt](https://mtcdrive.box.com/s/036crj8h6naqg016l079g0coybv8jsal) geodatabase)
* Redfin data (rf19_sfr1115, rf19_condounits1115, rf19_othertypes1115, rf19_sfr1619, and rf19_multiunit1619 at [smelt](https://mtcdrive.box.com/s/036crj8h6naqg016l079g0coybv8jsal) geodatabase)
* Parcel processing data (basis_pb_new_20200312 at [smelt](https://mtcdrive.box.com/s/036crj8h6naqg016l079g0coybv8jsal) geodatabase)
* BASIS pipeline data (basis_pipeline_20200228 at [smelt](https://mtcdrive.box.com/s/036crj8h6naqg016l079g0coybv8jsal) geodatabase)
* Opportunity Sites:
* * public land (at [portal](https://arcgis.ad.mtc.ca.gov/portal/home/item.html?id=8a9dfd54baaa4955b9f3dbbb4f757c64))
* * mall & office parks (at [portal](https://arcgis.ad.mtc.ca.gov/portal/home/item.html?id=04c1c2ffee824239bffa9ec9a27504a8))
* * incubator
* * ppa
* * manual oppsites (at [portal](https://arcgis.ad.mtc.ca.gov/portal/home/item.html?id=1a875fe466114482ad6847a925433512))

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

