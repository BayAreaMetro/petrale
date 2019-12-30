# coding: utf-8
import arcpy

cs1620 = "E:/baydata/smelt.gdb/cs1620"
p10 = "E:/baydata/smelt.gdb/p10"
cs1620p10JOIN = "E:/baydata/smelt.gdb/ttt_cs1620_p10"

arcpy.SpatialJoin_analysis(cs1620, p10, cs1620p10JOIN)
