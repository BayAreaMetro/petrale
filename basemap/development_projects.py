# coding: utf-8
#
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
#
# outputs:
#  file geodataase, devproj_[datestr].gdb, including
#    1. pipeline feature class, includes real build events of what has been built since 2011
#    2. development_projects feature class, includes pipeline plus opportunity sites, which
#       are scenario-specific
#  flat files:
#    3. csv version of pipeline
#    4. csv version of development_projects
#    5. log file
#
# Since this script relies on arcpy, for a windows machine with ArcGIS Pro installed,
# set PATH=C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3

import os, sys, time
import arcpy
import logging
from arcgis.gis import GIS
from arcgis.features import FeatureLayer
import pandas as pd

NOW = time.strftime("%Y_%m%d_%H%M")

# arcpy workspace and log file setup
# note: this runs a lot better if these directories are a local/fast disk
# Using a box drive or even a network drive tends to result in arcpy exceptions
if os.getenv("USERNAME")=="lzorn":
	WORKING_DIR		 = "C:\\Users\\lzorn\\Documents\\UrbanSim smelt\\2020 07 16"
	LOG_FILE		    = os.path.join(WORKING_DIR,"devproj_{}.log".format(NOW))
	SMELT_GDB		   = os.path.join(WORKING_DIR,"smelt.gdb")
	WORKSPACE_GDB       = "workspace_{}.GDB".format(NOW) # scratch
elif os.getenv("USERNAME")=="MTCPB":
	WORKING_DIR		 = "C:\\Users\\MTCPB\\Documents\\ArcGIS\\Projects\\Pipeline\\2020 07 16"
	LOG_FILE		    = os.path.join(WORKING_DIR,"devproj_{}.log".format(NOW))
	SMELT_GDB		   = "C:\\Users\\MTCPB\\Documents\\ArcGIS\\Projects\\Pipeline\\2020 07 16\\smelt.gdb"
	WORKSPACE_GDB       = "workspace_{}.GDB".format(NOW) # scratch
else:
	WORKING_DIR		 = "E:\\baydata"
	LOG_FILE		    = os.path.join(WORKING_DIR,"devproj_{}.log".format(NOW))
	SMELT_GDB		   = os.path.join(WORKING_DIR,"smelt.gdb")
	WORKSPACE_GDB       = "workspace_{}.GDB".format(NOW) # scratch

###BL: I am organizing the process by data sources, so that it is easy to replicate the process

### First need to know what's in the geodatabase, for now I couldn't find a way to list all datasets, feature, and tables using a code.
### but afte I made the fold connection, it shows that smelt.gdb contains 2 tables, 3 feature classes. and 2 feature datasets - built and dp1620

# SET VARS
# input
p10_pba50   = os.path.join(SMELT_GDB, "p10_pba50") # 2010 parcels, polygon feature class

### costar data
cs1620      = os.path.join(SMELT_GDB, "cs1620") # costar data  2016-2020, point feature class
cs1115      = os.path.join(SMELT_GDB, "cs1115") # costar data  2011-2015, point feature class

### redfin data
rfsfr1619   = os.path.join(SMELT_GDB,"rf19_sfr1619"       ) # redfin SFD data 2016-2019
rfmu1619    = os.path.join(SMELT_GDB,"rf19_multiunit1619" ) # redin MFD data 2016-2019
rfsfr1115   = os.path.join(SMELT_GDB,"rf19_sfr1115"       ) # redfin SFD data 2011-2015
rfcondo1115 = os.path.join(SMELT_GDB,"rf19_condounits1115") # redfin condo data 2011-2015
rfother1115 = os.path.join(SMELT_GDB,"rf19_othertypes1115") # redfin other data 2011-2015

### BASIS pipleline data
basis_pipeline = os.path.join(SMELT_GDB, "basis_pipeline_20200228")

### basis parcel/building new data
basis_pb_new = os.path.join(SMELT_GDB, "basis_pb_new_20200312")


MTC_ONLINE_MANUAL_URL = 'https://arcgis.ad.mtc.ca.gov/server/rest/services/Hosted/manual_dp_20200716/FeatureServer/0?token=5qV1qgKLXC7Uoum0N1sSTZSV2-eF9SG0PhR682PbAHyrmoc69codzAagWRYOM9Xypcu6KW61Fh6o_gxarcGObsAf07pS0cbvlK-VgakqgY8-DCShwsQ0v1G_O9JQdMPxYfkR7kr6SfjX-00qoRqCF5KOdLiPsgpzbw6gcm6AWWeGZ_d1Hh2smCJV6ShoeyVo1pKLEki3s0r8gZbhXAn6yPAIsWyoTblgsTYRIZsp2Pk.'

MTC_ONLINE_OPPSITE_URL = 'https://arcgis.ad.mtc.ca.gov/server/rest/services/Hosted/opportunity_sites_20201026/FeatureServer/0?token=Pl_DJ4-veoG357sbtVCk4Ui-0dM681BNSTxnQp6k-Dxg_2LjX7NHbDocTGJfXal8DKu35WkzKXr69ker1T5jtgRp4YF0rhNepcTDvuhMNaaDR6iBlJmWJAy86Io2qVJHorl71ZnkT5GfJf2EXblhTMiCNz4AOyA5PtBJKDjJPvXmuqffhgo7R3eaC4G_NRJDDdE7rg2MugcenXCEUw8YtBWYx1G36DreyKq1qXF5mx8.'

MTC_ONLINE_PUBLAND_URL = 'https://arcgis.ad.mtc.ca.gov/server/rest/services/Hosted/H8_AH_Public_Sites_v2/FeatureServer/1?token=AqWg4P13gnHhs3eow-l_DRj3B87GX-mNF0V4vxEw4GCIhPjB6GzEx0SDEod_Z-YQFEdsZod1OVHaiar89Gz5VQClSE67R-OOXjCxIlT4KdXRHWD4jugiMLQA5feu1w3GXrzT4Jy4NQjkxe8x_JAIUpav2KP-ARduE8Pbm0IlA2vLHiInuzGV6gj6quBL6gBdW7ODQ29dznZOaQrxfcb7livpfcUemSnGB7qNknUuxuc.'

manual_sites = arcpy.MakeFeatureLayer_management(MTC_ONLINE_MANUAL_URL,'manual_sites')

opportunity_sites = arcpy.MakeFeatureLayer_management(MTC_ONLINE_OPPSITE_URL,'opportunity_sites',)

publicland_sites = arcpy.MakeFeatureLayer_management(MTC_ONLINE_PUBLAND_URL,'publicland_sites',)

arcpy.env.workspace = SMELT_GDB
arcpy.env.overwriteOutput = True

if arcpy.Exists('manual_dp'):
	arcpy.Delete_management('manual_dp')
if arcpy.Exists('opportunity_dp'):
	arcpy.Delete_management('opportunity_dp')
if arcpy.Exists('pubsites_dp'):
	arcpy.Delete_management('pubsites_dp')
arcpy.FeatureClassToFeatureClass_conversion(manual_sites, SMELT_GDB,'manual_dp')
arcpy.FeatureClassToFeatureClass_conversion(opportunity_sites, SMELT_GDB,'opportunity_dp')
arcpy.FeatureClassToFeatureClass_conversion(publicland_sites, SMELT_GDB,'pubsites_dp')

### manually maintained pipeline data
manual_dp   = os.path.join(SMELT_GDB, "manual_dp")


# opportunity sites that keep their scen status from gis file
opp_sites   = os.path.join(SMELT_GDB, "opportunity_dp")

# public land sites that keep their scen status from gis file
pub_sites   = os.path.join(SMELT_GDB, "pubsites_dp")


#set up a process to make sure all incl = 1 records are in the results (also need to make sure that the feature class has column "incl")
def countRow (fc):
	if  arcpy.ListFields(fc, "incl"):
		try:
			arcpy.Delete_management("fcInc1")
		except:
			pass
		arcpy.MakeTableView_management(fc,"fcInc1","incl = 1")
		count = arcpy.GetCount_management("fcInc1")
		result = int(count[0])
		return result
	else:
		print("incl is not a variable in this file")


#this is to reorder file before export so that it could be used for urbansim directly
#source: http://joshwerts.com/blog/2014/04/17/arcpy-reorder-fields/
def reorder_fields(table, out_table, field_order, add_missing=True):
    """
    Reorders fields in input featureclass/table
    :table:         input table (fc, table, layer, etc)
    :out_table:     output table (fc, table, layer, etc)
    :field_order:   order of fields (objectid, shape not necessary)
    :add_missing:   add missing fields to end if True (leave out if False)
    -> path to output table
    """
    existing_fields = arcpy.ListFields(table)
    existing_field_names = [field.name for field in existing_fields]

    existing_mapping = arcpy.FieldMappings()
    existing_mapping.addTable(table)

    new_mapping = arcpy.FieldMappings()

    def add_mapping(field_name):
        mapping_index = existing_mapping.findFieldMapIndex(field_name)

        # required fields (OBJECTID, etc) will not be in existing mappings
        # they are added automatically
        if mapping_index != -1:
            field_map = existing_mapping.fieldMappings[mapping_index]
            new_mapping.addFieldMap(field_map)

    # add user fields from field_order
    for field_name in field_order:
        if field_name not in existing_field_names:
            raise Exception("Field: {0} not in {1}".format(field_name, table))

        add_mapping(field_name)

    # add missing fields at end
    if add_missing:
        missing_fields = [f for f in existing_field_names if f not in field_order]
        for field_name in missing_fields:
            add_mapping(field_name)

    # use merge with single input just to use new field_mappings
    arcpy.Merge_management(table, out_table, new_mapping)
    return out_table

# output
# pipeline shp
# development_projects shp
# development_projects csv
# demolish csv

if __name__ == '__main__':
	
	# create logger
	logger = logging.getLogger(__name__)
	logger.setLevel('DEBUG')

	# console handler
	ch = logging.StreamHandler()
	ch.setLevel('INFO')
	ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p'))
	logger.addHandler(ch)
	# file handler
	fh = logging.FileHandler(LOG_FILE, mode='w')
	fh.setLevel('DEBUG')
	fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p'))
	logger.addHandler(fh)


	logger.info("WORKING_DIR   = {}".format(WORKING_DIR))
	logger.info("WORKSPACE_GDB = {}".format(WORKSPACE_GDB))
	logger.info("SMELT_GDB     = {}".format(SMELT_GDB))

	# list info about SMELT_GDB
	arcpy.env.workspace = SMELT_GDB
	logger.info("workspace: {}".format(arcpy.env.workspace))
	for dataset in arcpy.ListDatasets():
		logger.info("  dataset: {}".format(dataset))
		logger.info("    feature classes: {} ".format(arcpy.ListFeatureClasses(feature_dataset=dataset)))
	
	logger.info("  feature classes: {} ".format(arcpy.ListFeatureClasses()))
	logger.info("  tables: {} ".format(arcpy.ListTables()))

	arcpy.CreateFileGDB_management(WORKING_DIR, WORKSPACE_GDB)
	arcpy.env.workspace = os.path.join(WORKING_DIR, WORKSPACE_GDB)

	#get an empty list to add feature class to so that they can be merged in the end all together
	dev_projects_temp_layers = []

	#create another empty geom_id list to use for checking and removing duplicates, the idea is that, once a dataset has been cleaned
	#before it gets added to the development projects temp layers, it needs to check against the geom_ids that are already in this list
	#not sure how cumbersome this approach would be
	geoList = []

	#count geom_id is null
	gidnull = 'gidnull'

	countOne = countRow(manual_dp)
	logger.info("Feature Class {} has {} records with incl = 1".format(manual_dp, countOne))
	joinFN = 'ttt_' + arcpy.Describe(manual_dp).name + '_p10_pba50'
	dev_projects_temp_layers.append(joinFN)
	#based on Mike's ranking, start with manual dp list
	try:
		count = arcpy.GetCount_management(joinFN)
		if int(count[0]) > 100:
			logger.info("Found layer {} with {} rows -- skipping creation".format(joinFN, int(count[0])))

	except:
		# go ahead and create it
		### 1 SPATIAL JOINS
		logger.info("Creating layer {} by spatial joining manual pipeline data ({}) and parcels ({})".format(joinFN, manual_dp, p10_pba50))
		arcpy.SpatialJoin_analysis(manual_dp, p10_pba50, joinFN)
		# rename any conflicting field names
		
		arcpy.AlterField_management(joinFN, "building_name", "m_building_name")
		arcpy.AlterField_management(joinFN, "site_name", "m_site_name")
		arcpy.AlterField_management(joinFN, "year_built", "m_year_built")
		arcpy.AlterField_management(joinFN, "parcel_id", "m_parcel_id")
		arcpy.AlterField_management(joinFN, "last_sale_price", "m_last_sale_price")
		arcpy.AlterField_management(joinFN, "last_sale_year", "m_sale_date")
		arcpy.AlterField_management(joinFN, "stories", "m_stories")
		arcpy.AlterField_management(joinFN, "residential_units", "m_residential_units")
		arcpy.AlterField_management(joinFN, "unit_ave_sqft", "m_unit_ave_sqft")
		arcpy.AlterField_management(joinFN, "zip", "m_zips")
		arcpy.AlterField_management(joinFN, "Average_Weighted_Rent", "m_average_weighted_rent")
		arcpy.AlterField_management(joinFN, "x", "p_x") 
		arcpy.AlterField_management(joinFN, "y", "p_y") 
		arcpy.AlterField_management(joinFN, "geom_id", "p_geom_id")#this is from the parcel file
					# add fields and calc values
		# full list development_projects_id,raw_id,building_name,site_name,action,scen0,scen1,
		# address,city,zip,county,x,y,geom_id,year_built,duration,building_type_id,building_type,building_sqft,non_residential_sqft,
		# residential_units,unit_ave_sqft,tenure,rent_type,stories,parking_spaces,Average Weighted Rent,rent_ave_sqft,rent_ave_unit,
		# last_sale_year,last_sale_price,source,edit_date,editor,version
		# AddField(in_table, field_name, field_type, {field_precision}, {field_scale}, {field_length}, {field_alias}, {field_is_nullable}, {field_is_required}, {field_domain})
		arcpy.AddField_management(joinFN, "development_projects_id", "LONG")
		arcpy.AddField_management(joinFN, "raw_id", "LONG")
		arcpy.AddField_management(joinFN, "building_name", "TEXT","","",200)
		arcpy.AddField_management(joinFN, "site_name", "TEXT","","",200)
		arcpy.AddField_management(joinFN, "PARCEL_ID", "LONG")
		arcpy.AddField_management(joinFN, "scen0", "SHORT")
		arcpy.AddField_management(joinFN, "scen1", "SHORT")
		arcpy.AddField_management(joinFN, "scen2", "SHORT")
		arcpy.AddField_management(joinFN, "scen3", "SHORT")
		arcpy.AddField_management(joinFN, "scen4", "SHORT")
		arcpy.AddField_management(joinFN, "scen5", "SHORT")
		arcpy.AddField_management(joinFN, "scen6", "SHORT")
		arcpy.AddField_management(joinFN, "scen7", "SHORT")
		arcpy.AddField_management(joinFN, "scen10", "SHORT")
		arcpy.AddField_management(joinFN, "scen11", "SHORT")
		arcpy.AddField_management(joinFN, "scen12", "SHORT")
		arcpy.AddField_management(joinFN, "scen15", "SHORT")
		arcpy.AddField_management(joinFN, "scen20", "SHORT")
		arcpy.AddField_management(joinFN, "scen21", "SHORT")
		arcpy.AddField_management(joinFN, "scen22", "SHORT")
		arcpy.AddField_management(joinFN, "scen23", "SHORT")
		arcpy.AddField_management(joinFN, "scen24", "SHORT")
		arcpy.AddField_management(joinFN, "scen25", "SHORT") 
		arcpy.AddField_management(joinFN, "zip", "TEXT","","",50)
		arcpy.AddField_management(joinFN, "x", "FLOAT")
		arcpy.AddField_management(joinFN, "y", "FLOAT")
		arcpy.AddField_management(joinFN, "geom_id", "DOUBLE")
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
		arcpy.AddField_management(joinFN, "deed_restricted_units", "SHORT")
		arcpy.AddField_management(joinFN, "source", "TEXT","","",15)
		arcpy.AddField_management(joinFN, "edit_date", "LONG")
		arcpy.AddField_management(joinFN, "editor", "TEXT","","",50)
		arcpy.AddField_management(joinFN, "version", "SHORT")
		if not arcpy.ListFields(joinFN, "incl"):
			arcpy.AddField_management(joinFN, "incl", "SHORT")

		arcpy.CalculateField_management(joinFN, "raw_id", '!manual_dp_id!')
		arcpy.CalculateField_management(joinFN, "building_name", '!m_building_name!')
		arcpy.CalculateField_management(joinFN, "site_name", '!m_site_name!')
		arcpy.CalculateField_management(joinFN, "PARCEL_ID", '!m_parcel_id!')
		arcpy.CalculateField_management(joinFN, "scen0", 1)
		arcpy.CalculateField_management(joinFN, "scen1", 1)
		arcpy.CalculateField_management(joinFN, "scen2", 1)
		arcpy.CalculateField_management(joinFN, "scen3", 1)
		arcpy.CalculateField_management(joinFN, "scen4", 1)
		arcpy.CalculateField_management(joinFN, "scen5", 1)
		arcpy.CalculateField_management(joinFN, "scen6", 1)
		arcpy.CalculateField_management(joinFN, "scen7", 1)
		arcpy.CalculateField_management(joinFN, "scen10", 1)
		arcpy.CalculateField_management(joinFN, "scen11", 1)
		arcpy.CalculateField_management(joinFN, "scen12", 1)
		arcpy.CalculateField_management(joinFN, "scen15", 1)
		arcpy.CalculateField_management(joinFN, "scen20", 1)
		arcpy.CalculateField_management(joinFN, "scen21", 1)
		arcpy.CalculateField_management(joinFN, "scen22", 1)
		arcpy.CalculateField_management(joinFN, "scen23", 1)
		arcpy.CalculateField_management(joinFN, "scen24", 1)
		arcpy.CalculateField_management(joinFN, "scen25", 1)  # these are committed so 1 for all scens 
		#not sure how to change zip field type
		#arcpy.CalculateField_management(joinFN, "zip", '!m_zip!')
		arcpy.CalculateField_management(joinFN, "x", '!X_1!') #use spatial info from parcel file
		arcpy.CalculateField_management(joinFN, "y", '!Y_1!') #use spatial info from parcel file
		arcpy.CalculateField_management(joinFN, "geom_id", '!p_geom_id!') #use spatial info from parcel file
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
		arcpy.CalculateField_management(joinFN, "deed_restricted_units", 0)
		arcpy.CalculateField_management(joinFN, "source", "'manual'")
		arcpy.CalculateField_management(joinFN, "edit_date", 20200429)
		arcpy.CalculateField_management(joinFN, "editor", "'MKR'")
		#arcpy.CalculateField_management(joinFN, "version", )
					#remove row where incl != 1
		with arcpy.da.UpdateCursor(joinFN, "incl") as cursor:
			for row in cursor:
				if row[0] != 1:
					cursor.deleteRow()	
			#check to make sure that the number of remaining records in the temp file (which should still have var incl) is the same as the raw file
		countTwo = countRow(joinFN)
		if countTwo == countOne:
			logger.info("All records with incl = 1 in feature class {} are included in the temp file".format(manual_dp))
		else:
			logger.fatal("Something is wrong in the code, please check")
			raise
		### 3 DELETE OTHER FIELDS
		FCfields = [f.name for f in arcpy.ListFields(joinFN)]
		#add "rent_ave_sqft", "rent_ave_unit","version", "duration", "building_type_id" if needed
		DontDeleteFields = ["OBJECTID","Shape","development_projects_id", "raw_id", "building_name", "site_name",  "action", 
		"scen0", "scen1", "scen2", "scen3", "scen4", "scen5", "scen6", "scen7", "scen10", "scen11", "scen12", "scen15", "scen20", "scen21", "scen22", "scen23", "scen24", "scen25",
		"address",  "city",  "zip",  "county", "x", "y", "geom_id", "year_built","building_type", "building_sqft", "non_residential_sqft", "residential_units", "unit_ave_sqft", 
		"tenure", "rent_type", "stories", "parking_spaces", "average_weighted_rent", "last_sale_year", "last_sale_price", "deed_restricted_units","source", "PARCEL_ID", "ZONE_ID", "edit_date", "editor", "Shape_Length", "Shape_Area"]
		fields2Delete = list(set(FCfields) - set(DontDeleteFields))
		arcpy.DeleteField_management(joinFN, fields2Delete)
		arcpy.MakeTableView_management(joinFN,gidnull,"geom_id is NULL")
		nullcount = arcpy.GetCount_management(gidnull)
		logger.info("{} list has {} records with geom_id info missing".format(joinFN, nullcount))
		arcpy.Delete_management(gidnull)

	gList = [row[0] for row in arcpy.da.SearchCursor(joinFN, 'PARCEL_ID')]
	for geo in gList:
		geoList.append(geo)

	### for costar data
	### create a list of feature class
	cs = [cs1115,cs1620]
	for fc in cs:
		countOne = countRow(fc)
		logger.info("Feature Class {} has {} records with incl = 1".format(fc, countOne))
		joinFN = 'ttt_' + arcpy.Describe(fc).name + '__p10_pba50'
		dev_projects_temp_layers.append(joinFN)
	
		### 1 SPATIAL JOINS
		logger.info("Creating layer {} by spatial joining costar ({}) and parcels ({})".format(joinFN, fc, p10_pba50))
		arcpy.SpatialJoin_analysis(fc, p10_pba50, joinFN)
		### 2 VARIABLE CLEANING 
		
		# rename any conflicting field names
		arcpy.AlterField_management(joinFN, "building_name", "cs_building_name")
		arcpy.AlterField_management(joinFN, "parcel_id", "cs_parcel_id")
		arcpy.AlterField_management(joinFN, "city", "cs_city")
		arcpy.AlterField_management(joinFN, "Zip", "cs_zip")
		arcpy.AlterField_management(joinFN, "rent_type", "cs_rent_type")
		arcpy.AlterField_management(joinFN, "year_built", "cs_year_built")
		arcpy.AlterField_management(joinFN, "last_sale_price", "cs_last_sale_price")
		arcpy.AlterField_management(joinFN, "last_sale_date", "cs_last_sale_date")
		arcpy.AlterField_management(joinFN, "Average_Weighted_Rent", "cs_average_weighted_rent")
		arcpy.AlterField_management(joinFN, "x", "p_x") 
		arcpy.AlterField_management(joinFN, "y", "p_y") 
		arcpy.AlterField_management(joinFN, "geom_id", "p_geom_id") # this is from the parcel 
	
		# add fields and calc values
		# full list development_projects_id,raw_id,building_name,site_name,action,scen0,scen1,
		# address,city,zip,county,x,y,geom_id,year_built,duration,building_type_id,building_type,building_sqft,non_residential_sqft,
		# residential_units,unit_ave_sqft,tenure,rent_type,stories,parking_spaces,Average Weighted Rent,rent_ave_sqft,rent_ave_unit,
		# last_sale_year,last_sale_price,source,edit_date,editor,version
		# AddField(in_table, field_name, field_type, {field_precision}, {field_scale}, {field_length}, {field_alias}, {field_is_nullable}, {field_is_required}, {field_domain})
		arcpy.AddField_management(joinFN, "development_projects_id", "LONG")
		arcpy.AddField_management(joinFN, "raw_id", "LONG")
		arcpy.AddField_management(joinFN, "building_name", "TEXT","","",200)
		arcpy.AddField_management(joinFN, "site_name", "TEXT","","",200)
		arcpy.AddField_management(joinFN, "PARCEL_ID", "LONG")
		arcpy.AddField_management(joinFN, "action", "TEXT","","",10)
		arcpy.AddField_management(joinFN, "scen0", "SHORT")
		arcpy.AddField_management(joinFN, "scen1", "SHORT")
		arcpy.AddField_management(joinFN, "scen2", "SHORT")
		arcpy.AddField_management(joinFN, "scen3", "SHORT")
		arcpy.AddField_management(joinFN, "scen4", "SHORT")
		arcpy.AddField_management(joinFN, "scen5", "SHORT")
		arcpy.AddField_management(joinFN, "scen6", "SHORT")
		arcpy.AddField_management(joinFN, "scen7", "SHORT")
		arcpy.AddField_management(joinFN, "scen10", "SHORT")
		arcpy.AddField_management(joinFN, "scen11", "SHORT")
		arcpy.AddField_management(joinFN, "scen12", "SHORT")
		arcpy.AddField_management(joinFN, "scen15", "SHORT")
		arcpy.AddField_management(joinFN, "scen20", "SHORT")
		arcpy.AddField_management(joinFN, "scen21", "SHORT")
		arcpy.AddField_management(joinFN, "scen22", "SHORT")
		arcpy.AddField_management(joinFN, "scen23", "SHORT")
		arcpy.AddField_management(joinFN, "scen24", "SHORT")
		arcpy.AddField_management(joinFN, "scen25", "SHORT") 
		arcpy.AddField_management(joinFN, "address", "TEXT","","",200)
		arcpy.AddField_management(joinFN, "city", "TEXT","","",50)
		arcpy.AddField_management(joinFN, "zip",  "TEXT","","",50) ## this is changed from LONG to TEXT because cs1115 file has some text formatted zipcode with "-"
		arcpy.AddField_management(joinFN, "county", "TEXT","","",50)
		arcpy.AddField_management(joinFN, "x", "FLOAT")
		arcpy.AddField_management(joinFN, "y", "FLOAT")
		arcpy.AddField_management(joinFN, "geom_id", "DOUBLE")
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
		arcpy.AddField_management(joinFN, "deed_restricted_units", "SHORT")
		arcpy.AddField_management(joinFN, "source", "TEXT","","",15)
		arcpy.AddField_management(joinFN, "edit_date", "LONG")
		arcpy.AddField_management(joinFN, "editor", "TEXT","","",50)
		arcpy.AddField_management(joinFN, "version", "SHORT")
		if not arcpy.ListFields(joinFN, "incl"):
			arcpy.AddField_management(joinFN, "incl", "SHORT")
	
		arcpy.CalculateField_management(joinFN, "raw_id", '!PropertyID!')
		arcpy.CalculateField_management(joinFN, "building_name", '!cs_building_name!')
		arcpy.CalculateField_management(joinFN, "site_name", '!Building_Park!')
		arcpy.CalculateField_management(joinFN, "PARCEL_ID", '!cs_parcel_id!')
		arcpy.CalculateField_management(joinFN, "action", "'build'")# need to quote marks here
		arcpy.CalculateField_management(joinFN, "scen0", 1)
		arcpy.CalculateField_management(joinFN, "scen1", 1)
		arcpy.CalculateField_management(joinFN, "scen2", 1)
		arcpy.CalculateField_management(joinFN, "scen3", 1)
		arcpy.CalculateField_management(joinFN, "scen4", 1)
		arcpy.CalculateField_management(joinFN, "scen5", 1)
		arcpy.CalculateField_management(joinFN, "scen6", 1)
		arcpy.CalculateField_management(joinFN, "scen7", 1)
		arcpy.CalculateField_management(joinFN, "scen10", 1)
		arcpy.CalculateField_management(joinFN, "scen11", 1)
		arcpy.CalculateField_management(joinFN, "scen12", 1)
		arcpy.CalculateField_management(joinFN, "scen15", 1)
		arcpy.CalculateField_management(joinFN, "scen20", 1)
		arcpy.CalculateField_management(joinFN, "scen21", 1)
		arcpy.CalculateField_management(joinFN, "scen22", 1)
		arcpy.CalculateField_management(joinFN, "scen23", 1)
		arcpy.CalculateField_management(joinFN, "scen24", 1)
		arcpy.CalculateField_management(joinFN, "scen25", 1)  # these are committed so 1 for all scens 
		arcpy.CalculateField_management(joinFN, "address", '!Building_Address!')
		arcpy.CalculateField_management(joinFN, "city", '!cs_city!')
		arcpy.CalculateField_management(joinFN, "zip", '!cs_zip!')
		arcpy.CalculateField_management(joinFN, "county", '!County_Name!')
		arcpy.CalculateField_management(joinFN, "x", '!p_x!') #use spatial info from parcel file
		arcpy.CalculateField_management(joinFN, "y", '!p_y!') #use spatial info from parcel file
		arcpy.CalculateField_management(joinFN, "geom_id", '!p_geom_id!') #use spatial info from parcel file
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
		#there is a worng parking space value is one of the tables, so adding this to work around
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

		with arcpy.da.UpdateCursor(joinFN, ["cs_rent_type","residential_units","deed_restricted_units"]) as cursor:
			for row in cursor:
				if row[0] == "Affordable":
					row[2] = row[1]
				elif row[0] == "Market/Affordable":
					row[2] = int(row[1] // 5)
				else:
					row[2] =0
				cursor.updateRow(row)

		arcpy.CalculateField_management(joinFN, "source", "'cs'")
		arcpy.CalculateField_management(joinFN, "edit_date", 20200429)
		arcpy.CalculateField_management(joinFN, "editor", "'MKR'")
		#arcpy.CalculateField_management(joinFN, "version", )
	
		#remove row where incl != 1
		with arcpy.da.UpdateCursor(joinFN, "incl") as cursor:
			for row in cursor:
				if row[0] != 1:
					cursor.deleteRow()
	
		#check all incl = 1 records are included 
		countTwo = countRow(joinFN)
		if countTwo == countOne:
			logger.info("All records with incl = 1 in feature class {} is included in the temp file".format(fc))
		else:
			logger.fatal("Something is wrong in the code, please check")
			raise

		### 3 DELETE OTHER FIELDS AND TEMP FILES
		FCfields = [f.name for f in arcpy.ListFields(joinFN)]
		#add "rent_ave_sqft", "rent_ave_unit","version", "duration", "building_type_id" if needed
		DontDeleteFields = ["OBJECTID","Shape","development_projects_id", "raw_id", "building_name", "site_name",  "action", 
		"scen0", "scen1", "scen2", "scen3", "scen4", "scen5", "scen6", "scen7", "scen10", "scen11", "scen12", "scen15", "scen20", "scen21", "scen22", "scen23", "scen24", "scen25",
		"address",  "city",  "zip",  "county", "x", "y", "geom_id", "year_built","building_type", "building_sqft", "non_residential_sqft", "residential_units", "unit_ave_sqft", 
		"tenure", "rent_type", "stories", "parking_spaces", "average_weighted_rent", "last_sale_year", "last_sale_price", "deed_restricted_units","source", "PARCEL_ID", "ZONE_ID", "edit_date", "editor", "Shape_Length", "Shape_Area"]
		fields2Delete = list(set(FCfields) - set(DontDeleteFields))
		arcpy.DeleteField_management(joinFN, fields2Delete)

		#zero out non res sqft for residential types (HS, HM, HT)
		with arcpy.da.UpdateCursor(joinFN, ["building_type","non_residential_sqft"]) as cursor:
			for row in cursor:
				if row[0] == 'HT':
					row[1] = 0
				elif row[0] == 'HS':
					row[1] = 0
				elif row[0] == 'HM':
					row[1] = 0
				cursor.updateRow(row)

		gidnull = 'gidnull'
		arcpy.MakeTableView_management(joinFN,gidnull,"geom_id is NULL")
		nullcount = arcpy.GetCount_management(gidnull)
		logger.info("{} list has {} records with geom_id info missing".format(joinFN, nullcount))
		arcpy.Delete_management(gidnull)

		###4 REMOVE DUPLICATES
		#check again existing geomList and remove duplicates
		with arcpy.da.UpdateCursor(joinFN, "PARCEL_ID") as cursor:
			for row in cursor:
				if row[0] in geoList:
					cursor.deleteRow()

		#then add the geoms in the geomList
		gList = [row[0] for row in arcpy.da.SearchCursor(joinFN, 'PARCEL_ID')]
		for geo in gList:
			geoList.append(geo)
		

	### for BASIS pipeline data
	countOne = countRow(basis_pipeline)
	logger.info("Feature Class {} has {} records with incl = 1".format(basis_pipeline, countOne))
	joinFN = 'ttt_basispp_p10_pba50'
	dev_projects_temp_layers.append(joinFN)
	
	### 1 SPATIAL JOINS
	logger.info("Creating layer {} by spatial joining BASIS pipeline data ({}) and parcels ({})".format(joinFN, basis_pipeline, p10_pba50))
	arcpy.SpatialJoin_analysis(basis_pipeline, p10_pba50, joinFN)
	
	### 2 VARIABLE CLEANING 
	# rename any conflicting field names
	arcpy.AlterField_management(joinFN, "county", "b_county")
	arcpy.AlterField_management(joinFN, "parcel_id", "b_parcel_id")
	arcpy.AlterField_management(joinFN, "raw_id", "b_id")
	arcpy.AlterField_management(joinFN, "year_built", "b_year_built")
	arcpy.AlterField_management(joinFN, "zip", "b_zip")
	arcpy.AlterField_management(joinFN, "stories", "b_stories")
	arcpy.AlterField_management(joinFN, "x", "p_x") # this is from the parcel centroid
	arcpy.AlterField_management(joinFN, "y", "p_y") # this is from the parcel centroid
	arcpy.AlterField_management(joinFN, "geom_id", "p_geom_id")# this is from the parcel
	arcpy.AlterField_management(joinFN, "residential_units", "p_residential_units") 
	arcpy.AlterField_management(joinFN, "edit_date", "p_edit_date")
	# add fields and calc values
	# full list development_projects_id,raw_id,building_name,site_name,action,scen0,scen1,
	# address,city,zip,county,x,y,geom_id,year_built,duration,building_type_id,building_type,building_sqft,non_residential_sqft,
	# residential_units,unit_ave_sqft,tenure,rent_type,stories,parking_spaces,Average Weighted Rent,rent_ave_sqft,rent_ave_unit,
	# last_sale_year,last_sale_price,source,edit_date,editor,version
	# AddField(in_table, field_name, field_type, {field_precision}, {field_scale}, {field_length}, {field_alias}, {field_is_nullable}, {field_is_required}, {field_domain})
	arcpy.AddField_management(joinFN, "development_projects_id", "LONG")
	arcpy.AddField_management(joinFN, "raw_id", "LONG")
	arcpy.AddField_management(joinFN, "building_name", "TEXT","","",200)
	arcpy.AddField_management(joinFN, "site_name", "TEXT","","",200)
	arcpy.AddField_management(joinFN, "PARCEL_ID", "LONG")
	arcpy.AddField_management(joinFN, "action", "TEXT","","",10)
	arcpy.AddField_management(joinFN, "scen0", "SHORT")
	arcpy.AddField_management(joinFN, "scen1", "SHORT")
	arcpy.AddField_management(joinFN, "scen2", "SHORT")
	arcpy.AddField_management(joinFN, "scen3", "SHORT")
	arcpy.AddField_management(joinFN, "scen4", "SHORT")
	arcpy.AddField_management(joinFN, "scen5", "SHORT")
	arcpy.AddField_management(joinFN, "scen6", "SHORT")
	arcpy.AddField_management(joinFN, "scen7", "SHORT")
	arcpy.AddField_management(joinFN, "scen10", "SHORT")
	arcpy.AddField_management(joinFN, "scen11", "SHORT")
	arcpy.AddField_management(joinFN, "scen12", "SHORT")
	arcpy.AddField_management(joinFN, "scen15", "SHORT")
	arcpy.AddField_management(joinFN, "scen20", "SHORT")
	arcpy.AddField_management(joinFN, "scen21", "SHORT")
	arcpy.AddField_management(joinFN, "scen22", "SHORT")
	arcpy.AddField_management(joinFN, "scen23", "SHORT")
	arcpy.AddField_management(joinFN, "scen24", "SHORT")
	arcpy.AddField_management(joinFN, "scen25", "SHORT") 
	arcpy.AddField_management(joinFN, "address", "TEXT","","",200)
	arcpy.AddField_management(joinFN, "city", "TEXT","","",50)
	arcpy.AddField_management(joinFN, "zip", "TEXT","","",50)
	arcpy.AddField_management(joinFN, "county", "TEXT","","",50)
	arcpy.AddField_management(joinFN, "x", "FLOAT")
	arcpy.AddField_management(joinFN, "y", "FLOAT")
	arcpy.AddField_management(joinFN, "geom_id", "DOUBLE")
	arcpy.AddField_management(joinFN, "year_built", "SHORT")
	arcpy.AddField_management(joinFN, "duration", "SHORT")
	arcpy.AddField_management(joinFN, "building_type_id", "LONG")
	arcpy.AddField_management(joinFN, "building_type", "TEXT","","",4)
	arcpy.AddField_management(joinFN, "building_sqft", "LONG")
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
	arcpy.AddField_management(joinFN, "deed_restricted_units", "SHORT")
	arcpy.AddField_management(joinFN, "source", "TEXT","","",15)
	arcpy.AddField_management(joinFN, "edit_date", "LONG")
	if not arcpy.ListFields(joinFN, "incl"):
		arcpy.AddField_management(joinFN, "incl", "SHORT")
	
	arcpy.CalculateField_management(joinFN, "building_name", '!project_name!')
	arcpy.CalculateField_management(joinFN, "action", "'build'")# need to quote marks here
	arcpy.CalculateField_management(joinFN, "PARCEL_ID", '!b_parcel_id!')
	arcpy.CalculateField_management(joinFN, "scen0", 1)
	arcpy.CalculateField_management(joinFN, "scen1", 1)
	arcpy.CalculateField_management(joinFN, "scen2", 1)
	arcpy.CalculateField_management(joinFN, "scen3", 1)
	arcpy.CalculateField_management(joinFN, "scen4", 1)
	arcpy.CalculateField_management(joinFN, "scen5", 1)
	arcpy.CalculateField_management(joinFN, "scen6", 1)
	arcpy.CalculateField_management(joinFN, "scen7", 1)
	arcpy.CalculateField_management(joinFN, "scen10", 1)
	arcpy.CalculateField_management(joinFN, "scen11", 1)
	arcpy.CalculateField_management(joinFN, "scen12", 1)
	arcpy.CalculateField_management(joinFN, "scen15", 1)
	arcpy.CalculateField_management(joinFN, "scen20", 1)
	arcpy.CalculateField_management(joinFN, "scen21", 1)
	arcpy.CalculateField_management(joinFN, "scen22", 1)
	arcpy.CalculateField_management(joinFN, "scen23", 1)
	arcpy.CalculateField_management(joinFN, "scen24", 1)
	arcpy.CalculateField_management(joinFN, "scen25", 1)  # these are committed so 1 for all scens 
	arcpy.CalculateField_management(joinFN, "address", '!street_address!')
	arcpy.CalculateField_management(joinFN, "city", '!mailing_city_name!')
	##arcpy.CalculateField_management(joinFN, "zip", '!b_zip!') ##not sure how to convert text to long data type
	arcpy.CalculateField_management(joinFN, "county", '!b_county!')
	arcpy.CalculateField_management(joinFN, "x", '!p_x!') 
	arcpy.CalculateField_management(joinFN, "y", '!p_y!') 
	arcpy.CalculateField_management(joinFN, "geom_id", '!p_geom_id!')
	arcpy.CalculateField_management(joinFN, "year_built", '!b_year_built!')
	arcpy.CalculateField_management(joinFN, "building_type", '!building_type_det!')
	arcpy.CalculateField_management(joinFN, "building_sqft", '!building_sqft!') # how often null for res
	arcpy.CalculateField_management(joinFN, "residential_units", '!p_residential_units!')
	arcpy.CalculateField_management(joinFN, "tenure", "'Rent'") ##what is tenure
	arcpy.CalculateField_management(joinFN, "stories", '!b_stories!')
	arcpy.CalculateField_management(joinFN, "deed_restricted_units", 0)
	arcpy.CalculateField_management(joinFN, "source", "'basis'")
	arcpy.CalculateField_management(joinFN, "edit_date", 20200429)
	#arcpy.CalculateField_management(joinFN, "version", )
	
	#remove row where incl != 1
	with arcpy.da.UpdateCursor(joinFN, "incl") as cursor:
		for row in cursor:
			if row[0] != 1:
				cursor.deleteRow()
	
	#check all incl = 1 records are included 
	countTwo = countRow(joinFN)
	if countTwo == countOne:
		logger.info("All records with incl = 1 in feature class {} are included in the temp file".format(basis_pipeline))
	else:
		logger.fatal("Something is wrong in the code, please check")
		raise
	
	### 3 DELETE OTHER FIELDS
	FCfields = [f.name for f in arcpy.ListFields(joinFN)]
	#add "rent_ave_sqft", "rent_ave_unit","version", "duration", "building_type_id" if needed
	DontDeleteFields = ["OBJECTID","Shape","development_projects_id", "raw_id", "building_name", "site_name",  "action", 
	"scen0", "scen1", "scen2", "scen3", "scen4", "scen5", "scen6", "scen7", "scen10", "scen11", "scen12", "scen15", "scen20", "scen21", "scen22", "scen23", "scen24", "scen25",
	"address",  "city",  "zip",  "county", "x", "y", "geom_id", "year_built","building_type", "building_sqft", "non_residential_sqft", "residential_units", "unit_ave_sqft", 
	"tenure", "rent_type", "stories", "parking_spaces", "average_weighted_rent", "last_sale_year", "last_sale_price", "deed_restricted_units","source", "PARCEL_ID", "ZONE_ID", "edit_date", "editor", "Shape_Length", "Shape_Area"]
	fields2Delete = list(set(FCfields) - set(DontDeleteFields))
	arcpy.DeleteField_management(joinFN, fields2Delete)

	gidnull = 'gidnull'
	arcpy.MakeTableView_management(joinFN,gidnull,"geom_id is NULL")
	nullcount = arcpy.GetCount_management(gidnull)
	logger.info("{} list has {} records with geom_id info missing".format(joinFN, nullcount))
	arcpy.Delete_management(gidnull)

	###4 REMOVE DUPLICATES
	#check again existing geomList and remove duplicates
	with arcpy.da.UpdateCursor(joinFN, "PARCEL_ID") as cursor:
		for row in cursor:
			if row[0] in geoList:
				cursor.deleteRow()
	#then add the geoms in the geomList
	gList = [row[0] for row in arcpy.da.SearchCursor(joinFN, 'PARCEL_ID')]
	for geo in gList:
		geoList.append(geo)


	### for basis_pb
	countOne = countRow(basis_pb_new)
	logger.info("Feature Class {} has {} records with incl = 1".format(basis_pb_new, countOne))
	joinFN = 'ttt_basis_pb_new_p10__pba50'
	dev_projects_temp_layers.append(joinFN)

	logger.info("Creating layer {} by spatial joining basis pba pipeline data ({}) and parcels ({})".format(joinFN, basis_pb_new, p10_pba50))
	arcpy.DeleteField_management(basis_pb_new, "geom_id") #this column is causing trouble
	arcpy.SpatialJoin_analysis(basis_pb_new, p10_pba50, joinFN)

	#remove records on parcels where there are no increase in residential units -- in comparsion to b10 table
	#first count existing rows
	cnt1 = arcpy.GetCount_management(joinFN)
	#examine building
	b10_smelt = os.path.join(SMELT_GDB, "b10")
	arcpy.TableToTable_conversion(b10_smelt, arcpy.env.workspace,'b10')
	b10 = 'b10'
	arcpy.analysis.Statistics(b10, 'b10_unitSUM',"residential_units SUM", "parcel_id")
	nonZero = arcpy.SelectLayerByAttribute_management('b10_unitSUM', "NEW_SELECTION", '"SUM_residential_units" > 0')#choose only parcels with residential units already
	arcpy.CopyRows_management(nonZero, 'nonZeroParcel')
	arcpy.AddJoin_management(joinFN, "parcel_id", "nonZeroParcel", "parcel_id","KEEP_COMMON")
	arcpy.SelectLayerByAttribute_management(joinFN, "NEW_SELECTION", "ttt_basis_pb_new_p10__pba50.urbansim_parcels_v3_geo_county_id = 85", None)
	#find parcels to remove 
	parcelRemoveList = []
	with arcpy.da.SearchCursor(joinFN,['parcel_id',
										"residential_units",
										"SUM_residential_units"]) as cursor:
		for row in cursor:
			if row[1] is not None:
				if row[1] - row[2] == 0: 
					parcelRemoveList.append(row[0])
	logger.info("There are {} records in basis_pb_new that do not see increase in residential unit counts on the parcel".format(len(parcelRemoveList)))			
	#remove join
	arcpy.RemoveJoin_management(joinFN, "nonZeroParcel")
	#remove records
	with arcpy.da.UpdateCursor(joinFN, "parcel_id") as cursor:
		for row in cursor:
			if row[0] in parcelRemoveList:
				cursor.deleteRow()
	arcpy.SelectLayerByAttribute_management(joinFN, "CLEAR_SELECTION")
	#count after rows
	cnt2 = arcpy.GetCount_management(joinFN)
	#check remove is successful
	cnt =  int(cnt1[0]) - int(cnt2[0])
	logger.info("Removed {} records".format(cnt))

	arcpy.AlterField_management(joinFN, "year_built", "n_year_built")
	arcpy.AlterField_management(joinFN, "building_sqft", "n_building_sqft")
	arcpy.AlterField_management(joinFN, "residential_units", "n_residential_units")
	arcpy.AlterField_management(joinFN, "X", "n_x")
	arcpy.AlterField_management(joinFN, "Y", "n_y")
	arcpy.AlterField_management(joinFN, "GEOM_ID", "n_geom_id")
	arcpy.AlterField_management(joinFN, "parcel_id", "n_parcel_id")

	arcpy.AddField_management(joinFN, "development_projects_id", "LONG")
	arcpy.AddField_management(joinFN, "raw_id", "LONG")
	arcpy.AddField_management(joinFN, "building_name", "TEXT","","",200)
	arcpy.AddField_management(joinFN, "site_name", "TEXT","","",200)
	arcpy.AddField_management(joinFN, "PARCEL_ID", "LONG")
	arcpy.AddField_management(joinFN, "action", "TEXT","","",10)
	arcpy.AddField_management(joinFN, "scen0", "SHORT")
	arcpy.AddField_management(joinFN, "scen1", "SHORT")
	arcpy.AddField_management(joinFN, "scen2", "SHORT")
	arcpy.AddField_management(joinFN, "scen3", "SHORT")
	arcpy.AddField_management(joinFN, "scen4", "SHORT")
	arcpy.AddField_management(joinFN, "scen5", "SHORT")
	arcpy.AddField_management(joinFN, "scen6", "SHORT")
	arcpy.AddField_management(joinFN, "scen7", "SHORT")
	arcpy.AddField_management(joinFN, "scen10", "SHORT")
	arcpy.AddField_management(joinFN, "scen11", "SHORT")
	arcpy.AddField_management(joinFN, "scen12", "SHORT")
	arcpy.AddField_management(joinFN, "scen15", "SHORT")
	arcpy.AddField_management(joinFN, "scen20", "SHORT")
	arcpy.AddField_management(joinFN, "scen21", "SHORT")
	arcpy.AddField_management(joinFN, "scen22", "SHORT")
	arcpy.AddField_management(joinFN, "scen23", "SHORT")
	arcpy.AddField_management(joinFN, "scen24", "SHORT")
	arcpy.AddField_management(joinFN, "scen25", "SHORT")
	arcpy.AddField_management(joinFN, "address", "TEXT","","",200)
	arcpy.AddField_management(joinFN, "city", "TEXT","","",50)
	arcpy.AddField_management(joinFN, "zip",  "TEXT","","",50) ## this is changed from LONG to TEXT because cs1115 file has some text formatted zipcode with "-"
	arcpy.AddField_management(joinFN, "county", "TEXT","","",50)
	arcpy.AddField_management(joinFN, "x", "FLOAT")
	arcpy.AddField_management(joinFN, "y", "FLOAT")
	arcpy.AddField_management(joinFN, "geom_id", "DOUBLE")
	arcpy.AddField_management(joinFN, "year_built", "SHORT")
	arcpy.AddField_management(joinFN, "duration", "SHORT")
	arcpy.AddField_management(joinFN, "building_type_id", "LONG")
	arcpy.AddField_management(joinFN, "building_sqft", "LONG")
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
	arcpy.AddField_management(joinFN, "deed_restricted_units", "SHORT")
	arcpy.AddField_management(joinFN, "source", "TEXT","","",15)
	arcpy.AddField_management(joinFN, "edit_date", "LONG")
	arcpy.AddField_management(joinFN, "editor", "TEXT","","",50)
	arcpy.AddField_management(joinFN, "version", "SHORT")
	
	arcpy.CalculateField_management(joinFN, "PARCEL_ID", '!n_parcel_id!')
	arcpy.CalculateField_management(joinFN, "scen0", 1)
	arcpy.CalculateField_management(joinFN, "scen1", 1)
	arcpy.CalculateField_management(joinFN, "scen2", 1)
	arcpy.CalculateField_management(joinFN, "scen3", 1)
	arcpy.CalculateField_management(joinFN, "scen4", 1)
	arcpy.CalculateField_management(joinFN, "scen5", 1)
	arcpy.CalculateField_management(joinFN, "scen6", 1)
	arcpy.CalculateField_management(joinFN, "scen7", 1)
	arcpy.CalculateField_management(joinFN, "scen10", 1)
	arcpy.CalculateField_management(joinFN, "scen11", 1)
	arcpy.CalculateField_management(joinFN, "scen12", 1)
	arcpy.CalculateField_management(joinFN, "scen15", 1)
	arcpy.CalculateField_management(joinFN, "scen20", 1)
	arcpy.CalculateField_management(joinFN, "scen21", 1)
	arcpy.CalculateField_management(joinFN, "scen22", 1)
	arcpy.CalculateField_management(joinFN, "scen23", 1)
	arcpy.CalculateField_management(joinFN, "scen24", 1)
	arcpy.CalculateField_management(joinFN, "scen25", 1) # these are committed so 1 for all scens 
	arcpy.CalculateField_management(joinFN, "action", "'build'")
	arcpy.CalculateField_management(joinFN, "city", '!urbansim_parcels_v3_geo_city!')
	with arcpy.da.UpdateCursor(joinFN, ["urbansim_parcels_v3_geo_county", "county"]) as cursor:
		for row in cursor:
			if row[0] == 1:
				row[1] = 'Alameda'
			elif row[0] == 13:
				row[1] = 'Contra Costa'
			elif row[0] == 41:
				row[1] = 'Marin'
			elif row[0] == 55:
				row[1] = 'Napa'
			elif row[0] == 75:
				row[1] = 'San Francisco'
			elif row[0] == 81:
				row[1] = 'San Mateo'
			elif row[0] == 85:
				row[1] = 'Santa Clara'
			elif row[0] == 95:
				row[1] = 'Solano'
			elif row[0] == 97:
				row[1] = 'Sonoma'
			cursor.updateRow(row)
	arcpy.CalculateField_management(joinFN, "x", '!n_x!') 
	arcpy.CalculateField_management(joinFN, "y", '!n_y!')
	arcpy.CalculateField_management(joinFN, "geom_id", '!n_geom_id!')
	arcpy.CalculateField_management(joinFN, "year_built", '!n_year_built!')
	arcpy.CalculateField_management(joinFN, "building_sqft", '!n_building_sqft!')
	arcpy.CalculateField_management(joinFN, "residential_units", '!n_residential_units!')

	with arcpy.da.UpdateCursor(joinFN, ["building_sqft", "residential_units", "unit_ave_sqft"]) as cursor:
		for row in cursor:
			if row[1] is int:
				row[2] = row[0] / row[1] 
				cursor.updateRow(row)

	arcpy.CalculateField_management(joinFN, "last_sale_year", '!last_sale_date!') #need to make into year
	arcpy.CalculateField_management(joinFN, "deed_restricted_units", 0)
	arcpy.CalculateField_management(joinFN, "source", "'bas_bp_new'")
	arcpy.CalculateField_management(joinFN, "edit_date", 20200429)
	arcpy.CalculateField_management(joinFN, "editor", "'MKR'")

	with arcpy.da.UpdateCursor(joinFN, "incl") as cursor:
		for row in cursor:
			if row[0] != 1:
				cursor.deleteRow()	

	#check to make sure that the number of remaining records in the temp file (which should still have var incl) is the same as the raw file
	#countTwo = countRow(joinFN)
	#if countTwo == countOne:
	#	logger.info("All records with incl = 1 in feature class {} are included in the temp file".format(basis_pb_new))
	#else:
	#	logger.fatal("Something is wrong in the code, please check")
	#	raise
	### 3 DELETE OTHER FIELDS
	FCfields = [f.name for f in arcpy.ListFields(joinFN)]
	#add "rent_ave_sqft", "rent_ave_unit","version", "duration", "building_type_id" if needed
	DontDeleteFields = ["OBJECTID","Shape","development_projects_id", "raw_id", "building_name", "site_name",  "action", 
	"scen0", "scen1", "scen2", "scen3", "scen4", "scen5", "scen6", "scen7", "scen10", "scen11", "scen12", "scen15", "scen20", "scen21", "scen22", "scen23", "scen24", "scen25",
	"address",  "city",  "zip",  "county", "x", "y", "geom_id", "year_built","building_type", "building_sqft", "non_residential_sqft", "residential_units", "unit_ave_sqft", 
	"tenure", "rent_type", "stories", "parking_spaces", "average_weighted_rent", "last_sale_year", "last_sale_price", "deed_restricted_units","source", "PARCEL_ID", "ZONE_ID", "edit_date", "editor", "Shape_Length", "Shape_Area"]
	fields2Delete = list(set(FCfields) - set(DontDeleteFields))
	arcpy.DeleteField_management(joinFN, fields2Delete)

	gidnull = 'gidnull'
	arcpy.MakeTableView_management(joinFN,gidnull,"geom_id is NULL")
	nullcount = arcpy.GetCount_management(gidnull)
	logger.info("{} list has {} records with geom_id info missing".format(joinFN, nullcount))
	arcpy.Delete_management(gidnull)
	###4 REMOVE DUPLICATES
	#check again existing geomList and remove duplicates
	with arcpy.da.UpdateCursor(joinFN, "PARCEL_ID") as cursor:
		for row in cursor:
			if row[0] in geoList:
				cursor.deleteRow()
	#then add the geoms in the geomList
	gList = [row[0] for row in arcpy.da.SearchCursor(joinFN, 'PARCEL_ID')]
	for geo in gList:
		geoList.append(geo)

	### for redfin data
	### create a list of feature class
	rf = [rfsfr1619, rfsfr1115, rfmu1619, rfcondo1115, rfother1115]
	for fc in rf:
		countOne = countRow(fc)
		logger.info("Feature Class {} has {} records with incl = 1".format(fc, countOne))
		joinFN = 'ttt_' + arcpy.Describe(fc).name + '__p10_pba50'
		dev_projects_temp_layers.append(joinFN)
	
		### 1 SPATIAL JOINS
		logger.info("Creating layer {} by spatial joining redfin ({}) and parcels ({})".format(joinFN, fc, p10_pba50))
		arcpy.SpatialJoin_analysis(fc, os.path.join(SMELT_GDB, p10_pba50), joinFN)
		### 2 VARIABLE CLEANING 
		
		# rename any conflicting field names
		arcpy.AlterField_management(joinFN, "CITY", "rf_city")
		arcpy.AlterField_management(joinFN, "COUNTY", "rf_county")
		arcpy.AlterField_management(joinFN, "YEAR_BUILT", "rf_year_built")
		arcpy.AlterField_management(joinFN, "ADDRESS", "rf_address")
		arcpy.AlterField_management(joinFN, "x", "p_x") # this is from the parcel centroid
		arcpy.AlterField_management(joinFN, "y", "p_y") # this is from the parcel centroid
		arcpy.AlterField_management(joinFN, "geom_id", "p_geom_id") # this is from the parcel
		arcpy.AlterField_management(joinFN, "parcel_id", "rf_parcel_id") 
	
		# add fields and calc values
		# full list development_projects_id,raw_id,building_name,site_name,action,scen0,scen1,
		# address,city,zip,county,x,y,geom_id,year_built,duration,building_type_id,building_type,building_sqft,non_residential_sqft,
		# residential_units,unit_ave_sqft,tenure,rent_type,stories,parking_spaces,Average Weighted Rent,rent_ave_sqft,rent_ave_unit,
		# last_sale_year,last_sale_price,source,edit_date,editor,version
		# AddField(in_table, field_name, field_type, {field_precision}, {field_scale}, {field_length}, {field_alias}, {field_is_nullable}, {field_is_required}, {field_domain})
		arcpy.AddField_management(joinFN, "development_projects_id", "LONG")
		arcpy.AddField_management(joinFN, "raw_id", "LONG")
		arcpy.AddField_management(joinFN, "building_name", "TEXT","","",200)
		arcpy.AddField_management(joinFN, "site_name", "TEXT","","",200)
		arcpy.AddField_management(joinFN, "PARCEL_ID", "LONG")
		arcpy.AddField_management(joinFN, "action", "TEXT","","",10)
		arcpy.AddField_management(joinFN, "scen0", "SHORT")
		arcpy.AddField_management(joinFN, "scen1", "SHORT")
		arcpy.AddField_management(joinFN, "scen2", "SHORT")
		arcpy.AddField_management(joinFN, "scen3", "SHORT")
		arcpy.AddField_management(joinFN, "scen4", "SHORT")
		arcpy.AddField_management(joinFN, "scen5", "SHORT")
		arcpy.AddField_management(joinFN, "scen6", "SHORT")
		arcpy.AddField_management(joinFN, "scen7", "SHORT")
		arcpy.AddField_management(joinFN, "scen10", "SHORT")
		arcpy.AddField_management(joinFN, "scen11", "SHORT")
		arcpy.AddField_management(joinFN, "scen12", "SHORT")
		arcpy.AddField_management(joinFN, "scen15", "SHORT")
		arcpy.AddField_management(joinFN, "scen20", "SHORT")
		arcpy.AddField_management(joinFN, "scen21", "SHORT")
		arcpy.AddField_management(joinFN, "scen22", "SHORT")
		arcpy.AddField_management(joinFN, "scen23", "SHORT")
		arcpy.AddField_management(joinFN, "scen24", "SHORT")
		arcpy.AddField_management(joinFN, "scen25", "SHORT")  
		arcpy.AddField_management(joinFN, "address", "TEXT","","",200)
		arcpy.AddField_management(joinFN, "city", "TEXT","","",50)
		arcpy.AddField_management(joinFN, "zip", "TEXT","","",50)
		arcpy.AddField_management(joinFN, "county", "TEXT","","",50)
		arcpy.AddField_management(joinFN, "x", "FLOAT")
		arcpy.AddField_management(joinFN, "y", "FLOAT")
		arcpy.AddField_management(joinFN, "geom_id", "DOUBLE")
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
		arcpy.AddField_management(joinFN, "deed_restricted_units", "SHORT")
		arcpy.AddField_management(joinFN, "source", "TEXT","","",15)
		arcpy.AddField_management(joinFN, "edit_date", "LONG")
		arcpy.AddField_management(joinFN, "editor", "TEXT","","",50)
		arcpy.AddField_management(joinFN, "version", "SHORT")
		if not arcpy.ListFields(joinFN, "incl"):
			arcpy.AddField_management(joinFN, "incl", "SHORT")
	
		arcpy.CalculateField_management(joinFN, "raw_id", '!redfinid!')
		arcpy.CalculateField_management(joinFN, "action", "'build'")
		arcpy.CalculateField_management(joinFN, "PARCEL_ID", '!rf_parcel_id!')
		arcpy.CalculateField_management(joinFN, "scen0", 1)
		arcpy.CalculateField_management(joinFN, "scen1", 1)
		arcpy.CalculateField_management(joinFN, "scen2", 1)
		arcpy.CalculateField_management(joinFN, "scen3", 1)
		arcpy.CalculateField_management(joinFN, "scen4", 1)
		arcpy.CalculateField_management(joinFN, "scen5", 1)
		arcpy.CalculateField_management(joinFN, "scen6", 1)
		arcpy.CalculateField_management(joinFN, "scen7", 1)
		arcpy.CalculateField_management(joinFN, "scen10", 1)
		arcpy.CalculateField_management(joinFN, "scen11", 1)
		arcpy.CalculateField_management(joinFN, "scen12", 1)
		arcpy.CalculateField_management(joinFN, "scen15", 1)
		arcpy.CalculateField_management(joinFN, "scen20", 1)
		arcpy.CalculateField_management(joinFN, "scen21", 1)
		arcpy.CalculateField_management(joinFN, "scen22", 1)
		arcpy.CalculateField_management(joinFN, "scen23", 1)
		arcpy.CalculateField_management(joinFN, "scen24", 1)
		arcpy.CalculateField_management(joinFN, "scen25", 1)  # these are committed so 1 for all scens 
		arcpy.CalculateField_management(joinFN, "address", '!rf_address!')
		arcpy.CalculateField_management(joinFN, "city", '!rf_city!')
		arcpy.CalculateField_management(joinFN, "county", '!rf_county!')
		arcpy.CalculateField_management(joinFN, "x", '!p_x!') 
		arcpy.CalculateField_management(joinFN, "y", '!p_y!') 
		arcpy.CalculateField_management(joinFN, "geom_id", '!p_geom_id!')
		arcpy.CalculateField_management(joinFN, "year_built", '!rf_year_built!')
		if 'sfr' in arcpy.Describe(fc).name:
			arcpy.CalculateField_management(joinFN, "building_type", "'HS'")
		else:
			arcpy.CalculateField_management(joinFN, "building_type", "'HM'")
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
		arcpy.CalculateField_management(joinFN, "deed_restricted_units", 0)
		arcpy.CalculateField_management(joinFN, "source", "'rf'")
		arcpy.CalculateField_management(joinFN, "edit_date", 20200429)
		arcpy.CalculateField_management(joinFN, "editor", "'MKR'")
		
		#remove row where incl != 1
		with arcpy.da.UpdateCursor(joinFN, "incl") as cursor:
			for row in cursor:
				if row[0] != 1:
					cursor.deleteRow()
	
		countTwo = countRow(joinFN)
		if countTwo == countOne:
			logger.info("All records with incl = 1 in feature class {} are included in the temp file".format(fc))
		else:
			logger.fatal("Something is wrong in the code, please check")
			raise
	
		### 3 DELETE OTHER FIELDS AND TEMP FILES
		FCfields = [f.name for f in arcpy.ListFields(joinFN)]
		#add "rent_ave_sqft", "rent_ave_unit","version", "duration", "building_type_id" if needed
		DontDeleteFields = ["OBJECTID","Shape","development_projects_id", "raw_id", "building_name", "site_name",  "action", 
		"scen0", "scen1", "scen2", "scen3", "scen4", "scen5", "scen6", "scen7", "scen10", "scen11", "scen12", "scen15", "scen20", "scen21", "scen22", "scen23", "scen24", "scen25",
		"address",  "city",  "zip",  "county", "x", "y", "geom_id", "year_built","building_type", "building_sqft", "non_residential_sqft", "residential_units", "unit_ave_sqft", 
		"tenure", "rent_type", "stories", "parking_spaces", "average_weighted_rent", "last_sale_year", "last_sale_price", "deed_restricted_units","source", "PARCEL_ID", "ZONE_ID", "edit_date", "editor", "Shape_Length", "Shape_Area"]
		fields2Delete = list(set(FCfields) - set(DontDeleteFields))
		arcpy.DeleteField_management(joinFN, fields2Delete)

		gidnull = 'gidnull'
		arcpy.MakeTableView_management(joinFN,gidnull,"geom_id is NULL")
		nullcount = arcpy.GetCount_management(gidnull)
		logger.info("{} list has {} records with geom_id info missing".format(joinFN, nullcount))
		arcpy.Delete_management(gidnull)
		###4 REMOVE DUPLICATES
		#check again existing geomList and remove duplicates
		with arcpy.da.UpdateCursor(joinFN, "PARCEL_ID") as cursor:
			for row in cursor:
				if row[0] in geoList:
					cursor.deleteRow()
		#then add the geoms in the geomList
		gList = [row[0] for row in arcpy.da.SearchCursor(joinFN, 'PARCEL_ID')]
		for geo in gList:
			geoList.append(geo)
	
	
	### 5 MERGE ALL INCL=1 POINTS INTO A SINGLE SHP FILE CALLED PIPELINE
	#now let's get to the real full pipeline file
	pipeline_fc = "pipeline"
	logger.info("Merging feature classes {} into {}".format(dev_projects_temp_layers, pipeline_fc))

	#merge
	arcpy.Merge_management(dev_projects_temp_layers, pipeline_fc)
	count = arcpy.GetCount_management(pipeline_fc)
	logger.info("  Results in {} rows in {}".format(int(count[0]), pipeline_fc))


	### 6 MERGE OPPSITES SHP WITH PIPELINE TO GET DEVELOPMENT PROJECTS 
	#public sites
	joinFN = 'ttt_pubsites_p10_pba50'
	dev_projects_temp_layers.append(joinFN)
	
	try:
		count = arcpy.GetCount_management(joinFN)
		if int(count[0]) > 100:
			logger.info("Found layer {} with {} rows -- skipping creation".format(joinFN, int(count[0])))
	except:
		# go ahead and create it
		logger.info("Creating layer {} by spatial joining opp sites data ({}) and parcels ({})".format(joinFN, pub_sites, p10_pba50))
		arcpy.SpatialJoin_analysis(pub_sites, p10_pba50, joinFN)
		
		arcpy.AlterField_management(joinFN, "yearbuilt2", "p_year_built")
		arcpy.AlterField_management(joinFN, "new_units", "p_new_units")
		arcpy.AlterField_management(joinFN, "deed_res_1", "p_dr_units")
		arcpy.AlterField_management(joinFN, "non_resid_", "p_non_resid_")
		arcpy.AlterField_management(joinFN, "PARCEL_ID", "p_parcel_id")
		arcpy.AlterField_management(joinFN, "X", "p_x")
		arcpy.AlterField_management(joinFN, "Y", "p_y")
		arcpy.AlterField_management(joinFN, "GEOM_ID", "p_geom_id")

		arcpy.AddField_management(joinFN, "development_projects_id", "LONG")
		arcpy.AddField_management(joinFN, "building_name", "TEXT","","",200)
		arcpy.AddField_management(joinFN, "site_name", "TEXT","","",200)
		arcpy.AddField_management(joinFN, "PARCEL_ID", "LONG")
		arcpy.AddField_management(joinFN, "action", "TEXT","","",10)
		arcpy.AddField_management(joinFN, "raw_id", "LONG")
		arcpy.AddField_management(joinFN, "scen0", "SHORT")
		arcpy.AddField_management(joinFN, "scen1", "SHORT")
		arcpy.AddField_management(joinFN, "scen2", "SHORT")
		arcpy.AddField_management(joinFN, "scen3", "SHORT")
		arcpy.AddField_management(joinFN, "scen4", "SHORT")
		arcpy.AddField_management(joinFN, "scen5", "SHORT")
		arcpy.AddField_management(joinFN, "scen6", "SHORT")
		arcpy.AddField_management(joinFN, "scen7", "SHORT")
		arcpy.AddField_management(joinFN, "scen10", "SHORT")
		arcpy.AddField_management(joinFN, "scen11", "SHORT")
		arcpy.AddField_management(joinFN, "scen12", "SHORT")
		arcpy.AddField_management(joinFN, "scen15", "SHORT")
		arcpy.AddField_management(joinFN, "scen20", "SHORT")
		arcpy.AddField_management(joinFN, "scen21", "SHORT")
		arcpy.AddField_management(joinFN, "scen22", "SHORT")
		arcpy.AddField_management(joinFN, "scen23", "SHORT")
		arcpy.AddField_management(joinFN, "scen24", "SHORT")
		arcpy.AddField_management(joinFN, "scen25", "SHORT") 
		arcpy.AddField_management(joinFN, "address", "TEXT","","",200)
		arcpy.AddField_management(joinFN, "city", "TEXT","","",50)
		arcpy.AddField_management(joinFN, "zip", "TEXT","","",50)
		arcpy.AddField_management(joinFN, "county", "TEXT","","",50)
		arcpy.AddField_management(joinFN, "x", "FLOAT")
		arcpy.AddField_management(joinFN, "y", "FLOAT")
		arcpy.AddField_management(joinFN, "geom_id", "DOUBLE")
		arcpy.AddField_management(joinFN, "year_built", "SHORT")
		arcpy.AddField_management(joinFN, "duration", "SHORT")
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
		arcpy.AddField_management(joinFN, "last_sale_year", "DATE") 
		arcpy.AddField_management(joinFN, "last_sale_price", "DOUBLE")
		arcpy.AddField_management(joinFN, "deed_restricted_units", "SHORT")
		arcpy.AddField_management(joinFN, "edit_date", "LONG")
		arcpy.AddField_management(joinFN, "editor", "TEXT","","",50)
		arcpy.AddField_management(joinFN, "version", "SHORT")
		arcpy.AddField_management(joinFN, "source", "TEXT","","",15)
		
		# NOTE THAT OPPSITES HAS SCEN SET IN GIS FILE
		arcpy.CalculateField_management(joinFN, "PARCEL_ID", '!p_parcel_id!')
		arcpy.CalculateField_management(joinFN, "action", "'build'")
		arcpy.CalculateField_management(joinFN, "scen0", 0)
		arcpy.CalculateField_management(joinFN, "scen0", 0)
		arcpy.CalculateField_management(joinFN, "scen0", 0)
		arcpy.CalculateField_management(joinFN, "scen1", 0)
		arcpy.CalculateField_management(joinFN, "scen2", 0)
		arcpy.CalculateField_management(joinFN, "scen3", 0)
		arcpy.CalculateField_management(joinFN, "scen4", 0)
		arcpy.CalculateField_management(joinFN, "scen5", 0)
		arcpy.CalculateField_management(joinFN, "scen6", 0)
		arcpy.CalculateField_management(joinFN, "scen7", 0)
		arcpy.CalculateField_management(joinFN, "scen10", 0)
		arcpy.CalculateField_management(joinFN, "scen11", 0)
		arcpy.CalculateField_management(joinFN, "scen12", 0)
		arcpy.CalculateField_management(joinFN, "scen15", 0)
		arcpy.CalculateField_management(joinFN, "scen20", 0)
		arcpy.CalculateField_management(joinFN, "scen21", 0)
		arcpy.CalculateField_management(joinFN, "scen22", 0)
		arcpy.CalculateField_management(joinFN, "scen23", 0)
		arcpy.CalculateField_management(joinFN, "scen24", 1)
		arcpy.CalculateField_management(joinFN, "scen25", 0)
		arcpy.CalculateField_management(joinFN, "x", '!p_x!') 
		arcpy.CalculateField_management(joinFN, "y", '!p_y!') 
		arcpy.CalculateField_management(joinFN, "geom_id", '!p_geom_id!')
		arcpy.CalculateField_management(joinFN, "city", '!juris!')
		arcpy.CalculateField_management(joinFN, "year_built", '!p_year_built!')
		arcpy.CalculateField_management(joinFN, "building_type", "'HM'")
		arcpy.CalculateField_management(joinFN, "residential_units", '!p_new_units!')
		arcpy.CalculateField_management(joinFN, "deed_restricted_units", '!p_dr_units!')
		arcpy.CalculateField_management(joinFN, "non_residential_sqft", '!p_non_resid_!')
		arcpy.CalculateField_management(joinFN, "source", "'pub'")
		arcpy.CalculateField_management(joinFN, "edit_date", 20201028)
		arcpy.CalculateField_management(joinFN, "editor", "'MS'")
		
		FCfields = [f.name for f in arcpy.ListFields(joinFN)]
		#add "rent_ave_sqft", "rent_ave_unit","version", "duration", "building_type_id" if needed
		DontDeleteFields = ["OBJECTID","Shape","development_projects_id", "raw_id", "building_name", "site_name",  "action", 
		"scen0", "scen1", "scen2", "scen3", "scen4", "scen5", "scen6", "scen7", "scen10", "scen11", "scen12", "scen15", "scen20", "scen21", "scen22", "scen23", "scen24", "scen25",
		"address",  "city",  "zip",  "county", "x", "y", "geom_id", "year_built","building_type", "building_sqft", "non_residential_sqft", "residential_units", "unit_ave_sqft", 
		"tenure", "rent_type", "stories", "parking_spaces", "average_weighted_rent", "last_sale_year", "last_sale_price", "deed_restricted_units","source", "PARCEL_ID", "ZONE_ID", "edit_date", "editor", "Shape_Length", "Shape_Area"]
		fields2Delete = list(set(FCfields) - set(DontDeleteFields))
		arcpy.DeleteField_management(joinFN, fields2Delete)

		gidnull = 'gidnull'
		arcpy.MakeTableView_management(joinFN,gidnull,"geom_id is NULL")
		nullcount = arcpy.GetCount_management(gidnull)
		logger.info("{} list has {} records with geom_id info missing".format(joinFN, nullcount))
		arcpy.Delete_management(gidnull)
		###4 REMOVE DUPLICATES
		#check again existing geomList and remove duplicates
		with arcpy.da.UpdateCursor(joinFN, "PARCEL_ID") as cursor:
			for row in cursor:
				if row[0] in geoList:
					cursor.deleteRow()
		#then add the geoms in the geomList
		gList = [row[0] for row in arcpy.da.SearchCursor(joinFN, 'PARCEL_ID')]
		for geo in gList:
			geoList.append(geo)
	
	#opportunity sites
	joinFN = 'ttt_opp_p10_pba50'
	dev_projects_temp_layers.append(joinFN)
	
	try:
		count = arcpy.GetCount_management(joinFN)
		if int(count[0]) > 100:
			logger.info("Found layer {} with {} rows -- skipping creation".format(joinFN, int(count[0])))
	except:
		# go ahead and create it
		logger.info("Creating layer {} by spatial joining opp sites data ({}) and parcels ({})".format(joinFN, opp_sites, p10_pba50))
		arcpy.SpatialJoin_analysis(opp_sites, p10_pba50, joinFN)
		
		arcpy.AlterField_management(joinFN, "year_built", "o_year_built")
		arcpy.AlterField_management(joinFN, "last_sale_price", "o_last_sale_price")
		arcpy.AlterField_management(joinFN, "last_sale_year", "o_sale_date")
		arcpy.AlterField_management(joinFN, "stories", "o_stories")
		arcpy.AlterField_management(joinFN, "building_name", "o_building_name")
		arcpy.AlterField_management(joinFN, "site_name", "o_site_name")
		arcpy.AlterField_management(joinFN, "PARCEL_ID", "o_parcel_id")
		arcpy.AlterField_management(joinFN, "scen0", "o_scen0")
		arcpy.AlterField_management(joinFN, "scen1", "o_scen1")
		arcpy.AlterField_management(joinFN, "scen2", "o_scen2")
		arcpy.AlterField_management(joinFN, "scen3", "o_scen3")
		arcpy.AlterField_management(joinFN, "scen4", "o_scen4")
		arcpy.AlterField_management(joinFN, "scen5", "o_scen5")
		arcpy.AlterField_management(joinFN, "scen6", "o_scen6")
		arcpy.AlterField_management(joinFN, "scen7", "o_scen7")
		arcpy.AlterField_management(joinFN, "scen10", "o_scen10")
		arcpy.AlterField_management(joinFN, "scen11", "o_scen11")
		arcpy.AlterField_management(joinFN, "scen12", "o_scen12")
		arcpy.AlterField_management(joinFN, "scen15", "o_scen15")
		arcpy.AlterField_management(joinFN, "scen20", "o_scen20")
		arcpy.AlterField_management(joinFN, "scen21", "o_scen21")
		arcpy.AlterField_management(joinFN, "scen22", "o_scen22")
		arcpy.AlterField_management(joinFN, "scen23", "o_scen23")
		arcpy.AlterField_management(joinFN, "scen24", "o_scen24")
		arcpy.AlterField_management(joinFN, "scen25", "o_scen25")
		arcpy.AlterField_management(joinFN, "duration", "o_duration")
		arcpy.AlterField_management(joinFN, "parking_spaces", "o_parking_spaces")
		arcpy.AlterField_management(joinFN, "non_residential_sqft", "o_non_residential_sqft")
		arcpy.AlterField_management(joinFN, "building_sqft", "o_building_sqft")
		arcpy.AlterField_management(joinFN, "residential_units", "o_residential_units")
		arcpy.AlterField_management(joinFN, "unit_ave_sqft", "o_unit_ave_sqft")
		arcpy.AlterField_management(joinFN, "rent_ave_sqft", "o_rent_ave_sqft")
		arcpy.AlterField_management(joinFN, "zip", "o_zips")
		arcpy.AlterField_management(joinFN, "Average_Weighted_Rent", "average_weighted_rent")
		arcpy.AlterField_management(joinFN, "x", "o_x")
		arcpy.AlterField_management(joinFN, "y", "o_y")
		arcpy.AlterField_management(joinFN, "geom_id", "o_geom_id")
		arcpy.AlterField_management(joinFN, "geom_id_s", "o_geom_id2")
		arcpy.AlterField_management(joinFN, "source", "o_source")

		arcpy.AddField_management(joinFN, "development_projects_id", "LONG")
		arcpy.AddField_management(joinFN, "building_name", "TEXT","","",200)
		arcpy.AddField_management(joinFN, "site_name", "TEXT","","",200)
		arcpy.AddField_management(joinFN, "PARCEL_ID", "LONG")
		arcpy.AddField_management(joinFN, "raw_id", "LONG")
		arcpy.AddField_management(joinFN, "scen0", "SHORT")
		arcpy.AddField_management(joinFN, "scen1", "SHORT")
		arcpy.AddField_management(joinFN, "scen2", "SHORT")
		arcpy.AddField_management(joinFN, "scen3", "SHORT")
		arcpy.AddField_management(joinFN, "scen4", "SHORT")
		arcpy.AddField_management(joinFN, "scen5", "SHORT")
		arcpy.AddField_management(joinFN, "scen6", "SHORT")
		arcpy.AddField_management(joinFN, "scen7", "SHORT")
		arcpy.AddField_management(joinFN, "scen10", "SHORT")
		arcpy.AddField_management(joinFN, "scen11", "SHORT")
		arcpy.AddField_management(joinFN, "scen12", "SHORT")
		arcpy.AddField_management(joinFN, "scen15", "SHORT")
		arcpy.AddField_management(joinFN, "scen20", "SHORT")
		arcpy.AddField_management(joinFN, "scen21", "SHORT")
		arcpy.AddField_management(joinFN, "scen22", "SHORT")
		arcpy.AddField_management(joinFN, "scen23", "SHORT")
		arcpy.AddField_management(joinFN, "scen24", "SHORT")
		arcpy.AddField_management(joinFN, "scen25", "SHORT") 
		arcpy.AddField_management(joinFN, "zip", "TEXT","","",50)
		arcpy.AddField_management(joinFN, "x", "FLOAT")
		arcpy.AddField_management(joinFN, "y", "FLOAT")
		arcpy.AddField_management(joinFN, "geom_id", "DOUBLE")
		arcpy.AddField_management(joinFN, "year_built", "SHORT")
		arcpy.AddField_management(joinFN, "duration", "SHORT")
		arcpy.AddField_management(joinFN, "building_sqft", "LONG")
		arcpy.AddField_management(joinFN, "non_residential_sqft", "LONG")
		arcpy.AddField_management(joinFN, "residential_units", "SHORT")
		arcpy.AddField_management(joinFN, "unit_ave_sqft", "FLOAT")
		arcpy.AddField_management(joinFN, "stories", "SHORT")
		arcpy.AddField_management(joinFN, "parking_spaces", "SHORT")
		arcpy.AddField_management(joinFN, "rent_ave_sqft", "FLOAT")
		###using date for now, as I tried to use datetime.datetime.strptime('cs_sale_date','%m/%d/%Y %I:%M:%S %p').strftime('%Y')) it didn't work
		arcpy.AddField_management(joinFN, "edit_date", "LONG")
		arcpy.AddField_management(joinFN, "editor", "TEXT","","",50)
		arcpy.AddField_management(joinFN, "version", "SHORT")
		arcpy.AddField_management(joinFN, "source", "TEXT","","",15)
		# NOTE THAT OPPSITES HAS SCEN SET IN GIS FILE
		arcpy.CalculateField_management(joinFN, "raw_id", "!opp_id!")
		arcpy.CalculateField_management(joinFN, "building_name", "!o_building_name!")
		arcpy.CalculateField_management(joinFN, "site_name", "!o_site_name!")
		arcpy.CalculateField_management(joinFN, "PARCEL_ID", '!o_parcel_id!')
		arcpy.CalculateField_management(joinFN, "scen0", "!o_scen0!")
		arcpy.CalculateField_management(joinFN, "scen0", "!o_scen0!")
		arcpy.CalculateField_management(joinFN, "scen0", "!o_scen0!")
		arcpy.CalculateField_management(joinFN, "scen1", "!o_scen1!")
		arcpy.CalculateField_management(joinFN, "scen2", "!o_scen2!")
		arcpy.CalculateField_management(joinFN, "scen3", "!o_scen3!")
		arcpy.CalculateField_management(joinFN, "scen4", "!o_scen4!")
		arcpy.CalculateField_management(joinFN, "scen5", "!o_scen5!")
		arcpy.CalculateField_management(joinFN, "scen6", "!o_scen6!")
		arcpy.CalculateField_management(joinFN, "scen7", "!o_scen7!")
		arcpy.CalculateField_management(joinFN, "scen10", "!o_scen10!")
		arcpy.CalculateField_management(joinFN, "scen11", "!o_scen11!")
		arcpy.CalculateField_management(joinFN, "scen12", "!o_scen12!")
		arcpy.CalculateField_management(joinFN, "scen15", "!o_scen15!")
		arcpy.CalculateField_management(joinFN, "scen20", "!o_scen20!")
		arcpy.CalculateField_management(joinFN, "scen21", "!o_scen21!")
		arcpy.CalculateField_management(joinFN, "scen22", "!o_scen22!")
		arcpy.CalculateField_management(joinFN, "scen23", "!o_scen23!")
		arcpy.CalculateField_management(joinFN, "scen24", "!o_scen23!")
		arcpy.CalculateField_management(joinFN, "scen25", 0)
		arcpy.CalculateField_management(joinFN, "x", '!X_1!') 
		arcpy.CalculateField_management(joinFN, "y", '!Y_1!') 
		arcpy.CalculateField_management(joinFN, "geom_id", '!o_geom_id2!')
		arcpy.CalculateField_management(joinFN, "year_built", '!o_year_built!')
		arcpy.CalculateField_management(joinFN, "building_sqft", '!o_building_sqft!')
		arcpy.CalculateField_management(joinFN, "non_residential_sqft", '!o_non_residential_sqft!')
		arcpy.CalculateField_management(joinFN, "residential_units", '!o_residential_units!')
		arcpy.CalculateField_management(joinFN, "unit_ave_sqft", '!o_unit_ave_sqft!')
		with arcpy.da.UpdateCursor(joinFN, ["source","type","building_name","o_source"]) as cursor:
			for row in cursor:
				if row[2] == 'incubator':
					row[0] = row[2]
				elif row[1] == 'pb50_opp':
					row[0] = 'mall_office'
				elif row[3] == 'ppa':
					row[0] = row[3]
				else:
					row[0] = 'opp'
				cursor.updateRow(row)
		arcpy.CalculateField_management(joinFN, "edit_date", 20200611)
		arcpy.CalculateField_management(joinFN, "editor", "'MKR'")
		
		FCfields = [f.name for f in arcpy.ListFields(joinFN)]
		#add "rent_ave_sqft", "rent_ave_unit","version", "duration", "building_type_id" if needed
		DontDeleteFields = ["OBJECTID","Shape","development_projects_id", "raw_id", "building_name", "site_name",  "action", 
		"scen0", "scen1", "scen2", "scen3", "scen4", "scen5", "scen6", "scen7", "scen10", "scen11", "scen12", "scen15", "scen20", "scen21", "scen22", "scen23", "scen24", "scen25",
		"address",  "city",  "zip",  "county", "x", "y", "geom_id", "year_built","building_type", "building_sqft", "non_residential_sqft", "residential_units", "unit_ave_sqft", 
		"tenure", "rent_type", "stories", "parking_spaces", "average_weighted_rent", "last_sale_year", "last_sale_price", "deed_restricted_units","source", "PARCEL_ID", "ZONE_ID", "edit_date", "editor", "Shape_Length", "Shape_Area"]
		fields2Delete = list(set(FCfields) - set(DontDeleteFields))
		arcpy.DeleteField_management(joinFN, fields2Delete)

		gidnull = 'gidnull'
		arcpy.MakeTableView_management(joinFN,gidnull,"geom_id is NULL")
		nullcount = arcpy.GetCount_management(gidnull)
		logger.info("{} list has {} records with geom_id info missing".format(joinFN, nullcount))
		arcpy.Delete_management(gidnull)
		###4 REMOVE DUPLICATES
		#check again existing geomList and remove duplicates
		with arcpy.da.UpdateCursor(joinFN, "PARCEL_ID") as cursor:
			for row in cursor:
				if row[0] in geoList:
					cursor.deleteRow()
		#then add the geoms in the geomList
		gList = [row[0] for row in arcpy.da.SearchCursor(joinFN, 'PARCEL_ID')]
		for geo in gList:
			geoList.append(geo)
	
	#not going to check duplicates, since opp sites should not duplicate

	#all non opp sites should be in the list dev_projects_temp_layers already
	devproj_fc = "development_project"
	logger.info("Merging feature classes {} into {}".format(dev_projects_temp_layers, devproj_fc))
	
	arcpy.Merge_management(dev_projects_temp_layers, devproj_fc)
	count = arcpy.GetCount_management(devproj_fc)
	logger.info("  Results in {} rows in {}".format(int(count[0]), devproj_fc))
	
	#assign unique incremental development_id
	i = 1
	with arcpy.da.UpdateCursor(devproj_fc, "development_projects_id") as cursor:
			for row in cursor:
				if i <= int(count[0]) :
					row[0] = i
					i  = i + 1
					cursor.updateRow(row)
	
	# it's no longer necessary to delete temporary spatial join layers since they're in the temporary WORKSPACE_GDB

	#update mapping of building types from detailed to simplified in both pipeline 
	arcpy.AlterField_management(pipeline_fc, "building_type", "building_type_det","building_type_det")
	arcpy.AddField_management(pipeline_fc, "building_type", "TEXT","","","800")
	arcpy.AddField_management(pipeline_fc, "building_type_id", "LONG")
	arcpy.AddField_management(pipeline_fc, "development_type_id", "LONG")

	with arcpy.da.UpdateCursor(pipeline_fc, ['building_type_det', "building_type","building_type_id", 'development_type_id']) as cursor:
				for row in cursor:
					if row[0] == 'HS':
						row[1] = 'HS'
						row[2] = 1
						row[3] = 1
					elif row[0] == 'HT':
						row[1] = 'HT'
						row[2] = 2
						row[3] = 2
					elif row[0] == 'HM':
						row[1] = 'HM'
						row[2] = 3
						row[3] = 2
					elif row[0] == 'MH':
						row[1] = 'HM'
						row[2] = 3
						row[3] = 4
					elif row[0] == 'SR':
						row[1] = 'HM'
						row[2] = 3
						row[3] = 2
					elif row[0] == 'AL':
						row[1] = 'GQ'
						row[2] = 3
						row[3] = 6
					elif row[0] == 'DM':
						row[1] = 'GQ'
						row[2] = 3
						row[3] = 6
					elif row[0] == 'CM':
						row[1] = 'HM'
						row[2] = 3
						row[3] = 2
					elif row[0] == 'OF':
						row[1] = 'OF'
						row[2] = 4
						row[3] = 10
					elif row[0] == 'GV':
						row[1] = 'OF'
						row[2] = 4
						row[3] = 10
					elif row[0] == 'HP':
						row[1] = 'OF'
						row[2] = 4
						row[3] = 10
					elif row[0] == 'HO':
						row[1] = 'HO'
						row[2] = 5
						row[3] = 9
					elif row[0] == 'SC':
						row[1] = 'SC'
						row[2] = 6
						row[3] = 17
					elif row[0] == 'UN':
						row[1] = 'SC'
						row[2] = 6
						row[3] = 18
					elif row[0] == 'IL':
						row[1] = 'IL'
						row[2] = 7
						row[2] = 14
					elif row[0] == 'FP':
						row[1] = 'IL'
						row[2] = 7
						row[2] = 14
					elif row[0] == 'IW':
						row[1] = 'IW'
						row[2] = 8
						row[3] = 13
					elif row[0] == 'IH':
						row[1] = 'IH'
						row[2] = 9
						row[3] = 15
					elif row[0] == 'RS':
						row[1] = 'RS'
						row[2] = 10
						row[3] = 7
					elif row[0] == 'RB':
						row[1] = 'RB'
						row[2] = 11
						row[3] = 8
					elif row[0] == 'MR':
						row[1] = 'MR'
						row[2] = 12
						row[3] = 5
					elif row[0] == 'MT':
						row[1] = 'MT'
						row[2] = 12
					elif row[0] == 'ME':
						row[1] = 'ME'
						row[2] = 14
						row[3] = 11
					elif row[0] == 'PA':
						row[1] = 'VA'
						row[2] = 15
						row[3] = 23
					elif row[0] == 'PG':
						row[1] = 'PG'
						row[2] = 16
						row[3] = 22
					elif row[0] == 'VA':
						row[1] = 'VA'
						row[2] = 0
						row[3] = 21
					elif row[0] == 'LR':
						row[1] = 'RS'
						row[2] = 10
						row[3] = 7
					elif row[0] == 'VP':
						row[1] = 'VP'
						row[2] = 0
						row[3] = 20
					elif row[0] == 'OT':
						row[1] = 'OT'
						row[2] = 0
					elif row[0] == 'IN':
						row[1] = 'OF'
						row[2] = 4
						row[3] = 10
					elif row[0] == 'RF':
						row[1] = 'RS'
						row[2] = 10
						row[3] = 7
					elif row[0] == 'GQ':
						row[1] = 'GQ'
						row[2] = 3
						row[3] = 6
					cursor.updateRow(row)

	## count missing value
	btnull = 'btnull' ##stands for building type null
	arcpy.MakeTableView_management(pipeline_fc,btnull,"building_type is NULL")
	nullcount = arcpy.GetCount_management(btnull)
	logger.info("Pipeline list has {} records with building type info missing".format(nullcount))
	arcpy.Delete_management(btnull)

	arcpy.AlterField_management(pipeline_fc, 'building_sqft','temp_building_sqft')
	arcpy.AddField_management(pipeline_fc, 'building_sqft',"LONG")
	arcpy.SelectLayerByAttribute_management(pipeline_fc, "NEW_SELECTION",'"residential_units">0')
	arcpy.SelectLayerByAttribute_management(pipeline_fc, "SUBSET_SELECTION",'"non_residential_sqft" = "temp_building_sqft"')
	arcpy.SelectLayerByAttribute_management(pipeline_fc, "SUBSET_SELECTION",'"building_type_id" = 3') #HM
	arcpy.CalculateField_management(pipeline_fc, "building_sqft","!residential_units! * 1400 + !temp_building_sqft! ", "PYTHON")

	arcpy.SelectLayerByAttribute_management(pipeline_fc, "NEW_SELECTION",'"residential_units">0')
	arcpy.SelectLayerByAttribute_management(pipeline_fc, "SUBSET_SELECTION",'"non_residential_sqft" = "temp_building_sqft"')
	arcpy.SelectLayerByAttribute_management(pipeline_fc, "SUBSET_SELECTION",'"building_type_id" = 12') #MR
	arcpy.CalculateField_management(pipeline_fc, "building_sqft","!residential_units! * 1400 + !temp_building_sqft! ", "PYTHON")

	arcpy.SelectLayerByAttribute_management(pipeline_fc, "NEW_SELECTION",'"building_sqft" is NULL ')
	arcpy.CalculateField_management(pipeline_fc, "building_sqft","!temp_building_sqft!", "PYTHON")
	arcpy.SelectLayerByAttribute_management(pipeline_fc, "CLEAR_SELECTION")

	arcpy.DeleteField_management(pipeline_fc, 'temp_building_sqft')

    #same process for development project list
	arcpy.AlterField_management(devproj_fc, "building_type", "building_type_det","building_type_det")
	arcpy.AddField_management(devproj_fc, "building_type", "TEXT","","","800")
	arcpy.AddField_management(devproj_fc, "building_type_id", "LONG")
	arcpy.AddField_management(devproj_fc, "development_type_id", "LONG")

	with arcpy.da.UpdateCursor(devproj_fc, ['building_type_det', "building_type","building_type_id", 'development_type_id']) as cursor:
				for row in cursor:
					if row[0] == 'HS':
						row[1] = 'HS'
						row[2] = 1
						row[3] = 1
					elif row[0] == 'HT':
						row[1] = 'HT'
						row[2] = 2 
						row[3] = 2
					elif row[0] == 'HM':
						row[1] = 'HM'
						row[2] = 3
						row[3] = 2
					elif row[0] == 'MH':
						row[1] = 'HM'
						row[2] = 3
						row[3] = 4
					elif row[0] == 'SR':
						row[1] = 'HM'
						row[2] = 3
						row[3] = 2
					elif row[0] == 'AL':
						row[1] = 'GQ'
						row[2] = 3
						row[3] = 6
					elif row[0] == 'DM':
						row[1] = 'GQ'
						row[2] = 3
						row[3] = 6
					elif row[0] == 'CM':
						row[1] = 'HM'
						row[2] = 3
						row[3] = 2
					elif row[0] == 'OF':
						row[1] = 'OF'
						row[2] = 4
						row[3] = 10
					elif row[0] == 'GV':
						row[1] = 'OF'
						row[2] = 4
						row[3] = 10
					elif row[0] == 'HP':
						row[1] = 'OF'
						row[2] = 4
						row[3] = 10
					elif row[0] == 'HO':
						row[1] = 'HO'
						row[2] = 5
						row[3] = 9
					elif row[0] == 'SC':
						row[1] = 'SC'
						row[2] = 6
						row[3] = 17
					elif row[0] == 'UN':
						row[1] = 'SC'
						row[2] = 6
						row[3] = 18
					elif row[0] == 'IL':
						row[1] = 'IL'
						row[2] = 7
						row[2] = 14
					elif row[0] == 'FP':
						row[1] = 'IL'
						row[2] = 7
						row[2] = 14
					elif row[0] == 'IW':
						row[1] = 'IW'
						row[2] = 8
						row[3] = 13
					elif row[0] == 'IH':
						row[1] = 'IH'
						row[2] = 9
						row[3] = 15
					elif row[0] == 'RS':
						row[1] = 'RS'
						row[2] = 10
						row[3] = 7
					elif row[0] == 'RB':
						row[1] = 'RB'
						row[2] = 11
						row[3] = 8
					elif row[0] == 'MR':
						row[1] = 'MR'
						row[2] = 12
						row[3] = 5
					elif row[0] == 'MT':
						row[1] = 'MT'
						row[2] = 12
					elif row[0] == 'ME':
						row[1] = 'ME'
						row[2] = 14
						row[3] = 11
					elif row[0] == 'PA':
						row[1] = 'VA'
						row[2] = 15
						row[3] = 23
					elif row[0] == 'PG':
						row[1] = 'PG'
						row[2] = 16
						row[3] = 22
					elif row[0] == 'VA':
						row[1] = 'VA'
						row[2] = 0
						row[3] = 21
					elif row[0] == 'LR':
						row[1] = 'RS'
						row[2] = 10
						row[3] = 7
					elif row[0] == 'VP':
						row[1] = 'VP'
						row[2] = 0
						row[3] = 20
					elif row[0] == 'OT':
						row[1] = 'OT'
						row[2] = 0
					elif row[0] == 'IN':
						row[1] = 'OF'
						row[2] = 4
						row[3] = 10
					elif row[0] == 'RF':
						row[1] = 'RS'
						row[2] = 10
						row[3] = 7
					elif row[0] == 'GQ':
						row[1] = 'GQ'
						row[2] = 3
						row[3] = 6
					cursor.updateRow(row)
	## count missing value
	btnull = 'btnull' ##stands for building type null
	arcpy.MakeTableView_management(devproj_fc,btnull,"building_type is NULL")
	nullcount = arcpy.GetCount_management(btnull)
	logger.info("Development Project list has {} records with building type info missing".format(nullcount))
	arcpy.Delete_management(btnull)


	arcpy.AlterField_management(devproj_fc, 'building_sqft','temp_building_sqft')
	arcpy.AddField_management(devproj_fc, 'building_sqft',"LONG")
	arcpy.SelectLayerByAttribute_management(devproj_fc, "NEW_SELECTION",'"residential_units">0')
	arcpy.SelectLayerByAttribute_management(devproj_fc, "SUBSET_SELECTION",'"non_residential_sqft" = "temp_building_sqft"')
	arcpy.SelectLayerByAttribute_management(devproj_fc, "SUBSET_SELECTION",'"building_type_id" = 3') #HM
	arcpy.CalculateField_management(devproj_fc, "building_sqft","!residential_units! * 1400 + !temp_building_sqft! ", "PYTHON")

	arcpy.SelectLayerByAttribute_management(devproj_fc, "NEW_SELECTION",'"residential_units">0')
	arcpy.SelectLayerByAttribute_management(devproj_fc, "SUBSET_SELECTION",'"non_residential_sqft" = "temp_building_sqft"')
	arcpy.SelectLayerByAttribute_management(devproj_fc, "SUBSET_SELECTION",'"building_type_id" = 12') #MR
	arcpy.CalculateField_management(devproj_fc, "building_sqft","!residential_units! * 1400 + !temp_building_sqft! ", "PYTHON")

	arcpy.SelectLayerByAttribute_management(devproj_fc, "NEW_SELECTION",'"building_sqft" is NULL ')
	arcpy.CalculateField_management(devproj_fc, "building_sqft","!temp_building_sqft!", "PYTHON")
	arcpy.SelectLayerByAttribute_management(devproj_fc, "CLEAR_SELECTION")

	arcpy.DeleteField_management(devproj_fc, 'temp_building_sqft')

	# 6 DIAGNOSTICS
	#number of units total by year
	arcpy.Statistics_analysis(devproj_fc, 'res_stats_y', [["residential_units", "SUM"]], "year_built")
	#then calculate the total 
	arcpy.Statistics_analysis(devproj_fc, 'res_stats_a', [["residential_units", "SUM"]])
	#get the total result and write into log
	cursor = arcpy.SearchCursor('res_stats_a','','', 'SUM_residential_units')
	row = cursor.next()
	sum_value = row.getValue('SUM_residential_units')
	logger.info("Total number of residential units in {} file: {:,} units".format(devproj_fc, int(sum_value)))
	
	#number of nonres sqft by year
	arcpy.Statistics_analysis(devproj_fc, 'nonres_stats_y', [["non_residential_sqft", "SUM"]], "year_built")
	#then calculate the total 
	arcpy.Statistics_analysis(devproj_fc, 'nonres_stats_a', [["non_residential_sqft", "SUM"]])
	#get the total result and write into log
	cursor = arcpy.SearchCursor('nonres_stats_a','','', 'SUM_non_residential_sqft')
	row = cursor.next()
	sum_value = row.getValue('SUM_non_residential_sqft')
	logger.info("Total number of non residential square footage in {}: {:,} square feet".format(devproj_fc, int(sum_value)))
	
	#count parcels with more than one points on them - pipeline
	#first, there is no development projects id for them, so set value for that
	count = arcpy.GetCount_management(pipeline_fc)
	i = 1
	with arcpy.da.UpdateCursor(pipeline_fc, "development_projects_id") as cursor:
			for row in cursor:
				if i <= int(count[0]) :
					row[0] = i
					i  = i + 1
					cursor.updateRow(row)
	
	p_pipeline = "p_pipeline"
	arcpy.Statistics_analysis(pipeline_fc, p_pipeline, [["development_projects_id", "COUNT"]], "geom_id")
	#there are projects with geom_id null, so in order to count, delete those first
	with arcpy.da.UpdateCursor(p_pipeline, "geom_id") as cursor:
		for row in cursor:
			if row[0] is None:
				cursor.deleteRow()	
	
	ppCount = "ppCount"
	arcpy.MakeTableView_management(p_pipeline,ppCount,"COUNT_development_projects_id > 1")
	countParcelP = arcpy.GetCount_management(ppCount)
	logger.info("There are {} of parcels with multiple project points (more than 1) on them in the pipeline file".format(countParcelP))
	
	#count parcels with more than one points on them - development projects
	p_dev = "p_dev"
	arcpy.Statistics_analysis(devproj_fc, p_dev, [["development_projects_id", "COUNT"]], "geom_id")
	#there are projects with geom_id null, so in order to count, delete those first
	with arcpy.da.UpdateCursor(p_dev, "geom_id") as cursor:
		for row in cursor:
			if row[0] is None:
				cursor.deleteRow()	
	
	pdCount = "pdCount"
	arcpy.MakeTableView_management(p_dev,pdCount,"COUNT_development_projects_id > 1")
	countParcelD = arcpy.GetCount_management(pdCount)
	logger.info("There are {} of parcels with multiple project points (more than 1) on them".format(countParcelD))
	
	# 7 BUILDINGS TO ADD INSTEAD OF BUILD
	# change a short list of activity to add
	# first doing it for the pipeline file
	pList_pipeline= [row[0] for row in arcpy.da.SearchCursor(ppCount, 'geom_id')]
	if  "8016918253805" not in pList_pipeline:
		pList_pipeline.append('8016918253805')
	if "9551692992638" not in pList_pipeline:
		pList_pipeline.append('9551692992638')
	with arcpy.da.UpdateCursor(pipeline_fc, ["geom_id","action"]) as cursor:
	    		for row in cursor:
	    			if row[0] in pList_pipeline: 
	    				row[1] = 'add'
	    				cursor.updateRow(row)
	# second doing it for the development project file
	pList_dev= [row[0] for row in arcpy.da.SearchCursor(pdCount, 'geom_id')]
	if  "8016918253805" not in pList_pipeline:
		pList_dev.append('8016918253805')
	if "9551692992638" not in pList_pipeline:
		pList_dev.append('9551692992638')
	with arcpy.da.UpdateCursor(devproj_fc, ["geom_id","action"]) as cursor:
	    		for row in cursor:
	    			if row[0] in pList_dev: 
	    				row[1] = 'add'
	    				cursor.updateRow(row)

	# change NaNs in non_residential_sqft to 0
	with arcpy.da.UpdateCursor(pipeline_fc, "non_residential_sqft") as cursor:
		for row in cursor:
			if row[0] is None:
				row[0] = 0
				cursor.updateRow(row)

	with arcpy.da.UpdateCursor(devproj_fc, "non_residential_sqft") as cursor:
		for row in cursor:
			if row[0] is None:
				row[0] = 0
				cursor.updateRow(row)

	#reordering before making the output
	new_field_order = ["OBJECTID","Shape","development_projects_id", "raw_id", "building_name", "site_name",  "action", 
		"scen0", "scen1", "scen2", "scen3", "scen4", "scen5", "scen6", "scen7", "scen10", "scen11", "scen12", "scen15", "scen20", "scen21", "scen22", "scen23", "scen24", "scen25",
		"address",  "city",  "zip",  "county", "x", "y", "geom_id", "year_built","building_type_det","building_type", "building_type_id","development_type_id", "building_sqft", "non_residential_sqft", "residential_units", "unit_ave_sqft", 
		"tenure", "rent_type", "stories", "parking_spaces", "average_weighted_rent", "last_sale_year", "last_sale_price", "deed_restricted_units","source", "PARCEL_ID", "ZONE_ID", "edit_date", "editor"]
	pipeline_fc_reordered = 'pipeline_reordered'
	devproj_fc_reordered = 'devproj_reordered'
	reorder_fields(pipeline_fc, pipeline_fc_reordered, new_field_order)
	reorder_fields(devproj_fc, devproj_fc_reordered, new_field_order)

	#we are only keeping one set of data. move this blolock of code to the end
	#export csv to folder -- remember to change fold path when run on other machines
	pipeline_output = "{}_pipeline.csv".format(NOW)
	arcpy.TableToTable_conversion(pipeline_fc_reordered, WORKING_DIR, pipeline_output)
	logger.info("Wrote {}".format(os.path.join(WORKING_DIR,pipeline_output)))
	
	development_project_output = "{}_development_projects.csv".format(NOW)
	arcpy.TableToTable_conversion(devproj_fc_reordered, WORKING_DIR, development_project_output)
	logger.info("Wrote {}".format(os.path.join(WORKING_DIR,development_project_output)))

	#long_cols that were cutoff are 'development_proj', 'non_residential_', 'development_type' , 'deed_restricted_'
	pipeline_df = pd.read_csv(os.path.join(WORKING_DIR, pipeline_output))
	pipeline_df = pipeline_df.rename(columns = {'development_proj' : 'development_projects_id',
											'non_residential_' : 'non_residential_sqft',
											'development_type' : 'development_type_id',
											'average_weighted' : 'average_weighted_rent',
											'building_type_de' : 'building_type_det',
											'residential_unit' : 'residential_units',

											'deed_restricted_' : 'deed_restricted_units'})
	development_project_df = pd.read_csv(os.path.join(WORKING_DIR, development_project_output))
	development_project_df = development_project_df.rename(columns = {'development_proj' : 'development_projects_id',
											'non_residential_' : 'non_residential_sqft',
											'development_type' : 'development_type_id',
											'residential_unit' : 'residential_units',
											'average_weighted' : 'average_weighted_rent',
											'building_type_de' : 'building_type_det',											
											'deed_restricted_' : 'deed_restricted_units'})
	#fix int column problem in csv
	field_types = {"OBJECTID" : "int",
					"development_projects_id":"int",
					"raw_id": "int",
					"scen0": "int",
					"scen1": "int",
					"scen2": "int",
					"scen3": "int",
					"scen4": "int",
					"scen5": "int",
					"scen6": "int",
					"scen7": "int",
					"scen10": "int",
					"scen11": "int",
					"scen12": "int",
					"scen15": "int",
					"scen20": "int",
					"scen21": "int",
					"scen22": "int",
					"scen23": "int",
					"scen24": "int",
					"scen25": "int",
					"geom_id": "int64",
					"year_built": "int",
					"building_type_id": "int",
					"development_type_id":"int",
					"building_sqft": "int",
					"non_residential_sqft":"int",
					"residential_units":"int",
					"stories":"int",
					"deed_restricted_units":"int",
					"PARCEL_ID":"int",
					"ZONE_ID": "int"}
	for key, value in field_types.items():
		pipeline_df[key] = pipeline_df[key].fillna(0)
		development_project_df[key] = development_project_df[key].fillna(0)
		if key == 'geom_id' or key == 'PARCEL_ID':
			pipeline_df[key] = pipeline_df[key].round(0).astype(value)
			development_project_df[key] = development_project_df[key].round(0).astype(value)
		else:
			pipeline_df[key] = pipeline_df[key].astype(value)
			development_project_df[key] = development_project_df[key].astype(value)

	res_type = ['HS','HT','HM','GQ','MR']
	nonres_type = ['MT','ME','VP','OF','HO','SC','IL','IW','IH','RS','RB','VA','PG','OT']

	pipeline_df.loc[(pipeline_df['residential_units'] < 0) & (pipeline_df.building_type.isin(res_type)),'residential_units'] = 0
	pipeline_df.loc[(pipeline_df['residential_units'] != 0) & (pipeline_df.building_type.isin(nonres_type)),'residential_units'] = 0
	
	development_project_df.loc[(development_project_df['residential_units'] < 0) & (development_project_df.building_type.isin(res_type)),'residential_units'] = 0
	development_project_df.loc[(development_project_df['residential_units'] != 0) & (development_project_df.building_type.isin(nonres_type)),'residential_units'] = 0

	pipeline_df.to_csv(os.path.join(WORKING_DIR, pipeline_output), index = False)
	development_project_df.to_csv(os.path.join(WORKING_DIR, development_project_output), index = False)
	
	#adding the two map files into a new gdb
	#first create that new gdb -- right now save and locally and upload manually
	out_name = "{}_devproj.gdb".format(NOW)
	arcpy.CreateFileGDB_management(WORKING_DIR, out_name)
	logger.info("Created {}".format(out_name))
	
	#second, move file to the new gdb
	fcs = [pipeline_fc_reordered, devproj_fc_reordered]
	for fc in fcs:
		arcpy.FeatureClassToFeatureClass_conversion(fc, os.path.join(WORKING_DIR, out_name), 
												    arcpy.Describe(fc).name)

	# 8 adding 2011-2015 projects to buildings
	pipeline = 'pipeline_reordered' 
	arcpy.FeatureClassToFeatureClass_conversion(pipeline, arcpy.env.workspace, 
										    'p1115', "year_built >= 2011 AND year_built <= 2015")
	p1115 = 'p1115'
	arcpy.AlterField_management(p1115, "PARCEL_ID", "b_PARCEL_ID")
	arcpy.AlterField_management(p1115, "residential_units", "b_residential_units")
	arcpy.AlterField_management(p1115, "unit_ave_sqft", "b_unit_ave_sqft")
	arcpy.AlterField_management(p1115, "building_sqft", "b_building_sqft")
	arcpy.AlterField_management(p1115, "year_built", "b_year_built")
	arcpy.AlterField_management(p1115, "stories", "b_stories")

	arcpy.AddField_management(p1115, "building_id", "LONG")
	arcpy.AddField_management(p1115, "parcel_id", "LONG")
	arcpy.AddField_management(p1115, "improvement_value", "DOUBLE")
	arcpy.AddField_management(p1115, "residential_units", "LONG")
	arcpy.AddField_management(p1115, "residential_sqft", "LONG")
	arcpy.AddField_management(p1115, "sqft_per_unit", "DOUBLE")
	arcpy.AddField_management(p1115, "non_residential_sqft", "LONG")
	arcpy.AddField_management(p1115, "building_sqft", "DOUBLE")
	arcpy.AddField_management(p1115, "nonres_rent_per_sqft", "DOUBLE")
	arcpy.AddField_management(p1115, "res_price_per_sqft", "DOUBLE")
	arcpy.AddField_management(p1115, "stories", "LONG")
	arcpy.AddField_management(p1115, "year_built", "LONG")
	arcpy.AddField_management(p1115, "redfin_sale_price", "DOUBLE")
	arcpy.AddField_management(p1115, "redfin_sale_year", "DOUBLE")
	arcpy.AddField_management(p1115, "redfin_home_type", "TEXT","","","800")
	arcpy.AddField_management(p1115, "costar_property_type", "TEXT","","","800")
	arcpy.AddField_management(p1115, "costar_rent", "TEXT","","","800")

	#arcpy.CalculateField_management(p1115, "building_id", )
	arcpy.CalculateField_management(p1115, "parcel_id", "!b_PARCEL_ID!")
	#arcpy.CalculateField_management(p1115, "development_type_id",)
	#arcpy.CalculateField_management(p1115, "improvement_value",)
	arcpy.CalculateField_management(p1115, "residential_units", "!b_residential_units!")
	#arcpy.CalculateField_management(p1115, "residential_sqft", )
	arcpy.CalculateField_management(p1115, "sqft_per_unit", "!b_unit_ave_sqft!")
	#arcpy.CalculateField_management(p1115, "non_residential_sqft",)
	arcpy.CalculateField_management(p1115, "building_sqft", "!b_building_sqft!")
	#arcpy.CalculateField_management(p1115, "nonres_rent_per_sqft", )
	#arcpy.CalculateField_management(p1115, "res_price_per_sqft", )
	arcpy.CalculateField_management(p1115, "stories", "!b_stories!")
	arcpy.CalculateField_management(p1115, "year_built", "!b_year_built!")
	arcpy.CalculateField_management(p1115, "redfin_sale_price", "!last_sale_price!")
	#arcpy.CalculateField_management(p1115, "redfin_sale_year", "!last_sale_year!")
	#arcpy.CalculateField_management(p1115, "redfin_home_type", )
	#arcpy.CalculateField_management(p1115, "costar_property_type", )
	arcpy.CalculateField_management(p1115, "costar_rent", "!average_weighted_rent!")

	arcpy.FeatureClassToFeatureClass_conversion(p1115, arcpy.env.workspace,'p1115_add', "action = 'add'")
	arcpy.FeatureClassToFeatureClass_conversion(p1115, arcpy.env.workspace,'p1115_build', "action = 'build'")

	p1115_add = 'p1115_add'
	p1115_build = 'p1115_build'

	FCfields = [f.name for f in arcpy.ListFields(p1115_add)]
	DontDeleteFields = ["OBJECTID","Shape","building_id","parcel_id","development_type_id", "improvement_value", "residential_units", "residential_sqft",  "sqft_per_unit", 
	"non_residential_sqft","building_sqft","nonres_rent_per_sqft","res_price_per_sqft","stories","year_built", "redfin_sale_price","redfin_sale_year",
	"redfin_home_type","costar_property_type","costar_rent","building_type","building_type_id","development_type_id"]
	fields2Delete = list(set(FCfields) - set(DontDeleteFields))
	arcpy.DeleteField_management(p1115_add, fields2Delete)
	arcpy.DeleteField_management(p1115_build, fields2Delete) #because the two dataset should have the same structure

	b10_smelt = os.path.join(SMELT_GDB, "b10")
	logger.info("Reading 2010 building file {}".format(b10_smelt))
	arcpy.TableToTable_conversion(b10_smelt, arcpy.env.workspace,'b10')
	b10 = 'b10'
	arcpy.AddField_management(b10, "building_type", "TEXT","","","800")
	arcpy.AddField_management(b10, "building_type_id", "LONG")

	with arcpy.da.UpdateCursor(b10, ["development_type_id","building_type","building_type_id"]) as cursor:
				for row in cursor:
					if row[0] == 1:
						row[1] = "HS"
						row[2] = 1
					elif row[0] == 2:
						row[1] = 'HM'
						row[2] = 3
					elif row[0] == 3:
						row[1] = 'HM'
						row[2] = 3
					elif row[0] == 4:
						row[1] = 'HM'
						row[2] = 3
					elif row[0] == 5:
						row[1] = 'MR'
						row[2] = 12
					elif row[0] == 6:
						row[1] = 'GQ'
						row[2] = 3
					elif row[0] == 7:
						row[1] = 'RS'
						row[2] = 10
					elif row[0] == 8:
						row[1] = 'RB'
						row[2] = 11
					elif row[0] == 9:
						row[1] = 'HO'
						row[2] = 5
					elif row[0] == 10:
						row[1] = 'OF'
						row[2] = 4
					elif row[0] == 11:
						row[1] = 'ME'
						row[2] = 14
					elif row[0] == 12:
						row[1] = 'OF'
						row[2] = 4
					elif row[0] == 13:
						row[1] = 'IW'
						row[2] = 8
					elif row[0] == 14:
						row[1] = 'IL'
						row[2] = 7
					elif row[0] == 15:
						row[1] = 'IH'
						row[2] = 9
					elif row[0] == 16:
						row[1] == 'IL'
						row[2] = 7
					elif row[0] == 17:
						row[1] = 'SC'
						row[2] = 6
					elif row[0] == 18:
						row[1] = 'SC'
						row[2] = 6
					elif row[0] == 19:
						row[1] = 'OF'
						row[2] = 4
					elif row[0] == 20:
						row[1] = 'VP'
						row[2] = 0
					elif row[0] == 21:
						row[1] = 'VA'
						row[2] = 0
					elif row[0] == 22:
						row[1] = 'PG'
						row[2] = 16
					elif row[0] == 23:
						row[1] = 'PA'
						row[2] = 15
					elif row[0] == 24:
						row[1] = 'VP'
						row[2] = 0
					elif row[0] == 25:
						row[1] = 'VA'
						row[2] = 0
					cursor.updateRow(row)

	arcpy.DeleteField_management(b10, 'id')

	#the approach is:
	#1. simply merge the projects with action == add
	#2. find out the parcel ids where projects would be built in p1115_build, then remove those parcels in b10, the merge the build file
	#need to build some diagnostic stuff to compare what was there that gets removed, and what's added

	#part 1: add the projects
	b10_p1115_part1 = 'b10_p1115_part1'
	mergeList = [b10,p1115_add]
	arcpy.Merge_management(mergeList, b10_p1115_part1)

	#create a copy of the merged file for diagnostics
	arcpy.TableToTable_conversion(b10_p1115_part1, arcpy.env.workspace,'b10_p1115_part1_copy')

	#part 2: remove and merge
	parcelBuildList = [row[0] for row in arcpy.da.SearchCursor(p1115_build, 'parcel_id')]
	with arcpy.da.UpdateCursor(b10_p1115_part1, "parcel_id") as cursor:
		for row in cursor:
			if row[0] in parcelBuildList:
				cursor.deleteRow()

	rawp10_b15_pba50 = 'rawp10_b15_pba50_{}'.format(NOW)[0:26] #delete ".time" part, because that dot breaks it.
	mergeList2 = [b10_p1115_part1,p1115_build]
	arcpy.Merge_management(mergeList2, rawp10_b15_pba50)

	btnull = 'btnull' ##stands for building type null
	arcpy.MakeTableView_management(rawp10_b15_pba50,btnull,"building_type is NULL")
	nullcount = arcpy.GetCount_management(btnull)
	logger.info("Building file list has {} records with building type info missing".format(nullcount))
	arcpy.Delete_management(btnull)

	#diagnotics using the copy
	b10_p1115_part1_copy = 'b10_p1115_part1_copy'
	with arcpy.da.UpdateCursor(b10_p1115_part1_copy, "parcel_id") as cursor:
		for row in cursor:
			if row[0] not in parcelBuildList:
				cursor.deleteRow()

		del cursor, row

	arcpy.Statistics_analysis(b10_p1115_part1_copy, 'removed_units', [["residential_units", "SUM"]])
	cursor = arcpy.SearchCursor('removed_units','','', 'SUM_residential_units')
	row = cursor.next()
	sum_value1 = row.getValue('SUM_residential_units')

	arcpy.Statistics_analysis(b10_p1115_part1_copy, 'removed_nonres', [["non_residential_sqft", "SUM"]])
	cursor = arcpy.SearchCursor('removed_nonres','','', 'SUM_non_residential_sqft')
	row = cursor.next()
	sum_value2 = row.getValue('SUM_non_residential_sqft')

	arcpy.Statistics_analysis(p1115_build, 'built_units', [["residential_units", "SUM"]])
	cursor = arcpy.SearchCursor('built_units','','', 'SUM_residential_units')
	row = cursor.next()
	sum_value3 = row.getValue('SUM_residential_units')

	arcpy.Statistics_analysis(p1115_build, 'built_nonres', [["non_residential_sqft", "SUM"]])
	cursor = arcpy.SearchCursor('built_nonres','','', 'SUM_non_residential_sqft')
	row = cursor.next()
	sum_value4 = row.getValue('SUM_non_residential_sqft')

	if sum_value1 >= sum_value3:
		logger.info("There is a net decrease of {} units from {} units to {} units after incorporating the 'built' projects".format(sum_value1 - sum_value3, sum_value1, sum_value3))
	else:
		logger.info("There is a net increase of {} units from {} units to {} units after incorporating the 'built' projects".format(sum_value3 - sum_value1,sum_value1, sum_value3))
	if sum_value2 >= sum_value4:
		logger.info("There is a net decrease of {} square feet of nonresidential from {} sqft to {} sqft  after incorporating the 'built' projects".format(sum_value2 - sum_value4, sum_value2, sum_value4))
	else:
		logger.info("There is a net increase of {} square feet of nonresidential from {} sqft  to {} sqft  after incorporating the 'built' projects".format(sum_value4 - sum_value2, sum_value2, sum_value4))

	building_output = "{}_buildings.csv".format(NOW)
	arcpy.TableToTable_conversion(rawp10_b15_pba50, WORKING_DIR, building_output)
	building_df = pd.read_csv(os.path.join(WORKING_DIR, building_output))
	building_df = building_df.rename(columns = {'development_type' : 'development_type_id',
											'improvement_valu' : 'improvement_value',
											'residential_unit' : 'residential_units',
											'non_residential_' : 'non_residential_sqft',
											'nonres_rent_per_' : 'nonres_rent_per_sqft',
											'res_price_per_sq' : 'res_price_per_sqft',	
											'redfin_sale_pric' : 'redfin_sale_price',
											'costar_property_' : 'costar_property_type'})	

	#fix int column problem in csv
	field_types_building = {"OBJECTID" : "int",
					"building_id": "int",
					"parcel_id": "int",
					"stories":"int",
					"year_built": "int",
					"building_type_id": "int",
					"development_type_id":"int",
					"building_sqft": "int",
					"non_residential_sqft":"int",
					"residential_units":"int",
					"residential_sqft":"int"}

	for key, value in field_types_building.items():
		building_df[key] = building_df[key].fillna(0)
		building_df[key] = building_df[key].astype(value)
	building_df.to_csv(os.path.join(WORKING_DIR, building_output), index = False)
	logger.info("Transform {} to building table".format(rawp10_b15_pba50))




