# coding: utf-8
import arcpy


# set enviro

# set vars

cs1620 = "E:/baydata/smelt.gdb/cs1620"
p10 = "E:/baydata/smelt.gdb/p10"
cs1620p10JOIN = "E:/baydata/smelt.gdb/ttt_cs1620_p10"


# spatial joins

arcpy.SpatialJoin_analysis(cs1620, p10, cs1620p10JOIN)



# add fields and calc values
# full list development_projects_id,raw_id,building_name,site_name,action,scen0,scen1,scen2,scen3,scen4,scen5,scen6,scen7,scen10,scen11,scen12,scen15,address,city,zip,county,x,y,geom_id,year_built,duration,building_type_id,building_type,building_sqft,non_residential_sqft,residential_units,unit_ave_sqft,tenure,rent_type,stories,parking_spaces,Average Weighted Rent,rent_ave_sqft,rent_ave_unit,last_sale_year,last_sale_price,source,edit_date,editor,version

arcpy.AddField_management(inFeatures, fieldName1, "DOUBLE", 
                          fieldPrecision, fieldScale)

arcpy.CalculateField_management(in_table, field, expression)


