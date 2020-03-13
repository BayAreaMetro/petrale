The goal is to share an ArcGIS online map with internal and external partners to communicate UrbanSim's inputs, in other words, UrbanSim's understanding of the base-year demographic, economic, and land use situations of the region, as well as key Blueprint strategies underpinning PBA50.  

Three layers of data:
* Base-year TAZ-level popoulation, household, employment, and housing units
* BASIS zoning BOC data at the jurisdiction/zone level which reflects the development capacity of the region's land under existing local zoning ordidances and general plans 
* Zoningmods which reflects the Blueprint strategies which, in UrbanSim's scenario simulations, overrides local zoning ordinances and general plans

Layer attributes
* TAZ base-year
    * FID (OID)
    * Shape (Geometry)
    * objectid (Double)
    * taz1454 (Double)
    * district (Double)
    * county (String)
    * gacres (Double)
    * Shape__Are (Double)
    * Shape__Len (Double)
    * sd (Double)
    * county_id (Double)
    * tothh (Double)：total household count
    * totpop (Double): total population count
    * totemp (Double): total employement count
    * sfdu (Double): number of single-family housing units
    * mfdu (Double): number of multi-family housing units
    * units (Double): total number of housing units

* BASIS BOC
    * OBJECTID (OID)
    * Shape (Geometry)
    * PARCEL_ID (Double)
    * ACRES (Double)
    * COUNTY_ID (Double)
    * X (Double)
    * Y (Double)
    * plu_id (String)
    * plu_code (String)
    * plu_description (String)
    * Shape_Length (Double)
    * Shape_Area (Double)
    * max_far (String): maximum non-residential floor-area-ratio allowed
    * max_dua (String): maximum residential dwelling units per acre allowed
    * max_height (String): maximum height allowed
    * plu_county (String)
    * plu_jurisdiction (String): jurisdictions (incorporated places and unincorporated county areas) of which the zoning ordiance applies
    * hm (String): allows multi-family residential development (1; 0: not allowed; NaN: no data)
    * ho (String): allows hotel development 
    * hs (String): allows single-family residential development 
    * ht (String): allows townhomes development 
    * ih (String): allows heavy industry development 
    * il (String): allows light industry development 
    * iw (String): allows warehouse or logistics development 
    * me (String): allows mixed-use employment-focused development 
    * mr (String): allows mixed-use residential-focused development
    * mt (String): allows mixed-use industrial-focused development 
    * of (String): allows office development 
    * rb (String): allows big-box or regional development  
    * rs (String): allows general retail development 
    * sc (String): allows school development 

* Zoningmods
    * OBJECTID (OID)
    * Shape (Geometry)
    * PARCEL_ID (Double)
    * COUNTY_ID (Double)
    * X (Double)
    * Y (Double)
    * Shape_Length (Double)
    * Shape_Area (Double)
    * juris_id (String)
    * gg_id (String): growth geography designation
    * tra_id (String): tra area designation
    * sesit_id (String): combination of high-resource and high-displacement-risk area designation
    * ppa_id (String): 
    * exp2020_id (String)
    * pba50chcat (String): parcel categorization based on combinations of all strategies
    * exsfd_id (String)
    * chcatwsfd (String)
    * pba50zoningmodcat (String): concatenate jurisdiction name with pba50chcat 
    * nodev (SmallInteger)