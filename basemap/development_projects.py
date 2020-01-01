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


# spatial joins

arcpy.SpatialJoin_analysis(cs1620, p10, cs1620p10JOIN)
#arcpy.SpatialJoin_analysis(rfsfr1619, p10, rfsfr1619p10JOIN)
#arcpy.SpatialJoin_analysis(rfmu1619, p10, rfmu1619p10JOIN)

# possibly collapse on geomid or do all as adds but first demollish those geomids in separate step but that must be manual 


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


arcpy.CalculateField_management(cs1620p10JOIN, "residential_units", "!Number of Units!")


# delete all those other fields

# FCfields = [f.name for f in arcpy.ListFields(fc)]
# DontDeleteFields = ['Shape_STArea__', 'Shape_STLength__', 'STATE', 'FIPS', 'Shape',  'Shape_Length', 'Shape_Area', 'AreaFT']
# fields2Delete = list(set(FCfields) - set(DontDeleteFields))
# arcpy.DeleteField_management(fc, fields2Delete)


# export csv

#arcpy.Delete_management(rfsfr1619p10JOIN)
