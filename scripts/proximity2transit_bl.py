import os, sys, time
import arcpy
import logging
from arcgis.gis import GIS
from arcgis.features import FeatureLayer
import pandas as pd
import numpy as np

NOW = time.strftime("%Y_%m%d_%H%M")

if os.getenv("USERNAME")=="MTCPB":
	WORKING_DIR		 = "C:\\Users\\MTCPB\\Documents\\ArcGIS\\Projects\\Proximity"
	LOG_FILE		    = os.path.join(WORKING_DIR,"proximity2transit_{}.log".format(NOW))
	P2T_GDB		   = "C:\\Users\\MTCPB\\Documents\\ArcGIS\\Projects\\Proximity\\Proximity.gdb"
	WORKSPACE_GDB       = "workspace_{}.GDB".format(NOW)


MTC_ONLINE_TRANSIT15_URL = 'https://arcgis.ad.mtc.ca.gov/server/rest/services/Hosted/Existing_Transit_Stops_2020/FeatureServer/0'
MTC_ONLINE_TRANSIT50_URL = 'https://arcgis.ad.mtc.ca.gov/server/rest/services/Hosted/transitstops_01_2020_potential/FeatureServer/0'
MTC_ONLINE_BACOUNTY_URL  = 'https://arcgis.ad.mtc.ca.gov/server/rest/services/Hosted/county_region/FeatureServer/\
0?token=CjEwvAXFsqxLRQUDXcXdE2UiCvnfSdSnbwyLWY9nyEd3_X-8fqweg4FGuxjPXZ-GLsX8Hu5K_u0JfQP\
8VlapfgMcPFqFNzAkh7gjRLJnjO_a72KZtHGm3OSl-GLC3v4hqxpS478NRaSkQJB5fCLtvn_9nDiagBLbpldEwgL\
ruCJpsNDb9TPyyyrJ13Vl9LtZ-xZDqyZ5762Kju_a-nydWOqk0tB6ri9fPHh67sElVVA.'

transit_current_portal = arcpy.MakeFeatureLayer_management(MTC_ONLINE_TRANSIT15_URL,'transit_current_portal')
transit_potential_portal = arcpy.MakeFeatureLayer_management(MTC_ONLINE_TRANSIT50_URL,'transit_potential_portal')
bacounty_portal = arcpy.MakeFeatureLayer_management(MTC_ONLINE_BACOUNTY_URL,'bacounty_portal')

arcpy.env.workspace = P2T_GDB
arcpy.env.overwriteOutput = True

if arcpy.Exists('transit_current'):
	arcpy.Delete_management('transit_current')
if arcpy.Exists('transit_potential'):
	arcpy.Delete_management('transit_potential')
if arcpy.Exists('bacounty'):
	arcpy.Delete_management('bacounty')
arcpy.FeatureClassToFeatureClass_conversion(transit_current_portal, P2T_GDB,'transit_current')
arcpy.FeatureClassToFeatureClass_conversion(transit_potential_portal, P2T_GDB,'transit_potential')
arcpy.FeatureClassToFeatureClass_conversion(bacounty_portal, P2T_GDB,'bacounty')

transit_current   = os.path.join(P2T_GDB, "transit_current")
transit_potential   = os.path.join(P2T_GDB, "transit_potential")
bacounty   = os.path.join(P2T_GDB, "bacounty")

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
	logger.info("Proximity_GDB     = {}".format(P2T_GDB))

	# list info about SMELT_GDB
	arcpy.env.workspace = P2T_GDB
	logger.info("workspace: {}".format(arcpy.env.workspace))
	for dataset in arcpy.ListDatasets():
		logger.info("  dataset: {}".format(dataset))
		logger.info("    feature classes: {} ".format(arcpy.ListFeatureClasses(feature_dataset=dataset)))
	
	logger.info("  feature classes: {} ".format(arcpy.ListFeatureClasses()))
	logger.info("  tables: {} ".format(arcpy.ListTables()))

	arcpy.CreateFileGDB_management(WORKING_DIR, WORKSPACE_GDB)
	arcpy.env.workspace = os.path.join(WORKING_DIR, WORKSPACE_GDB)

	###doing for current transit stops
	logger.info('Select buffer for major transit stops')
	arcpy.management.SelectLayerByAttribute("transit_current", "NEW_SELECTION", "major_stop = 1", None)
	arcpy.analysis.Buffer("transit_current", "TPA2020", "0.5 Miles", "FULL", "ROUND", "ALL", None, "PLANAR")

	logger.info('Select buffer for headway < 15min (TRA)')
	arcpy.management.SelectLayerByAttribute("transit_current", "NEW_SELECTION", "hdwy_15min = 1", None)
	arcpy.analysis.Buffer("transit_current", "TRA2020", "0.25 Miles", "FULL", "ROUND", "ALL", None, "PLANAR")

	logger.info('Select buffer for headway 15-30 min')
	arcpy.management.SelectLayerByAttribute("transit_current", "NEW_SELECTION", "hdwy_30min = 1", None)
	arcpy.analysis.Buffer("transit_current", "Bus15_30", "0.25 Miles", "FULL", "ROUND", "ALL", None, "PLANAR")

	logger.info('Select buffer for headway 30+ min')
	arcpy.management.SelectLayerByAttribute("transit_current", "NEW_SELECTION", "hdwy_class = '31 mins or more'", None)
	arcpy.analysis.Buffer("transit_current", "Bus30Plus", "0.25 Miles", "FULL", "ROUND", "ALL", None, "PLANAR")

	#Using county boundaries alone did not capture all parcels (1,952,484/1,956,212). With buffering 0.5 mi 1,956,044/1,956,212 99.99% of all parcels
	arcpy.analysis.Buffer("bacounty", "bacounty_expand", "0.5 Miles", "FULL", "ROUND", "ALL", None, "PLANAR")

	logger.info('only include high-freq bus area not already part of Major Transit Stop buffer')
	arcpy.analysis.Erase("TRA2020", "TPA2020", "TRA2020_Erased", None)

	logger.info('Create Bus 15-30min shape')
	arcpy.analysis.Erase("Bus15_30", "TRA2020_Erased", "Bus15_30_PartialErased", None)
	arcpy.analysis.Erase("Bus15_30_PartialErased", "TPA2020", "Bus15_30_Erased", None)

	logger.info('Create Bus 31+ min shape')
	arcpy.analysis.Erase("Bus30Plus", "Bus15_30_Erased", "Bus30Plus_PartialErased1", None)
	arcpy.analysis.Erase("Bus30Plus_PartialErased1", "TRA2020_Erased", "Bus30Plus_PartialErased2", None)
	arcpy.analysis.Erase("Bus30Plus_PartialErased2", "TPA2020", "Bus30Plus_Erased", None)

	logger.info('Create Rest of Bay Area Shape')
	arcpy.analysis.Erase("BAcounty_expand", "Bus30Plus_Erased", "RestofBA_PartialErased1", None)
	arcpy.analysis.Erase("RestofBA_PartialErased1", "Bus15_30_Erased", "RestofBA_PartialErased2", None)
	arcpy.analysis.Erase("RestofBA_PartialErased2", "TRA2020_Erased", "RestofBA_PartialErased3", None)
	arcpy.analysis.Erase("RestofBA_PartialErased3", "TPA2020", "RestofBA_Erased", None)

	logger.info('Merge into 1 feature class with 5 polygons: Major Transit stop, high freq corridor, 15-30min bus, 31+min bus and remainder of region')
	arcpy.management.Merge("RestofBA_Erased;Bus30Plus_Erased;Bus15_30_Erased;TRA2020_Erased;TPA2020", "Transit2020")

	arcpy.management.Delete(["Bus15_30_PartialErased","Bus30Plus_PartialErased1",\
							"Bus30Plus_PartialErased2","RestofBA_PartialErased1",\
							"RestofBA_PartialErased2","RestofBA_PartialErased3"])

	####repeat the same process for No Plan, projects that are in No Plan are automatically high quality transit as a major transit stop
	logger.info('Select and Buffer No Plan stops')
	arcpy.management.SelectLayerByAttribute("transit_potential", "NEW_SELECTION", "status = 'Under Construction'", None)
	arcpy.analysis.Buffer("transit_potential", "TPA2050_NP", "0.5 Miles", "FULL", "ROUND", "ALL", None, "PLANAR")

	logger.info('Merge and create a new TPA under NP')
	arcpy.management.Merge("TPA2050_NP; TPA2020", "TPA2050_NP_Merge")
	#dissolve so easier when merged
	arcpy.management.Dissolve("TPA2050_NP_Merge", "TPA2050_NP_Dislve", None, None, "MULTI_PART", "DISSOLVE_LINES")

	arcpy.analysis.Erase("TRA2020", "TPA2050_NP_Dislve", "TRA2050_NP", None)

 	logger.info('Create Bus 15-30min shape for NP')
 	arcpy.analysis.Erase("Bus15_30", "TRA2050_NP", "Bus15_30_2050NP_PartialErase", None)
	arcpy.analysis.Erase("Bus15_30_2050NP_PartialErase", "TPA2050_NP_Dislve", "Bus15_30_2050NP", None)

	logger.info('Create Bus 31+ min shape for NP')
	arcpy.analysis.Erase("Bus30Plus", "Bus15_30_2050NP", "Bus30Plus_2050NP_PartialErased1", None)
	arcpy.analysis.Erase("Bus30Plus_2050NP_PartialErased1", "TRA2050_NP", "Bus30Plus_2050NP_PartialErased2", None)
	arcpy.analysis.Erase("Bus30Plus_2050NP_PartialErased2", "TPA2050_NP_Dislve", "Bus30Plus_2050NP", None)

	logger.info('Create Rest of Bay Area Shape for NP')
	arcpy.analysis.Erase("BAcounty_expand", "Bus30Plus_2050NP", "RestofBA_2050NP_PartialErased1", None)
	arcpy.analysis.Erase("RestofBA_2050NP_PartialErased1", "Bus15_30_2050NP", "RestofBA_2050NP_PartialErased2", None)
	arcpy.analysis.Erase("RestofBA_2050NP_PartialErased2", "TRA2050_NP", "RestofBA_2050NP_PartialErased3", None)
	arcpy.analysis.Erase("RestofBA_2050NP_PartialErased3", "TPA2050_NP_Dislve", "RestofBA_2050NP", None)

	logger.info('Merge into 1 feature class with 5 polygons')
	arcpy.management.Merge("RestofBA_2050NP;Bus30Plus_2050NP; Bus15_30_2050NP;TRA2050_NP;TPA2050_NP_Dislve", "Transit2050_NP")

	arcpy.management.Delete(["Bus15_30_2050NP_PartialErased","Bus30Plus_2050NP_PartialErased1",\
							"Bus30Plus_2050NP_PartialErased2","RestofBA_2050NP_PartialErased1",\
							"RestofBA_2050NP_PartialErased2","RestofBA_2050NP_PartialErased3"])

	####repeat the same process for DBP Plan, projects that are in No Plan are automatically high quality transit as a major transit stop -- this to revise to Final Blue Print
	logger.info('Select and Buffer No Plan stops')
	arcpy.management.SelectLayerByAttribute("transit_potential", "NEW_SELECTION", "status = 'Under Construction' Or status = 'Draft Blueprint'", None)
	arcpy.analysis.Buffer("transit_potential", "TPA2050_BP", "0.5 Miles", "FULL", "ROUND", "ALL", None, "PLANAR")

	logger.info('Merge and create a new TPA under BP')
	arcpy.management.Merge("TPA2050_BP; TPA2020", "TPA2050_BP_Merge")
	#dissolve so easier when merged
	arcpy.management.Dissolve("TPA2050_BP_Merge", "TPA2050_BP_Dislve", None, None, "MULTI_PART", "DISSOLVE_LINES")

	arcpy.analysis.Erase("TRA2020", "TPA2050_BP_Dislve", "TRA2050_BP", None)

 	logger.info('Create Bus 15-30min shape for BP')
 	arcpy.analysis.Erase("Bus15_30", "TRA2050_BP", "Bus15_30_2050BP_PartialErase", None)
	arcpy.analysis.Erase("Bus15_30_2050BP_PartialErase", "TPA2050_BP_Dislve", "Bus15_30_2050BP", None)

	logger.info('Create Bus 31+ min shape for BP')
	arcpy.analysis.Erase("Bus30Plus", "Bus15_30_2050BP", "Bus30Plus_2050BP_PartialErased1", None)
	arcpy.analysis.Erase("Bus30Plus_2050BP_PartialErased1", "TRA2050_BP", "Bus30Plus_2050BP_PartialErased2", None)
	arcpy.analysis.Erase("Bus30Plus_2050BP_PartialErased2", "TPA2050_BP_Dislve", "Bus30Plus_2050BP", None)

	logger.info('Create Rest of Bay Area Shape for BP')
	arcpy.analysis.Erase("BAcounty_expand", "Bus30Plus_2050BP", "RestofBA_2050BP_PartialErased1", None)
	arcpy.analysis.Erase("RestofBA_2050BP_PartialErased1", "Bus15_30_2050BP", "RestofBA_2050BP_PartialErased2", None)
	arcpy.analysis.Erase("RestofBA_2050BP_PartialErased2", "TRA2050_BP", "RestofBA_2050BP_PartialErased3", None)
	arcpy.analysis.Erase("RestofBA_2050BP_PartialErased3", "TPA2050_BP_Dislve", "RestofBA_2050BP", None)

	logger.info('Merge into 1 feature class with 5 polygons')
	arcpy.management.Merge("RestofBA_2050BP;Bus30Plus_2050BP; Bus15_30_2050BP;TRA2050_BP;TPA2050_BP_Dislve", "Transit2050_BP")

		arcpy.management.Delete(["Bus15_30_2050BP_PartialErased","Bus30Plus_2050BP_PartialErased1",\
							"Bus30Plus_2050BP_PartialErased2","RestofBA_2050BP_PartialErased1",\
							"RestofBA_2050BP_PartialErased2","RestofBA_2050BP_PartialErased3"])