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

arcpy.AddField_management(inFeatures, fieldName1, "DOUBLE", 
                          fieldPrecision, fieldScale)

arcpy.AddField_management(inFeatures, fieldName1, "DOUBLE", 
                          fieldPrecision, fieldScale)


