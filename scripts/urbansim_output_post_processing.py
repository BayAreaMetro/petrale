
# coding: utf-8
#The script is used for process geograpy summary files and combine different run results for visualization in Tableau
import pandas as pd
import numpy as np
import os
import re
from functools import reduce

#PBA40 folder
PBA40_DIR                  = os.path.join(os.environ["USERPROFILE"],
                            "Box\Modeling and Surveys\Share Data\plan-bay-area-2040\RTP17 UrbanSim Output\\r7224c\\")

# The location of Urbansim outputs
URBANSIM_OUTPUT_BOX_DIR    = os.path.join(os.environ["USERPROFILE"],
                            "Box\Modeling and Surveys\Urban Modeling\Bay Area UrbanSim 1.5\PBA50")


# Final draft blueprint output
DBP_DIR                    = "Draft Blueprint runs\Blueprint Plus Crossing (s23)\\v1.7.1- FINAL DRAFT BLUEPRINT"

# Add new runs here: for comparison -- using v1.8 as a placeholder for now
DBP_CLEANER_DIR                 = "Draft Blueprint runs\Blueprint Plus Crossing (s23)\\v1.8 - final cleaner"

# A list of paths of runs, which would be read and produce summaries altogether
PATH_LIST      = [PBA40_DIR, DBP_DIR, DBP_CLEANER_DIR] # ---Add new run paths to this list---

#Visualization folder
VIZ            = "Visualizations"

#Output will into this workbook
OUTPUT_FILE    = os.path.join(URBANSIM_OUTPUT_BOX_DIR, VIZ, 
                                         "PBA50_growth_{}_allruns.csv")

#calculate the growth between 2015 and 2050 for taz summaries
def taz_calculator(DF1, DF2):
    #PBA40 has a couple of different columns
    if ('total_residential_units' in DF1.columns) & ('total_residential_units' in DF2.columns):
        DF1.rename(columns={'total_residential_units': 'RES_UNITS'}, inplace=True)
        DF2.rename(columns={'total_residential_units': 'RES_UNITS'}, inplace=True)
        
    if ('zone_id' in DF1.columns) & ('zone_id' in DF2.columns):
        DF1.rename(columns={'zone_id': 'TAZ'}, inplace=True)
        DF2.rename(columns={'zone_id': 'TAZ'}, inplace=True)    
        
    if ('TAZ' in DF1.columns) & ('TAZ' in DF2.columns):
        DF_merge = DF1.merge(DF2, on = 'TAZ')
        DF_merge['AGREMPN GROWTH'] = DF_merge['AGREMPN_y']-DF_merge['AGREMPN_x']
        DF_merge['FPSEMPN GROWTH'] = DF_merge['FPSEMPN_y']-DF_merge['FPSEMPN_x']
        DF_merge['HEREMPN GROWTH'] = DF_merge['HEREMPN_y']-DF_merge['HEREMPN_x']
        DF_merge['MWTEMPN GROWTH'] = DF_merge['MWTEMPN_y']-DF_merge['MWTEMPN_x']
        DF_merge['OTHEMPN GROWTH'] = DF_merge['OTHEMPN_y']-DF_merge['OTHEMPN_x']
        DF_merge['RETEMPN GROWTH'] = DF_merge['RETEMPN_y']-DF_merge['RETEMPN_x']
        DF_merge['TOTEMP GROWTH'] = DF_merge['TOTEMP_y']-DF_merge['TOTEMP_x']
        DF_merge['HHINCQ1 GROWTH'] = DF_merge['HHINCQ1_y']-DF_merge['HHINCQ1_x']
        DF_merge['HHINCQ2 GROWTH'] = DF_merge['HHINCQ2_y']-DF_merge['HHINCQ2_x']
        DF_merge['HHINCQ3 GROWTH'] = DF_merge['HHINCQ3_y']-DF_merge['HHINCQ3_x']
        DF_merge['HHINCQ4 GROWTH'] = DF_merge['HHINCQ4_y']-DF_merge['HHINCQ4_x']
        DF_merge['HHPOP GROWTH'] = DF_merge['HHPOP_y']-DF_merge['HHPOP_x']
        DF_merge['TOTHH GROWTH'] = DF_merge['TOTHH_y']-DF_merge['TOTHH_x']
        DF_merge['SHPOP62P GROWTH'] = DF_merge['SHPOP62P_y']-DF_merge['SHPOP62P_x']
        DF_merge['GQPOP GROWTH'] = DF_merge['GQPOP_y']-DF_merge['GQPOP_x']
        DF_merge['TOTPOP GROWTH'] = DF_merge['TOTPOP_y']-DF_merge['TOTPOP_x']
        DF_merge['RES_UNITS GROWTH'] = DF_merge['RES_UNITS_y']-DF_merge['RES_UNITS_x']
        DF_merge['MFDU GROWTH'] = DF_merge['MFDU_y']-DF_merge['MFDU_x']
        DF_merge['SFDU GROWTH'] = DF_merge['SFDU_y']-DF_merge['SFDU_x']
        DF_merge['RESACRE GROWTH'] = DF_merge['RESACRE_y']-DF_merge['RESACRE_x']
        DF_merge['EMPRES GROWTH'] = DF_merge['EMPRES_y']-DF_merge['EMPRES_x']
        DF_merge['AGE0004 GROWTH'] = DF_merge['AGE0004_y']-DF_merge['AGE0004_x']
        DF_merge['AGE0519 GROWTH'] = DF_merge['AGE0519_y']-DF_merge['AGE0519_x']
        DF_merge['AGE2044 GROWTH'] = DF_merge['AGE2044_y']-DF_merge['AGE2044_x']
        DF_merge['AGE4564 GROWTH'] = DF_merge['AGE4564_y']-DF_merge['AGE4564_x']
        DF_merge['AGE65P GROWTH'] = DF_merge['AGE65P_y']-DF_merge['AGE65P_x']
            
        TAZ_DF_COLUMNS = ['TAZ',
                         'SD_x',
                         'ZONE_x',
                         'COUNTY_x',
                         'AGREMPN GROWTH',
                         'FPSEMPN GROWTH',
                         'HEREMPN GROWTH',
                         'MWTEMPN GROWTH',
                         'OTHEMPN GROWTH',
                         'RETEMPN GROWTH',
                         'TOTEMP GROWTH',
                         'HHINCQ1 GROWTH',
                         'HHINCQ2 GROWTH',
                         'HHINCQ3 GROWTH',
                         'HHINCQ4 GROWTH',
                         'HHPOP GROWTH',
                         'TOTHH GROWTH',
                         'SHPOP62P GROWTH',
                         'GQPOP GROWTH',
                         'TOTPOP GROWTH',
                         'RES_UNITS GROWTH',
                         'MFDU GROWTH',
                         'SFDU GROWTH',
                         'RESACRE GROWTH',
                         'EMPRES GROWTH',
                         'AGE0004 GROWTH',
                         'AGE0519 GROWTH',
                         'AGE2044 GROWTH',
                         'AGE4564 GROWTH',
                         'AGE65P GROWTH']
        
        DF_TAZ_GROWTH = DF_merge[TAZ_DF_COLUMNS].copy()
        return DF_TAZ_GROWTH
    else:
        print ('Merge cannot be performed')

#A separate calculator for juris, pda, and superdistrct summaries, because they have different columns
def nontaz_calculator(DF1, DF2):
    
    DF_COLUMNS = ['agrempn growth',
                  'fpsempn growth',
                  'herempn growth',
                  'mwtempn growth',
                  'othempn growth',
                  'retempn growth',
                  'totemp growth',
                  'hhincq1 growth',
                  'hhincq2 growth',
                  'hhincq3 growth',
                  'hhincq4 growth',
                  'tothh growth',
                  'mfdu growth',
                  'sfdu growth',
                  'occupancy_rate growth',
                  'non_residential_sqft growth',
                  'deed_restricted_units growth',
                  'inclusionary_units growth',
                  'subsidized_units growth']
    
    if ('juris' in DF1.columns) & ('juris' in DF2.columns):
        DF_merge = DF1.merge(DF2, on = 'juris')
        DF_COLUMNS = ['juris'] + DF_COLUMNS
    #elif ('pda' in DF1.columns) & ('pda' in DF2.columns):
       # DF_merge = DF1.merge(DF2, on = 'pda')
        #DF_COLUMNS = ['pda'] + DF_COLUMNS
    elif ('pda_pba50' in DF1.columns) & ('pda_pba50' in DF2.columns):
        DF_merge = DF1.merge(DF2, on = 'pda_pba50')
        #change to pda to merge with other files
        #but not that PBA40 and DBP used pba40 PDAs, new runs would use pba50 PDAs
        #so technically, pda summaries should be compared for new runs
        DF_COLUMNS = ['pda_pba50'] + DF_COLUMNS #this add only pda instead of pda_pba50 so that this can be joined with 
    elif ('superdistrict' in DF1.columns) & ('superdistrict' in DF2.columns):
        DF_merge = DF1.merge(DF2, on = 'superdistrict')
        DF_COLUMNS = ['superdistrict'] + DF_COLUMNS
    else:
        print ('Merge cannot be performed')
        
    DF_merge['agrempn growth'] = DF_merge['agrempn_y']-DF_merge['agrempn_x']
    DF_merge['fpsempn growth'] = DF_merge['fpsempn_y']-DF_merge['fpsempn_x']
    DF_merge['herempn growth'] = DF_merge['herempn_y']-DF_merge['herempn_x']
    DF_merge['mwtempn growth'] = DF_merge['mwtempn_y']-DF_merge['mwtempn_x']
    DF_merge['othempn growth'] = DF_merge['othempn_y']-DF_merge['othempn_x']
    DF_merge['retempn growth'] = DF_merge['retempn_y']-DF_merge['retempn_x']
    DF_merge['totemp growth'] = DF_merge['totemp_y']-DF_merge['totemp_x']
    DF_merge['hhincq1 growth'] = DF_merge['hhincq1_y']-DF_merge['hhincq1_x']
    DF_merge['hhincq2 growth'] = DF_merge['hhincq2_y']-DF_merge['hhincq2_x']
    DF_merge['hhincq3 growth'] = DF_merge['hhincq3_y']-DF_merge['hhincq3_x']
    DF_merge['hhincq4 growth'] = DF_merge['hhincq4_y']-DF_merge['hhincq4_x']
    DF_merge['tothh growth'] = DF_merge['tothh_y']-DF_merge['tothh_x']
    DF_merge['mfdu growth'] = DF_merge['mfdu_y']-DF_merge['mfdu_x']
    DF_merge['sfdu growth'] = DF_merge['sfdu_y']-DF_merge['sfdu_x']
    DF_merge['occupancy_rate growth'] = DF_merge['occupancy_rate_y']-DF_merge['occupancy_rate_x']
    DF_merge['non_residential_sqft growth'] = DF_merge['non_residential_sqft_y']-DF_merge['non_residential_sqft_x']
    DF_merge['deed_restricted_units growth'] = DF_merge['deed_restricted_units_y']-DF_merge['deed_restricted_units_x']
    DF_merge['inclusionary_units growth'] = DF_merge['inclusionary_units_y']-DF_merge['inclusionary_units_x']
    DF_merge['subsidized_units growth'] = DF_merge['subsidized_units_y']-DF_merge['subsidized_units_x']
        
    DF_GROWTH = DF_merge[DF_COLUMNS].copy()
    return DF_GROWTH

#This is to have an easier way to read summary files, particularly when you don't know the run id, only the folder

#load the file by looking for the file location, geography level, base year, and end year summary files
#for PBA40, baseyear is 2010, and end year is 2040
#for PBA50 (DBP and new runs) baseyear is 2015, and end year is 2050
#return a tuple of baseyear summary file, endyear summary file, and the runid
def FILELOADER(path, geo, baseyear, endyear):
    localpath = ''
    DF = pd.DataFrame()
    #PBA40 has a different pattern for taz files
    if path == PBA40_DIR:
        localpath = path
        if geo == 'taz':
            pattern_baseyear = "(run[0-9]{2,4}c_%s_summaries_%s\.csv)"%(geo, baseyear)
            pattern_endyear  = "(run[0-9]{2,4}c_%s_summaries_%s\.csv)"%(geo, endyear)
        else:
            pattern_baseyear = "(run[0-9]{2,4}_%s_summaries_%s\.csv)"%(geo, baseyear)
            pattern_endyear  = "(run[0-9]{2,4}_%s_summaries_%s\.csv)"%(geo, endyear)
            
    #DBP has a different pattern from all new BP runs        
    elif path == DBP_DIR:
        localpath = os.path.join(URBANSIM_OUTPUT_BOX_DIR, path) #the path is the run folder, must be specificed. 
        pattern_baseyear = "(run[0-9]{2,4}_%s_summaries_%s\.csv)"%(geo, baseyear)
        pattern_endyear  = "(run[0-9]{2,4}_%s_summaries_%s\.csv)"%(geo, endyear)
        
    else:
        if geo == 'pda':    
            localpath = os.path.join(URBANSIM_OUTPUT_BOX_DIR, path) #the path is the run folder, must be specificed. 
            pattern_baseyear = "(run[0-9]{2,4}_%s_pba50_summaries_%s\.csv)"%(geo, baseyear)
            pattern_endyear  = "(run[0-9]{2,4}_%s_pba50_summaries_%s\.csv)"%(geo, endyear)
        else:
            localpath = os.path.join(URBANSIM_OUTPUT_BOX_DIR, path) #the path is the run folder, must be specificed. 
            pattern_baseyear = "(run[0-9]{2,4}_%s_summaries_%s\.csv)"%(geo, baseyear)
            pattern_endyear  = "(run[0-9]{2,4}_%s_summaries_%s\.csv)"%(geo, endyear)            
    
    files_baseyear = [f for f in os.listdir(localpath) if re.match(pattern_baseyear, f)]
    filename_baseyear = files_baseyear[0]
    filepath_baseyear = os.path.join(localpath,filename_baseyear)
    summary_baseyear = pd.read_csv(filepath_baseyear)

    files_endyear = [f for f in os.listdir(localpath) if re.match(pattern_endyear, f)]
    filename_endyear = files_endyear[0]
    filepath_endyear = os.path.join(localpath,filename_endyear)
    summary_endyear = pd.read_csv(filepath_endyear)
    
    runid = filename_baseyear.split('_')[0]
    
    return summary_baseyear, summary_endyear, runid

if __name__ == "__main__":
    
    #process taz file first, since it is different from other files
    GEO = 'taz'
    DF_LIST = []
    
    for path in PATH_LIST:
        #Read PBA40 file
        if path == PBA40_DIR:
            baseyear = 2010
            endyear  = 2040
        else:
            baseyear = 2015
            endyear  = 2050
            
        data_summary =  FILELOADER(path, GEO, baseyear, endyear)
        summary_baseyear = data_summary[0]
        summary_endyear  = data_summary[1]
        summary_runid    = data_summary[2]
    
        #calculate growth and combine files
        DF  = taz_calculator(summary_baseyear, summary_endyear)
        if summary_runid == 'run7224c':
            new_names = [(i,'PBA40_'+ i) for i in DF.iloc[:, 1:].columns.values]
            DF.rename(columns = dict(new_names), inplace=True)
        elif summary_runid == 'run98':
            new_names = [(i,'DBP_'+ i) for i in DF.iloc[:, 1:].columns.values]
            DF.rename(columns = dict(new_names), inplace=True)
        else:
            new_names = [(i,summary_runid +'_'+ i) for i in DF.iloc[:, 1:].columns.values]
            DF.rename(columns = dict(new_names), inplace=True)
        
        DF_LIST.append(DF)
        
    DF_MERGE = reduce(lambda left,right: pd.merge(left, right, on = 'TAZ', how='outer'), DF_LIST)
    DF_MERGE.reset_index(drop=True, inplace=True)
    DF_MERGE.to_csv(OUTPUT_FILE.format(GEO))
    
    #then process other geography summaries     
    GEO = ['pda','juris','superdistrict']
    DF_LIST = []
                    
    for geo in GEO:
        #PDA summary comparisons should exclude PBA40 and DBP, because they used PBA40 PDAs,
        #for PBA50 PDAs, only include new runs
        if geo =='pda':
            
            PATH_LIST_v2 = filter(lambda x: (x != PBA40_DIR)&(x != DBP_DIR),PATH_LIST)
            baseyear = 2015
            endyear  = 2050
                        
            for path in PATH_LIST_v2:
                data_summary =  FILELOADER(path, geo, baseyear, endyear)
                summary_baseyear = data_summary[0]
                summary_endyear  = data_summary[1]
                summary_runid    = data_summary[2]
    
                #calculate growth and combine files
                DF  = nontaz_calculator(summary_baseyear, summary_endyear)
                new_names = [(i,summary_runid +'_'+ i) for i in DF.iloc[:, 1:].columns.values]
                DF.rename(columns = dict(new_names), inplace=True)
        
                DF_LIST.append(DF)
        
            DF_MERGE = reduce(lambda left,right: pd.merge(left, right, on = 'pda_pba50', how='outer'), DF_LIST)
            DF_MERGE.reset_index(drop=True, inplace=True)
            DF_MERGE.to_csv(OUTPUT_FILE.format(geo))                
            DF_LIST = []
        else:
            for path in PATH_LIST:
            #Read PBA40 file
                if path == PBA40_DIR:
                    baseyear = 2010
                    endyear  = 2040
                else:
                    baseyear = 2015
                    endyear  = 2050
            
                data_summary =  FILELOADER(path, geo, baseyear, endyear)
                summary_baseyear = data_summary[0]
                summary_endyear  = data_summary[1]
                summary_runid    = data_summary[2]
    
                #calculate growth and combine files
                DF  = nontaz_calculator(summary_baseyear, summary_endyear)
                if summary_runid == 'run7224':
                    new_names = [(i,'PBA40_'+ i) for i in DF.iloc[:, 1:].columns.values]
                    DF.rename(columns = dict(new_names), inplace=True)
                elif summary_runid == 'run98':
                    new_names = [(i,'DBP_'+ i) for i in DF.iloc[:, 1:].columns.values]
                    DF.rename(columns = dict(new_names), inplace=True)
                else:
                    new_names = [(i,summary_runid +'_'+ i) for i in DF.iloc[:, 1:].columns.values]
                    DF.rename(columns = dict(new_names), inplace=True)
                DF_LIST.append(DF)
            
            DF_MERGE = reduce(lambda left,right: pd.merge(left, right, on = geo, how='outer'), DF_LIST)
            DF_MERGE.sort_values(geo, inplace=True)
            DF_MERGE.reset_index(drop=True, inplace=True)
            DF_MERGE.to_csv(OUTPUT_FILE.format(geo))
            DF_LIST = []        



