# petrale
Bay Area Metro Internal Urban GeoDatabase

This repository contains land use/urban economics data and related code for Bay Area Metro. The major categories of data and code (equivalent to the directory structure above) are:

* applications: the various products and analyses supported by basis
* basemap: information on the current state of buildings and their inhabitants
* control totals: region-wide forecasts for households and employment
* deed restricted units: a database of current housing with low income residency requirements
* institutions: a current and forecast database of large entities (e.g., universities, hospitals) and group quarters
* pipeline: a list of building projects recently completed, under construction, or approved
* policies: information on existing local and regional land use policies
* scenarios: changes to policies and assumptions used to build alternate growth sceanrios
* scripts: code to modify or integrate datasets
* tests: code to assure the validity of database changes
* zones: various boundary files and related data for TAZs, MAZs, Jurisdictions, PDAs, etc; geographic lookups


--------------
## How to Use This Repository

Common File Types
* each data file has a name and generally ends with a csv denoting that is it a comma separated values text file
* most data files have a corresponding file with "meta" prepended: this contains information about the structure and creation of the data file
* most data files have a corresponding file with "temp" prepended: this is template with blank values
* most data files have a corresponding file with "dict" prepended: this contains a variable dictionary for that data file


Backwards
1) start with product 
2) examines its readme and metadata file (i.e., starts with 'meta' and means information about the data)
3) move back toward original main category indicated in metadata file
4) look at readme and metadata file
5) look at code and raw data
