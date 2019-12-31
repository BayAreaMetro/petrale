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
arcpy.SpatialJoin_analysis(rfsfr1619, p10, rfsfr1619p10JOIN)
arcpy.SpatialJoin_analysis(rfmu1619, p10, rfmu1619p10JOIN)

# possibly collapse on geomid or do all as adds but first demollish those geomids in separate step but that must be manual 


# rename any conflicting field names
# arcpy.AlterField_management(fc, field.name, 'ELEVATION', 'Elevation in Metres')

# add fields and calc values
# full list development_projects_id,raw_id,building_name,site_name,action,scen0,scen1,scen2,scen3,scen4,scen5,scen6,scen7,scen10,scen11,scen12,scen15,address,city,zip,county,x,y,geom_id,year_built,duration,building_type_id,building_type,building_sqft,non_residential_sqft,residential_units,unit_ave_sqft,tenure,rent_type,stories,parking_spaces,Average Weighted Rent,rent_ave_sqft,rent_ave_unit,last_sale_year,last_sale_price,source,edit_date,editor,version

#arcpy.AddField_management(inFeatures, fieldName1, "DOUBLE", 
#                          fieldPrecision, fieldScale)

#arcpy.CalculateField_management(in_table, field, expression)


# delete all those other fields

# FCfields = [f.name for f in arcpy.ListFields(fc)]
# DontDeleteFields = ['Shape_STArea__', 'Shape_STLength__', 'STATE', 'FIPS', 'Shape',  'Shape_Length', 'Shape_Area', 'AreaFT']
# fields2Delete = list(set(FCfields) - set(DontDeleteFields))
# arcpy.DeleteField_management(fc, fields2Delete)


# export csv
