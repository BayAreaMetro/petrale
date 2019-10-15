Sea level rise data used for the Bay Area UrbanSim SLR model is from BCDC's Adapting to Rising Tides project. The data is prepared for the model with the following steps:

1) sea_level_rise/gis_output: ArcGIS operations are used to intersect the BCDC SLR polygons with Bay Area parcels
2) sea_level_rise/scripts/parcels_with_inundation.ipynb: a notebook is used to organize the GIS output by inundation level
3) sea_level_rise/output: Python output is stored for use in the model
