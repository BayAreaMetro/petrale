# coding: utf-8

import arcpy

# set enviro
arcpy.env.workspace = "E:/baydata/smelt.gdb"
#arcpy.env.workspace = "D:/Users/blu/Box/baydata/smelt/2020 01 16/smelt.gdb"

# This script brings together many different datasets that each offer some info
# on development in the region from 2011 on. Overall approach is to:
# 1 spatially join parcels to each point file of new buildings
# 2 recompute all fields in each point file so that they exactly the same schema 
# 3 clean out old fields 
# 4 merge point files into one shapefile (pipeline) including only records w incl=1
# 5 merge point file of opportunity sites with pipeline to form development_projects
# 6 run diagnostics
# 7 remove duplicates by manually or automatically switching incl to 0 or another code
# 8 build a shapefile of buildings to demolish
# 9 export a csv file with buildings to build and demolish

###BL: I am organizing the process by data sources, so that it is easy to replicate the process

### First need to know what's in the geodatabase, for now I couldn't find a way to list all datasets, feature, and tables using a code.
### but afte I made the fold connection, it shows that smelt.gdb contains 2 tables, 3 feature classes. and 2 feature datasets - built and dp1620

# SET VARS
# input
p10 = "p10" # 2010 parcels

### costar data
cs1620 = "cs1620" # costar data  2016-2020
cs1115 = "cs1115" # costar data  2011-2015

### redfin data
rfsfr1619 = "rf19_sfr1619" # redfin SFD data 2016-2019
rfmu1619 = "rf19_multiunit1619" # redin MFD data 2016-2019
rfsfr1115 = "rf19_sfr1115" # redfin SFD data 2011-2015
rfcondo1115 = "rf19_condounits1115" # redfin condo data 2011-2015
rfother1115 = "rf19_othertypes1115" # redfin other data 2011-2015


### BASIS pipleline data
basis_pipeline = "basis_pipeline_20200113" 

### manually maintained pipeline data
manual_dp = "manual_dp_20200113" 

# opportunity sites that keep their scen status from gis file
opp_sites = "oppsites_20200116" 

#get an empty list to add feature class to so that they can be merged in the end all together

l = []

# output
# pipeline shp
# development_projects shp
# development_projects csv
# demolish csv

### for costar data
### create a list of feature class
cs = [cs1115,cs1620]
for fc in cs:
	joinFN = 'ttt_' + arcpy.Describe(fc).name + '__p10'
	### 1 SPATIAL JOINS
	arcpy.SpatialJoin_analysis(fc, p10, joinFN)
	### 2 VARIABLE CLEANING 
	
	# rename any conflicting field names
	arcpy.AlterField_management(joinFN, "building_name", "cs_building_name")
	arcpy.AlterField_management(joinFN, "city", "cs_city")
	arcpy.AlterField_management(joinFN, "Zip", "cs_zip")
	arcpy.AlterField_management(joinFN, "rent_type", "cs_rent_type")
	arcpy.AlterField_management(joinFN, "year_built", "cs_year_built")
	arcpy.AlterField_management(joinFN, "last_sale_price", "cs_last_sale_price")
	arcpy.AlterField_management(joinFN, "last_sale_date", "cs_last_sale_date")
	arcpy.AlterField_management(joinFN, "Average_Weighted_Rent", "cs_average_weighted_rent")
	arcpy.AlterField_management(joinFN, "x", "p_x") # this is from the parcel centroid
	arcpy.AlterField_management(joinFN, "y", "p_y") # this is from the parcel centroid
	arcpy.AlterField_management(joinFN, "geom_id", "p_geom_id") # this is from the parcel 
	# add fields and calc values
	# full list development_projects_id,raw_id,building_name,site_name,action,scen0,scen1,
	# address,city,zip,county,x,y,geom_id,year_built,duration,building_type_id,building_type,building_sqft,non_residential_sqft,
	# residential_units,unit_ave_sqft,tenure,rent_type,stories,parking_spaces,Average Weighted Rent,rent_ave_sqft,rent_ave_unit,
	# last_sale_year,last_sale_price,source,edit_date,editor,version
	# AddField(in_table, field_name, field_type, {field_precision}, {field_scale}, {field_length}, {field_alias}, {field_is_nullable}, {field_is_required}, {field_domain})

	arcpy.AddField_management(joinFN, "development_projects_id", "SHORT")
	arcpy.AddField_management(joinFN, "raw_id", "LONG")
	arcpy.AddField_management(joinFN, "building_name", "TEXT","","",200)
	arcpy.AddField_management(joinFN, "site_name", "TEXT","","",50)
	arcpy.AddField_management(joinFN, "action", "TEXT","","",10)
	arcpy.AddField_management(joinFN, "scen0", "SHORT")
	arcpy.AddField_management(joinFN, "scen1", "SHORT") ### added this line, seems like we have two scenarios
	arcpy.AddField_management(joinFN, "address", "TEXT","","",200)
	arcpy.AddField_management(joinFN, "city", "TEXT","","",50)
	arcpy.AddField_management(joinFN, "zip",  "TEXT","","",50) ## this is changed from LONG to TEXT because cs1115 file has some text formatted zipcode with "-"
	arcpy.AddField_management(joinFN, "county", "TEXT","","",50)
	arcpy.AddField_management(joinFN, "x", "FLOAT")
	arcpy.AddField_management(joinFN, "y", "FLOAT")
	arcpy.AddField_management(joinFN, "geom_id", "TEXT","","",50)
	arcpy.AddField_management(joinFN, "year_built", "SHORT")
	arcpy.AddField_management(joinFN, "duration", "SHORT")
	arcpy.AddField_management(joinFN, "building_type_id", "LONG")
	arcpy.AddField_management(joinFN, "building_type", "TEXT","","",4)
	arcpy.AddField_management(joinFN, "building_sqft", "LONG")
	arcpy.AddField_management(joinFN, "non_residential_sqft", "LONG")
	arcpy.AddField_management(joinFN, "residential_units", "SHORT")
	arcpy.AddField_management(joinFN, "unit_ave_sqft", "FLOAT")
	arcpy.AddField_management(joinFN, "tenure", "TEXT","","",5)
	arcpy.AddField_management(joinFN, "rent_type", "TEXT","","",25)
	arcpy.AddField_management(joinFN, "stories", "SHORT")
	arcpy.AddField_management(joinFN, "parking_spaces", "SHORT")
	arcpy.AddField_management(joinFN, "average_weighted_rent", "TEXT")
	arcpy.AddField_management(joinFN, "rent_ave_sqft", "FLOAT")
	arcpy.AddField_management(joinFN, "rent_ave_unit", "SHORT")
	###using date for now, as I tried to use datetime.datetime.strptime('cs_sale_date','%m/%d/%Y %I:%M:%S %p').strftime('%Y')) it didn't work
	arcpy.AddField_management(joinFN, "last_sale_year", "DATE") 
	arcpy.AddField_management(joinFN, "last_sale_price", "DOUBLE")
	arcpy.AddField_management(joinFN, "source", "TEXT","","",10)
	arcpy.AddField_management(joinFN, "edit_date", "DATE")
	arcpy.AddField_management(joinFN, "editor", "TEXT","","",50)
	arcpy.AddField_management(joinFN, "version", "SHORT")
	if not arcpy.ListFields(joinFN, "incl"):
		arcpy.AddField_management(joinFN, "incl", "SHORT")

	arcpy.CalculateField_management(joinFN, "raw_id", '!PropertyID!')
	arcpy.CalculateField_management(joinFN, "building_name", '!cs_building_name!')
	arcpy.CalculateField_management(joinFN, "site_name", '!Building_Park!')
	arcpy.CalculateField_management(joinFN, "action", "'build'")# need to quote marks here
	arcpy.CalculateField_management(joinFN, "scen0", 1) # these are committed so 1 for all scens 
	arcpy.CalculateField_management(joinFN, "address", '!Building_Address!')
	arcpy.CalculateField_management(joinFN, "city", '!cs_city!')
	arcpy.CalculateField_management(joinFN, "zip", '!cs_zip!')
	arcpy.CalculateField_management(joinFN, "county", '!County_Name!')
	arcpy.CalculateField_management(joinFN, "x", '!p_x!') 
	arcpy.CalculateField_management(joinFN, "y", '!p_y!') 
	arcpy.CalculateField_management(joinFN, "geom_id", '!p_geom_id!')
	arcpy.CalculateField_management(joinFN, "year_built", '!cs_year_built!')
	#arcpy.CalculateField_management(joinFN, "duration", )
	#arcpy.CalculateField_management(joinFN, "building_type_id", )
	arcpy.CalculateField_management(joinFN, "building_type", '!det_bldg_type!')
	arcpy.CalculateField_management(joinFN, "building_sqft", '!Rentable_Building_Area!') # how often null for res
	arcpy.CalculateField_management(joinFN, "non_residential_sqft", '!Rentable_Building_Area!') # need to zero out for res
	arcpy.CalculateField_management(joinFN, "residential_units", '!Number_Of_Units!')
	arcpy.CalculateField_management(joinFN, "unit_ave_sqft", '!Avg_Unit_SF!')
	arcpy.CalculateField_management(joinFN, "tenure", "'Rent'")
	arcpy.CalculateField_management(joinFN, "rent_type", '!cs_rent_type!') # need to clean
	arcpy.CalculateField_management(joinFN, "stories", '!Number_Of_Stories!')
	#there is a worng parking space value is one of the tables
	with arcpy.da.UpdateCursor(joinFN, ["Number_Of_Parking_Spaces","parking_spaces"]) as cursor:
    		for row in cursor:
    			if len(str((row[0]))) <= 5: ##short integer has value less than 32700
    				row[1] = row[0]
    				cursor.updateRow(row)
	#arcpy.CalculateField_management(joinFN, "parking_spaces", '!Number_Of_Parking_Spaces!')
	arcpy.CalculateField_management(joinFN, "average_weighted_rent", '!cs_average_weighted_rent!')
	#arcpy.CalculateField_management(joinFN, "rent_ave_sqft", )
	#arcpy.CalculateField_management(joinFN, "rent_ave_unit", )
	arcpy.CalculateField_management(joinFN, "last_sale_year", '!cs_last_sale_date!') #need to make into year
	arcpy.CalculateField_management(joinFN, "last_sale_price", '!cs_last_sale_price!')
	arcpy.CalculateField_management(joinFN, "source", "'cs'")
	arcpy.CalculateField_management(joinFN, "edit_date", "'Jan 2020'")
	arcpy.CalculateField_management(joinFN, "editor", "'MKR'")
	#arcpy.CalculateField_management(joinFN, "version", )

	# 3 DELETE OTHER FIELDS AND TEMP FILES
	FCfields = [f.name for f in arcpy.ListFields(joinFN)]
	#add "rent_ave_sqft", "rent_ave_unit","version", "duration", "building_type_id" if needed
	DontDeleteFields = ["OBJECTID","Shape","development_projects_id", "raw_id", "building_name", "site_name",  "action", "scen0",  "address",  "city",  "zip",  "county", "x", "y",
	"geom_id", "year_built","building_type", "building_sqft", "non_residential_sqft", "residential_units", "unit_ave_sqft", 
	"tenure", "rent_type", "stories", "parking_spaces", "average_weighted_rent", "last_sale_year", "last_sale_price", "source", "edit_date", "editor", "Shape",  "Shape_Length", "Shape_Area"]
	fields2Delete = list(set(FCfields) - set(DontDeleteFields))
	arcpy.DeleteField_management(joinFN, fields2Delete)
	
	l.append(joinFN)

### for redfin data
### create a list of feature class
rf = [rfsfr1619, rfmu1619, rfsfr1115, rfcondo1115, rfother1115]
for fc in rf:
	joinFN = 'ttt_' + arcpy.Describe(fc).name + '__p10'
	### 1 SPATIAL JOINS
	arcpy.SpatialJoin_analysis(fc, p10, joinFN)
	### 2 VARIABLE CLEANING 
	
	# rename any conflicting field names
	arcpy.AlterField_management(joinFN, "CITY", "rf_city")
	arcpy.AlterField_management(joinFN, "COUNTY", "rf_county")
	arcpy.AlterField_management(joinFN, "YEAR_BUILT", "rf_year_built")
	arcpy.AlterField_management(joinFN, "ADDRESS", "rf_address")
	arcpy.AlterField_management(joinFN, "x", "p_x") # this is from the parcel centroid
	arcpy.AlterField_management(joinFN, "y", "p_y") # this is from the parcel centroid
	arcpy.AlterField_management(joinFN, "geom_id", "p_geom_id") # this is from the parcel 
	# add fields and calc values
	# full list development_projects_id,raw_id,building_name,site_name,action,scen0,scen1,
	# address,city,zip,county,x,y,geom_id,year_built,duration,building_type_id,building_type,building_sqft,non_residential_sqft,
	# residential_units,unit_ave_sqft,tenure,rent_type,stories,parking_spaces,Average Weighted Rent,rent_ave_sqft,rent_ave_unit,
	# last_sale_year,last_sale_price,source,edit_date,editor,version
	# AddField(in_table, field_name, field_type, {field_precision}, {field_scale}, {field_length}, {field_alias}, {field_is_nullable}, {field_is_required}, {field_domain})

	arcpy.AddField_management(joinFN, "development_projects_id", "SHORT")
	arcpy.AddField_management(joinFN, "raw_id", "LONG")
	arcpy.AddField_management(joinFN, "building_name", "TEXT","","",200)
	arcpy.AddField_management(joinFN, "site_name", "TEXT","","",50)
	arcpy.AddField_management(joinFN, "action", "TEXT","","",10)
	arcpy.AddField_management(joinFN, "scen0", "SHORT")
	arcpy.AddField_management(joinFN, "scen1", "SHORT") ### added this line, seems like we have two scenarios
	arcpy.AddField_management(joinFN, "address", "TEXT","","",200)
	arcpy.AddField_management(joinFN, "city", "TEXT","","",50)
	arcpy.AddField_management(joinFN, "zip", "TEXT","","",50)
	arcpy.AddField_management(joinFN, "county", "TEXT","","",50)
	arcpy.AddField_management(joinFN, "x", "FLOAT")
	arcpy.AddField_management(joinFN, "y", "FLOAT")
	arcpy.AddField_management(joinFN, "geom_id", "TEXT","","",50)
	arcpy.AddField_management(joinFN, "year_built", "SHORT")
	arcpy.AddField_management(joinFN, "duration", "SHORT")
	arcpy.AddField_management(joinFN, "building_type_id", "LONG")
	arcpy.AddField_management(joinFN, "building_type", "TEXT","","",4)
	arcpy.AddField_management(joinFN, "building_sqft", "LONG")
	arcpy.AddField_management(joinFN, "non_residential_sqft", "LONG")
	arcpy.AddField_management(joinFN, "residential_units", "SHORT")
	arcpy.AddField_management(joinFN, "unit_ave_sqft", "FLOAT")
	arcpy.AddField_management(joinFN, "tenure", "TEXT","","",5)
	arcpy.AddField_management(joinFN, "rent_type", "TEXT","","",25)
	arcpy.AddField_management(joinFN, "stories", "SHORT")
	arcpy.AddField_management(joinFN, "parking_spaces", "SHORT")
	arcpy.AddField_management(joinFN, "average_weighted_rent", "TEXT")
	arcpy.AddField_management(joinFN, "rent_ave_sqft", "FLOAT")
	arcpy.AddField_management(joinFN, "rent_ave_unit", "SHORT")
	arcpy.AddField_management(joinFN, "last_sale_year", "DATE")
	arcpy.AddField_management(joinFN, "last_sale_price", "DOUBLE")
	arcpy.AddField_management(joinFN, "source", "TEXT","","",10)
	arcpy.AddField_management(joinFN, "edit_date", "DATE")
	arcpy.AddField_management(joinFN, "editor", "TEXT","","",50)
	arcpy.AddField_management(joinFN, "version", "SHORT")
	if not arcpy.ListFields(joinFN, "incl"):
		arcpy.AddField_management(joinFN, "incl", "SHORT")

	arcpy.CalculateField_management(joinFN, "raw_id", '!redfinid!')
	arcpy.CalculateField_management(joinFN, "action", "'build'")
	arcpy.CalculateField_management(joinFN, "scen0", 1) # these are committed so 1 for all scens 
	arcpy.CalculateField_management(joinFN, "address", '!rf_address!')
	arcpy.CalculateField_management(joinFN, "city", '!rf_city!')
	arcpy.CalculateField_management(joinFN, "county", '!rf_county!')
	arcpy.CalculateField_management(joinFN, "x", '!p_x!') 
	arcpy.CalculateField_management(joinFN, "y", '!p_y!') 
	arcpy.CalculateField_management(joinFN, "geom_id", '!p_geom_id!')
	arcpy.CalculateField_management(joinFN, "year_built", '!rf_year_built!')
	#arcpy.CalculateField_management(joinFN, "building_type", '!det_bldg_type!') #building type is not defined for redfin data
	arcpy.CalculateField_management(joinFN, "building_sqft", '!SQFT!') # how often null for res
	arcpy.CalculateField_management(joinFN, "non_residential_sqft", 0) # seems redfin data are all residential
	arcpy.CalculateField_management(joinFN, "residential_units", '!UNITS!')
	###ideally, everything could be done using cursor since it is much faster to run
	with arcpy.da.UpdateCursor(joinFN, ["SQFT", "UNITS", "unit_ave_sqft"]) as cursor:
    		for row in cursor:
        		row[2] = row[0] / row[1] 
        		cursor.updateRow(row)
	arcpy.CalculateField_management(joinFN, "tenure", "'Sale'") #is redfin data rental?
	arcpy.CalculateField_management(joinFN, "last_sale_year", '!SOLD_DATE!') #need to make into year
	arcpy.CalculateField_management(joinFN, "last_sale_price", '!PRICE!')
	arcpy.CalculateField_management(joinFN, "source", "'rf'")
	arcpy.CalculateField_management(joinFN, "edit_date", "'Jan 2020'")
	arcpy.CalculateField_management(joinFN, "editor", "'MKR'")
	

	# 3 DELETE OTHER FIELDS AND TEMP FILES
	FCfields = [f.name for f in arcpy.ListFields(joinFN)]
	#add "rent_ave_sqft", "rent_ave_unit","version", "duration", "building_type_id" if needed
	DontDeleteFields = ["OBJECTID","Shape","development_projects_id", "raw_id", "building_name", "site_name",  "action", "scen0",  "address",  "city",  "zip",  "county", "x", "y",
	"geom_id", "year_built","building_type", "building_sqft", "non_residential_sqft", "residential_units", "unit_ave_sqft", 
	"tenure", "rent_type", "stories", "parking_spaces", "average_weighted_rent", "last_sale_year", "last_sale_price", "source", "edit_date", "editor", "Shape_Length", "Shape_Area"]
	fields2Delete = list(set(FCfields) - set(DontDeleteFields))
	arcpy.DeleteField_management(joinFN, fields2Delete)

	l.append(joinFN)

### for BASIS pipeline data
joinFN = 'ttt_basispp_p10'
### 1 SPATIAL JOINS
arcpy.SpatialJoin_analysis(basis_pipeline, p10, joinFN)
### 2 VARIABLE CLEANING 

# rename any conflicting field names
arcpy.AlterField_management(joinFN, "county", "b_county")
arcpy.AlterField_management(joinFN, "raw_id", "b_id")
arcpy.AlterField_management(joinFN, "year_built", "b_year_built")
arcpy.AlterField_management(joinFN, "zip", "b_zip")
arcpy.AlterField_management(joinFN, "stories", "b_stories")
arcpy.AlterField_management(joinFN, "x", "p_x") # this is from the parcel centroid
arcpy.AlterField_management(joinFN, "y", "p_y") # this is from the parcel centroid
arcpy.AlterField_management(joinFN, "geom_id", "p_geom_id") # this is from the parcel 
# add fields and calc values
# full list development_projects_id,raw_id,building_name,site_name,action,scen0,scen1,
# address,city,zip,county,x,y,geom_id,year_built,duration,building_type_id,building_type,building_sqft,non_residential_sqft,
# residential_units,unit_ave_sqft,tenure,rent_type,stories,parking_spaces,Average Weighted Rent,rent_ave_sqft,rent_ave_unit,
# last_sale_year,last_sale_price,source,edit_date,editor,version
# AddField(in_table, field_name, field_type, {field_precision}, {field_scale}, {field_length}, {field_alias}, {field_is_nullable}, {field_is_required}, {field_domain})

arcpy.AddField_management(joinFN, "development_projects_id", "SHORT")
arcpy.AddField_management(joinFN, "raw_id", "LONG")
arcpy.AddField_management(joinFN, "building_name", "TEXT","","",200)
arcpy.AddField_management(joinFN, "site_name", "TEXT","","",50)
arcpy.AddField_management(joinFN, "action", "TEXT","","",10)
arcpy.AddField_management(joinFN, "scen0", "SHORT")
arcpy.AddField_management(joinFN, "scen1", "SHORT") ### added this line, seems like we have two scenarios
arcpy.AddField_management(joinFN, "address", "TEXT","","",200)
arcpy.AddField_management(joinFN, "city", "TEXT","","",50)
arcpy.AddField_management(joinFN, "zip", "TEXT","","",50)
arcpy.AddField_management(joinFN, "county", "TEXT","","",50)
arcpy.AddField_management(joinFN, "x", "FLOAT")
arcpy.AddField_management(joinFN, "y", "FLOAT")
arcpy.AddField_management(joinFN, "geom_id", "TEXT","","",50)
arcpy.AddField_management(joinFN, "year_built", "SHORT")
arcpy.AddField_management(joinFN, "duration", "SHORT")
arcpy.AddField_management(joinFN, "building_type_id", "LONG")
arcpy.AddField_management(joinFN, "building_type", "TEXT","","",4)
arcpy.AddField_management(joinFN, "building_sqft", "LONG")
arcpy.AddField_management(joinFN, "non_residential_sqft", "LONG")
arcpy.AddField_management(joinFN, "residential_units", "SHORT")
arcpy.AddField_management(joinFN, "unit_ave_sqft", "FLOAT")
arcpy.AddField_management(joinFN, "tenure", "TEXT","","",5)
arcpy.AddField_management(joinFN, "rent_type", "TEXT","","",25)
arcpy.AddField_management(joinFN, "stories", "SHORT")
arcpy.AddField_management(joinFN, "parking_spaces", "SHORT")
arcpy.AddField_management(joinFN, "average_weighted_rent", "TEXT")
arcpy.AddField_management(joinFN, "rent_ave_sqft", "FLOAT")
arcpy.AddField_management(joinFN, "rent_ave_unit", "SHORT")
###using date for now, as I tried to use datetime.datetime.strptime('cs_sale_date','%m/%d/%Y %I:%M:%S %p').strftime('%Y')) it didn't work
arcpy.AddField_management(joinFN, "last_sale_year", "DATE") 
arcpy.AddField_management(joinFN, "last_sale_price", "DOUBLE")
arcpy.AddField_management(joinFN, "source", "TEXT","","",10)
arcpy.AddField_management(joinFN, "edit_date", "DATE")
if not arcpy.ListFields(joinFN, "incl"):
	arcpy.AddField_management(joinFN, "incl", "SHORT")

arcpy.CalculateField_management(joinFN, "building_name", '!project_na!')
arcpy.CalculateField_management(joinFN, "action", "'build'")# need to quote marks here
arcpy.CalculateField_management(joinFN, "scen0", 1) # these are committed so 1 for all scens 
arcpy.CalculateField_management(joinFN, "address", '!street_add!')
arcpy.CalculateField_management(joinFN, "city", '!mailing_ci!')
##arcpy.CalculateField_management(joinFN, "zip", '!b_zip!') ##not sure how to convert text to long data type
arcpy.CalculateField_management(joinFN, "county", '!b_county!')
arcpy.CalculateField_management(joinFN, "x", '!p_x!') 
arcpy.CalculateField_management(joinFN, "y", '!p_y!') 
arcpy.CalculateField_management(joinFN, "geom_id", '!p_geom_id!')
arcpy.CalculateField_management(joinFN, "year_built", '!b_year_built!')
##arcpy.CalculateField_management(joinFN, "building_type", '!building_t!') ##this need to translate to two-letter type code
arcpy.CalculateField_management(joinFN, "building_sqft", '!building_s!') # how often null for res
arcpy.CalculateField_management(joinFN, "non_residential_sqft", '!non_reside!') # need to zero out for res
arcpy.CalculateField_management(joinFN, "residential_units", '!residentia!')
arcpy.CalculateField_management(joinFN, "tenure", "'Rent'") ##what is tenure
arcpy.CalculateField_management(joinFN, "stories", '!b_stories!')
arcpy.CalculateField_management(joinFN, "source", "'basis'")
arcpy.CalculateField_management(joinFN, "edit_date", "'Jan 2020'")
#arcpy.CalculateField_management(joinFN, "version", )

# 3 DELETE OTHER FIELDS AND TEMP FILES
FCfields = [f.name for f in arcpy.ListFields(joinFN)]
#add "rent_ave_sqft", "rent_ave_unit","version", "duration", "building_type_id" if needed
DontDeleteFields = ["OBJECTID","Shape","development_projects_id", "raw_id", "building_name", "site_name",  "action", "scen0",  "address",  "city",  "zip",  "county", "x", "y",
"geom_id", "year_built","building_type", "building_sqft", "non_residential_sqft", "residential_units", "unit_ave_sqft", 
"tenure", "rent_type", "stories", "parking_spaces", "average_weighted_rent", "last_sale_year", "last_sale_price", "source", "edit_date", "editor", "Shape",  "Shape_Length", "Shape_Area"]
fields2Delete = list(set(FCfields) - set(DontDeleteFields))
arcpy.DeleteField_management(joinFN, fields2Delete)

l.append(joinFN)

#Manual
joinFN = 'ttt_manual_p10'
### 1 SPATIAL JOINS
arcpy.SpatialJoin_analysis(manual_dp, p10, joinFN)
# rename any conflicting field names

arcpy.AlterField_management(joinFN, "building_name", "m_building_name")
arcpy.AlterField_management(joinFN, "year_built", "m_year_built")
arcpy.AlterField_management(joinFN, "last_sale_price", "m_last_sale_price")
arcpy.AlterField_management(joinFN, "last_sale_year", "m_sale_date")
arcpy.AlterField_management(joinFN, "stories", "m_stories")
arcpy.AlterField_management(joinFN, "residential_units", "m_residential_units")
arcpy.AlterField_management(joinFN, "unit_ave_sqft", "m_unit_ave_sqft")
arcpy.AlterField_management(joinFN, "zip", "m_zips")
arcpy.AlterField_management(joinFN, "Average_Weighted_Rent", "m_average_weighted_rent")
arcpy.AlterField_management(joinFN, "x", "p_x") # this is from the parcel centroid
arcpy.AlterField_management(joinFN, "y", "p_y") # this is from the parcel centroid
arcpy.AlterField_management(joinFN, "geom_id", "p_geom_id") # this is from the parcel 
# add fields and calc values
# full list development_projects_id,raw_id,building_name,site_name,action,scen0,scen1,
# address,city,zip,county,x,y,geom_id,year_built,duration,building_type_id,building_type,building_sqft,non_residential_sqft,
# residential_units,unit_ave_sqft,tenure,rent_type,stories,parking_spaces,Average Weighted Rent,rent_ave_sqft,rent_ave_unit,
# last_sale_year,last_sale_price,source,edit_date,editor,version
# AddField(in_table, field_name, field_type, {field_precision}, {field_scale}, {field_length}, {field_alias}, {field_is_nullable}, {field_is_required}, {field_domain})

arcpy.AddField_management(joinFN, "development_projects_id", "SHORT")
arcpy.AddField_management(joinFN, "raw_id", "LONG")
arcpy.AddField_management(joinFN, "building_name", "TEXT","","",200)
arcpy.AddField_management(joinFN, "scen0", "SHORT")
arcpy.AddField_management(joinFN, "scen1", "SHORT") ### added this line, seems like we have two scenarios
arcpy.AddField_management(joinFN, "zip", "TEXT","","",50)
arcpy.AddField_management(joinFN, "x", "FLOAT")
arcpy.AddField_management(joinFN, "y", "FLOAT")
arcpy.AddField_management(joinFN, "geom_id", "TEXT","","",50)
arcpy.AddField_management(joinFN, "year_built", "SHORT")
arcpy.AddField_management(joinFN, "residential_units", "SHORT")
arcpy.AddField_management(joinFN, "unit_ave_sqft", "FLOAT")
arcpy.AddField_management(joinFN, "stories", "SHORT")
arcpy.AddField_management(joinFN, "average_weighted_rent", "TEXT")
arcpy.AddField_management(joinFN, "rent_ave_sqft", "FLOAT")
arcpy.AddField_management(joinFN, "rent_ave_unit", "SHORT")
###using date for now, as I tried to use datetime.datetime.strptime('cs_sale_date','%m/%d/%Y %I:%M:%S %p').strftime('%Y')) it didn't work
arcpy.AddField_management(joinFN, "last_sale_year", "DATE") 
arcpy.AddField_management(joinFN, "last_sale_price", "DOUBLE")
arcpy.AddField_management(joinFN, "source", "TEXT","","",10)
arcpy.AddField_management(joinFN, "edit_date", "DATE")
arcpy.AddField_management(joinFN, "editor", "TEXT","","",50)
arcpy.AddField_management(joinFN, "version", "SHORT")

arcpy.CalculateField_management(joinFN, "raw_id", '!manual_dp_id!')
arcpy.CalculateField_management(joinFN, "building_name", '!m_building_name!')
arcpy.CalculateField_management(joinFN, "scen0", 1) # these are committed so 1 for all scens 
#not sure how to change zip field type
#arcpy.CalculateField_management(joinFN, "zip", '!m_zip!')
arcpy.CalculateField_management(joinFN, "x", '!p_x!') 
arcpy.CalculateField_management(joinFN, "y", '!p_y!') 
arcpy.CalculateField_management(joinFN, "geom_id", '!p_geom_id!')
arcpy.CalculateField_management(joinFN, "year_built", '!m_year_built!')
#arcpy.CalculateField_management(joinFN, "duration", )
arcpy.CalculateField_management(joinFN, "residential_units", '!m_residential_units!')
arcpy.CalculateField_management(joinFN, "unit_ave_sqft", '!m_unit_ave_sqft!')
arcpy.CalculateField_management(joinFN, "stories", '!m_stories!')
arcpy.CalculateField_management(joinFN, "average_weighted_rent", '!m_average_weighted_rent!')
#arcpy.CalculateField_management(joinFN, "rent_ave_sqft", )
#arcpy.CalculateField_management(joinFN, "rent_ave_unit", )
arcpy.CalculateField_management(joinFN, "last_sale_year", '!m_sale_date!') #need to make into year
arcpy.CalculateField_management(joinFN, "last_sale_price", '!m_last_sale_price!')
arcpy.CalculateField_management(joinFN, "source", "'manual'")
arcpy.CalculateField_management(joinFN, "edit_date", "'Jan 2020'")
arcpy.CalculateField_management(joinFN, "editor", "'MKR'")
#arcpy.CalculateField_management(joinFN, "version", )

FCfields = [f.name for f in arcpy.ListFields(joinFN)]
#add "rent_ave_sqft", "rent_ave_unit","version", "duration", "building_type_id" if needed
DontDeleteFields = ["OBJECTID","Shape","development_projects_id", "raw_id", "building_name", "site_name",  "action", "scen0",  "address",  "city",  "zip",  "county", "x", "y",
"geom_id", "year_built","building_type", "building_sqft", "non_residential_sqft", "residential_units", "unit_ave_sqft", 
"tenure", "rent_type", "stories", "parking_spaces", "average_weighted_rent", "last_sale_year", "last_sale_price", "source", "edit_date", "editor", "Shape",  "Shape_Length", "Shape_Area"]
fields2Delete = list(set(FCfields) - set(DontDeleteFields))
arcpy.DeleteField_management(joinFN, fields2Delete)

l.append(joinFN)

#opportunity sites
joinFN = 'ttt_opp_p10'

arcpy.SpatialJoin_analysis(opp_sites, p10, joinFN)

arcpy.AlterField_management(joinFN, "year_built", "o_year_built")
arcpy.AlterField_management(joinFN, "last_sale_price", "o_last_sale_price")
arcpy.AlterField_management(joinFN, "last_sale_year", "o_sale_date")
arcpy.AlterField_management(joinFN, "stories", "o_stories")
arcpy.AlterField_management(joinFN, "scen0", "o_scen0")
arcpy.AlterField_management(joinFN, "duration", "o_duration")
arcpy.AlterField_management(joinFN, "parking_spaces", "o_parking_spaces")
arcpy.AlterField_management(joinFN, "residential_units", "o_residential_units")
arcpy.AlterField_management(joinFN, "unit_ave_sqft", "o_unit_ave_sqft")
arcpy.AlterField_management(joinFN, "rent_ave_sqft", "o_rent_ave_sqft")
arcpy.AlterField_management(joinFN, "rent_ave_unit", "o_rent_ave_unit")
arcpy.AlterField_management(joinFN, "zip", "o_zips")
arcpy.AlterField_management(joinFN, "Average_Weighted_Rent", "average_weighted_rent")
arcpy.AlterField_management(joinFN, "x", "p_x") # this is from the parcel centroid
arcpy.AlterField_management(joinFN, "y", "p_y") # this is from the parcel centroid
arcpy.AlterField_management(joinFN, "geom_id", "p_geom_id") 

arcpy.AddField_management(joinFN, "development_projects_id", "SHORT")
arcpy.AddField_management(joinFN, "raw_id", "LONG")
arcpy.AddField_management(joinFN, "scen0", "SHORT")
#arcpy.AddField_management(joinFN, "scen1", "SHORT") ### added this line, seems like we have two scenarios
arcpy.AddField_management(joinFN, "zip", "TEXT","","",50)
arcpy.AddField_management(joinFN, "x", "FLOAT")
arcpy.AddField_management(joinFN, "y", "FLOAT")
arcpy.AddField_management(joinFN, "geom_id", "TEXT","","",50)
arcpy.AddField_management(joinFN, "year_built", "SHORT")
arcpy.AddField_management(joinFN, "duration", "SHORT")
arcpy.AddField_management(joinFN, "residential_units", "SHORT")
arcpy.AddField_management(joinFN, "unit_ave_sqft", "FLOAT")
arcpy.AddField_management(joinFN, "stories", "SHORT")
arcpy.AddField_management(joinFN, "parking_spaces", "SHORT")
arcpy.AddField_management(joinFN, "rent_ave_sqft", "FLOAT")
arcpy.AddField_management(joinFN, "rent_ave_unit", "SHORT")
###using date for now, as I tried to use datetime.datetime.strptime('cs_sale_date','%m/%d/%Y %I:%M:%S %p').strftime('%Y')) it didn't work
arcpy.AddField_management(joinFN, "last_sale_year", "DATE") 
arcpy.AddField_management(joinFN, "last_sale_price", "DOUBLE")
arcpy.AddField_management(joinFN, "edit_date", "DATE")
arcpy.AddField_management(joinFN, "editor", "TEXT","","",50)
arcpy.AddField_management(joinFN, "version", "SHORT")
arcpy.AddField_management(joinFN, "incl", "SHORT")

arcpy.CalculateField_management(joinFN, "scen0", 0) # these are committed so 1 for all scens 
#arcpy.CalculateField_management(joinFN, "zip", '!o_zip!')
arcpy.CalculateField_management(joinFN, "x", '!p_x!') 
arcpy.CalculateField_management(joinFN, "y", '!p_y!') 
arcpy.CalculateField_management(joinFN, "geom_id", '!p_geom_id!')
arcpy.CalculateField_management(joinFN, "year_built", '!o_year_built!')
arcpy.CalculateField_management(joinFN, "residential_units", '!o_residential_units!')
arcpy.CalculateField_management(joinFN, "unit_ave_sqft", '!o_unit_ave_sqft!')
arcpy.CalculateField_management(joinFN, "stories", '!o_stories!')
arcpy.CalculateField_management(joinFN, "rent_ave_sqft", "!o_rent_ave_sqft!" )
arcpy.CalculateField_management(joinFN, "rent_ave_unit", "!o_rent_ave_unit!")
arcpy.CalculateField_management(joinFN, "last_sale_year", '!o_sale_date!') #need to make into year
arcpy.CalculateField_management(joinFN, "last_sale_price", '!o_last_sale_price!')
arcpy.CalculateField_management(joinFN, "source", "'opp'")
arcpy.CalculateField_management(joinFN, "edit_date", "'Jan 2020'")
arcpy.CalculateField_management(joinFN, "editor", "'MKR'")
arcpy.CalculateField_management(joinFN, "incl", 0)

FCfields = [f.name for f in arcpy.ListFields(joinFN)]
#add "rent_ave_sqft", "rent_ave_unit","version", "duration", "building_type_id" if needed
DontDeleteFields = ["OBJECTID","Shape","development_projects_id", "raw_id", "building_name", "site_name",  "action", "scen0",  "address",  "city",  "zip",  "county", "x", "y",
"geom_id", "year_built","building_type", "building_sqft", "non_residential_sqft", "residential_units", "unit_ave_sqft", 
"tenure", "rent_type", "stories", "parking_spaces", "average_weighted_rent", "last_sale_year", "last_sale_price", "source", "edit_date", "editor", "Shape",  "Shape_Length", "Shape_Area"]
fields2Delete = list(set(FCfields) - set(DontDeleteFields))
arcpy.DeleteField_management(joinFN, fields2Delete)


# 4 MERGE ALL INCL=1 POINTS INTO A SINGLE SHP FILE CALLED PIPELINE
#all non opp sites should be in the list l
arcpy.Merge_management(l, 'pipeline')

# 5 MERGE OPPSITES SHP WITH PIPELINE TO GET DEVELOPMENT PROJECTS
# NOTE THAT OPPSITES HAS SCEN SET IN GIS FILE

arcpy.Merge_management(['pipeline','ttt_opp_p10'], 'development_projects')

# delete temporary join files
# arcpy.Delete_management(rfsfr1619p10JOIN)
for fc in 'development_projects':
  if arcpy.Exists(fc):
    arcpy.Delete_management(fc)

# 6 DIAGNOSTICS




# 7 REMOVE DUPLICATES
# manually: go ahead and recode a 1 to 0 in the GIS file to not use a record 

# automatically switching incl to 0 or another code using hierarchy
# keep multiple points on same parcel from WITHIN the same dataset but don't add additional from lower datasets
# manual_dp is best, then cs, then BASIS, then redfin SFD, then all other redfin, then oppsites 



# 8 BUILDINGS TO DEMOLISH

# list of all geomids that build then subtract out manual list
# auto calc demolish
# export csv




#arcpy.CalculateField_management(ALL, "development_projects_id", ) #create


# 9 EXPORT CSV W BUILDINGS TO BUILD AND DEMOLISH


