# coding: utf-8
import arcpy


# set enviro
arcpy.env.workspace = "E:/baydata/smelt.gdb"


# set vars
p10 = "p10"

cs1620 = "cs1620"
cs1620p10JOIN = "ttt_cs1620_p10"
rfsfr1619 = "rf19_sfr1619"
rfsfr1619p10JOIN = "ttt_rfsfr1619_p10"
rfmu1619 = "rf19_multiunit1619"
rfmu1619p10JOIN = "ttt_rfmu1619_p10"

cs1115 = "cs1115"
cs1115p10JOIN = "ttt_cs1115_p10"
rfsfr1115 = "rf19_sfr1115"
rfsfr1115p10JOIN = "ttt_rfsfr1115_p10"
rfcondo1115 = "rf19_condounits1115"
rfcondo1115p10JOIN = "ttt_rfcondo1115_p10"
rfother1115 = "rf19_othertypes1115"
rfother1115p10JOIN = "ttt_rfother1115_p10"

basis_pipeline = "basis_pipeline"

# spatial joins

arcpy.SpatialJoin_analysis(cs1620, p10, cs1620p10JOIN)
#arcpy.SpatialJoin_analysis(rfsfr1619, p10, rfsfr1619p10JOIN)
#arcpy.SpatialJoin_analysis(rfmu1619, p10, rfmu1619p10JOIN)

# possibly collapse on geomid or do all as adds but first demollish those geomids in separate step but that must be manual 

# OR JUST RENAME ALL VARS FIRST AND MERGE THEN CLEAN 

# rename any conflicting field names
arcpy.AlterField_management(cs1620p10JOIN, "building_name", "cs_building_name")
arcpy.AlterField_management(cs1620p10JOIN, "city", "cs_city")
arcpy.AlterField_management(cs1620p10JOIN, "rent_type", "cs_rent_type")
arcpy.AlterField_management(cs1620p10JOIN, "year_built", "cs_year_built")
arcpy.AlterField_management(cs1620p10JOIN, "last_sale_price", "cs_last_sale_price")
arcpy.AlterField_management(cs1620p10JOIN, "last_sale_date", "cs_sale_date")
arcpy.AlterField_management(cs1620p10JOIN, "Average_Weighted_Rent", "cs_average_weighted_rent")
arcpy.AlterField_management(cs1620p10JOIN, "x", "p_x") # this is from the parcel centroid
arcpy.AlterField_management(cs1620p10JOIN, "y", "p_y") # this is from the parcel centroid
arcpy.AlterField_management(cs1620p10JOIN, "geom_id", "p_geom_id") # this is from the parcel 


# add fields and calc values
# full list development_projects_id,raw_id,building_name,site_name,action,scen0,scen1,scen2,scen3,scen4,scen5,scen6,scen7,scen10,scen11,scen12,scen15,
# address,city,zip,county,x,y,geom_id,year_built,duration,building_type_id,building_type,building_sqft,non_residential_sqft,
# residential_units,unit_ave_sqft,tenure,rent_type,stories,parking_spaces,Average Weighted Rent,rent_ave_sqft,rent_ave_unit,
# last_sale_year,last_sale_price,source,edit_date,editor,version
# AddField(in_table, field_name, field_type, {field_precision}, {field_scale}, {field_length}, {field_alias}, {field_is_nullable}, {field_is_required}, {field_domain})

arcpy.AddField_management(cs1620p10JOIN, "development_projects_id", "SHORT")
arcpy.AddField_management(cs1620p10JOIN, "raw_id", "LONG")
arcpy.AddField_management(cs1620p10JOIN, "building_name", "TEXT","","",50)
arcpy.AddField_management(cs1620p10JOIN, "site_name", "TEXT","","",50)
arcpy.AddField_management(cs1620p10JOIN, "action", "TEXT","","",10)
arcpy.AddField_management(cs1620p10JOIN, "scen0", "SHORT")
arcpy.AddField_management(cs1620p10JOIN, "address", "TEXT","","",50)
arcpy.AddField_management(cs1620p10JOIN, "city", "TEXT","","",50)
arcpy.AddField_management(cs1620p10JOIN, "zip", "LONG")
arcpy.AddField_management(cs1620p10JOIN, "county", "TEXT","","",50)
arcpy.AddField_management(cs1620p10JOIN, "x", "FLOAT")
arcpy.AddField_management(cs1620p10JOIN, "y", "FLOAT")
arcpy.AddField_management(cs1620p10JOIN, "geom_id", "TEXT","","",50)
arcpy.AddField_management(cs1620p10JOIN, "year_built", "SHORT")
arcpy.AddField_management(cs1620p10JOIN, "duration", "SHORT")
arcpy.AddField_management(cs1620p10JOIN, "building_type_id", "SHORT")
arcpy.AddField_management(cs1620p10JOIN, "building_type", "TEXT","","",4)
arcpy.AddField_management(cs1620p10JOIN, "building_sqft", "LONG")
arcpy.AddField_management(cs1620p10JOIN, "non_residential_sqft", "LONG")
arcpy.AddField_management(cs1620p10JOIN, "residential_units", "SHORT")
arcpy.AddField_management(cs1620p10JOIN, "unit_ave_sqft", "SHORT")
arcpy.AddField_management(cs1620p10JOIN, "tenure", "TEXT","","",5)
arcpy.AddField_management(cs1620p10JOIN, "rent_type", "TEXT","","",25)
arcpy.AddField_management(cs1620p10JOIN, "stories", "SHORT")
arcpy.AddField_management(cs1620p10JOIN, "parking_spaces", "SHORT")
arcpy.AddField_management(cs1620p10JOIN, "Average Weighted Rent", "FLOAT")
arcpy.AddField_management(cs1620p10JOIN, "rent_ave_sqft", "FLOAT")
arcpy.AddField_management(cs1620p10JOIN, "rent_ave_unit", "SHORT")
arcpy.AddField_management(cs1620p10JOIN, "last_sale_year", "SHORT")
arcpy.AddField_management(cs1620p10JOIN, "last_sale_price", "LONG")
arcpy.AddField_management(cs1620p10JOIN, "source", "TEXT","","",10)
arcpy.AddField_management(cs1620p10JOIN, "edit_date", "DATE")
arcpy.AddField_management(cs1620p10JOIN, "editor", "TEXT","","",50)
arcpy.AddField_management(cs1620p10JOIN, "version", "SHORT")


arcpy.CalculateField_management(cs1620p10JOIN, "raw_id", '!PropertyID!')
arcpy.CalculateField_management(cs1620p10JOIN, "building_name", '!cs_building_name!')
arcpy.CalculateField_management(cs1620p10JOIN, "site_name", '!Building_Park!')
arcpy.CalculateField_management(cs1620p10JOIN, "action", "add")
arcpy.CalculateField_management(cs1620p10JOIN, "scen0", "1") # these are committed so 1 for all scens 
arcpy.CalculateField_management(cs1620p10JOIN, "address", '!Building_Adress!')
arcpy.CalculateField_management(cs1620p10JOIN, "city", '!cs_city!')
arcpy.CalculateField_management(cs1620p10JOIN, "zip", '!Zip!')
arcpy.CalculateField_management(cs1620p10JOIN, "county", '!County_Name!')
arcpy.CalculateField_management(cs1620p10JOIN, "x", '!p_x!')
arcpy.CalculateField_management(cs1620p10JOIN, "y", '!p_y!')
arcpy.CalculateField_management(cs1620p10JOIN, "geom_id", '!p_geom_id!')
arcpy.CalculateField_management(cs1620p10JOIN, "year_built", '!cs_year_built!')
#arcpy.CalculateField_management(cs1620p10JOIN, "duration", )
#arcpy.CalculateField_management(cs1620p10JOIN, "building_type_id", )
arcpy.CalculateField_management(cs1620p10JOIN, "building_type", '!det_bldg_type!')
arcpy.CalculateField_management(cs1620p10JOIN, "building_sqft", '!Rentable_Building_Area!') # how often null for res
arcpy.CalculateField_management(cs1620p10JOIN, "non_residential_sqft", '!Rentable_Building_Area!') # need to zero out for res
arcpy.CalculateField_management(cs1620p10JOIN, "residential_units", '!Number_Of_Units!')
arcpy.CalculateField_management(cs1620p10JOIN, "unit_ave_sqft", '!Avg_Unit_SF!')
arcpy.CalculateField_management(cs1620p10JOIN, "tenure", "Rent")
arcpy.CalculateField_management(cs1620p10JOIN, "rent_type", '!cs_rent_type!') # need to clean
arcpy.CalculateField_management(cs1620p10JOIN, "stories", '!Number_Of_Stories!')
arcpy.CalculateField_management(cs1620p10JOIN, "parking_spaces", '!Number_Of_Parking_Spaces!')
arcpy.CalculateField_management(cs1620p10JOIN, "Average Weighted Rent", '!cs_average_weighted_rent!')
arcpy.CalculateField_management(cs1620p10JOIN, "rent_ave_sqft", )
arcpy.CalculateField_management(cs1620p10JOIN, "rent_ave_unit", )
arcpy.CalculateField_management(cs1620p10JOIN, "last_sale_year", '!cs_sale_date!') #need to make into year
arcpy.CalculateField_management(cs1620p10JOIN, "last_sale_price", '!cs_last_sale_price'!)
arcpy.CalculateField_management(cs1620p10JOIN, "source", "cs")
arcpy.CalculateField_management(cs1620p10JOIN, "edit_date", "Jan 2020")
arcpy.CalculateField_management(cs1620p10JOIN, "editor", "MKR")
arcpy.CalculateField_management(cs1620p10JOIN, "version", )

#scen is by info in file originally
#do xy from parcel centroids cause captures cleaning

# delete all those other fields

# FCfields = [f.name for f in arcpy.ListFields(fc)]
# DontDeleteFields = ['Shape_STArea__', 'Shape_STLength__', 'STATE', 'FIPS', 'Shape',  'Shape_Length', 'Shape_Area', 'AreaFT']
# fields2Delete = list(set(FCfields) - set(DontDeleteFields))
# arcpy.DeleteField_management(fc, fields2Delete)


# merge shapefiles into 1 for committed dev proj


# bring in oppsites and set scens as in gis file

# then merge committed with oppsites for a single shapefile 



#arcpy.CalculateField_management(ALL, "development_projects_id", ) #create

# manual scen mods

# export csv

#arcpy.Delete_management(rfsfr1619p10JOIN)
