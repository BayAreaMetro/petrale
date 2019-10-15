# Basemap

This directory contains the data needed to build a "current year" map of the region's parcels, buildings, residents, and employment. The most recent base or "current" year has been 2010 but it may be updated to 2015 in the next round. This objective map of what is on the ground now is built from:
* parcels:
* commercial buildings:
* historic buildings: list of parcels that cannot be redeveloped because they are historic
* nodev list: list of parcels that cannot be developed in a future forecast

Once a good map of land and buildings has been pulled together and cleaned, additional buildings are imputed and households/jobs are sited within the buildings. The process is detailed [here](basemap_process.md).

This map is used for multiple purposes:
* it serves as the startng point from which the UrbanSim land use forecast is made
* it is convrted to the Bay Area Land Use Map for public use
* it provides a high resolution repressenttaion of the region for use in transportation, resillience, and environmental studies
