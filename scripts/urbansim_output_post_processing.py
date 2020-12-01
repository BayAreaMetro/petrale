
# coding: utf-8


#The script is used for process geograpy summary files and combine different run results for visualization in Tableau
import pandas as pd
import numpy as np
import os
import re
from functools import reduce


#PBA40 folder
PBA40_DIR                  = os.path.join(os.environ["USERPROFILE"],
                            "Box/Modeling and Surveys/Share Data/plan-bay-area-2040/RTP17 UrbanSim Output/r7224c")

# The location of Urbansim outputs
URBANSIM_OUTPUT_BOX_DIR    = os.path.join(os.environ["USERPROFILE"],
                            "Box/Modeling and Surveys/Urban Modeling/Bay Area UrbanSim/PBA50")

# Final draft blueprint output
DBP_DIR                    = "Draft Blueprint runs/Blueprint Plus Crossing (s23)/v1.7.1- FINAL DRAFT BLUEPRINT"

# Add new runs here: for comparison -- using v1.8 as a placeholder for now
FBP_v3                      = "Final Blueprint runs/Final Blueprint (s24)/BAUS v2.2.1 (growth summary updates)"
FBP_v4                      = 'Final Blueprint runs/Final Blueprint (s24)/BAUS v2.3.1 (devproj updates)'
FBP_v5                      = 'Final Blueprint runs/Final Blueprint (s24)/BAUS v2.4'
FBP_v6                      = 'Final Blueprint runs/Final Blueprint (s24)/BAUS v2.5'
FBP_v7                      = 'Final Blueprint runs/Final Blueprint (s24)/BAUS v2.6.1 (growth summary updates)'
FBP_v8                      = 'Final Blueprint runs/Final Blueprint (s24)/BAUS v2.7'
FBP_v9                      = 'Final Blueprint runs/Final Blueprint (s24)/BAUS v2.8'
FBP_v10                    = "Final Blueprint runs/Final Blueprint (s24)/BAUS v2.8.1 (parcels geography update)"
FBP_v11                    = "Final Blueprint runs/Final Blueprint (s24)/BAUS v2.9"
FBP_v12                    = "Final Blueprint runs/Final Blueprint (s24)/BAUS v2.10"
FBP_v13                    = "Final Blueprint runs/Final Blueprint (s24)/BAUS v2.11"
FBP_v14                    = "Final Blueprint runs/Final Blueprint (s24)/BAUS v2.12"
FBP_v15                    = "Final Blueprint runs/Final Blueprint (s24)/BAUS v2.15"
FBP_v16                    = "Final Blueprint runs/Final Blueprint (s24)/BAUS v2.16"
FBP_v19                    = "Final Blueprint runs/Final Blueprint (s24)/BAUS v2.19"
FBP_v20                    = "Final Blueprint runs/Final Blueprint (s24)/BAUS v2.20.1 (adds project to devproj)"
FBP_v23                    = "Final Blueprint runs/Final Blueprint (s24)/BAUS v2.23"
FBP_v24                    = "Final Blueprint runs/Final Blueprint (s24)/BAUS v2.24"
FBP_v25                    = "Final Blueprint runs/Final Blueprint (s24)/BAUS v2.25"
FBP_v26                    = "Final Blueprint runs/Final Blueprint (s24)/BAUS v2.26"

# A list of paths of runs, which would be read and produce summaries altogether
PATH_LIST                  = [PBA40_DIR, DBP_DIR, FBP_v25, FBP_v26] # ---Add new run paths to this list---
PATH_LIST_PARCEL           = [DBP_DIR, FBP_v25, FBP_v26]

#Visualization folder
VIZ                        = "Visualizations"

#Output will into this workbook
OUTPUT_FILE                = os.path.join(URBANSIM_OUTPUT_BOX_DIR, VIZ, 
                                         "PBA50_growth_{}_allruns.csv")

#Parcel_geography
PARCEL_GEO_DIR          = "Current PBA50 Large General Input Data/2020_10_27_parcels_geography.csv"

juris_to_county = {'alameda' : 'Alameda',
'albany' : 'Alameda',
'american_canyon' : 'Napa',
'antioch' : 'Contra Costa',
'atherton' : 'San Mateo',
'belmont' : 'San Mateo',
'belvedere' : 'Marin',
'benicia' : 'Solano',
'berkeley' : 'Alameda',
'brentwood' : 'Contra Costa',
'brisbane' : 'San Mateo',
'burlingame' : 'San Mateo',
'calistoga' : 'Napa',
'campbell' : 'Santa Clara',
'clayton' : 'Contra Costa',
'cloverdale' : 'Sonoma',
'colma' : 'San Mateo',
'concord' : 'Contra Costa',
'corte_madera' : 'Marin',
'cotati' : 'Sonoma',
'cupertino' : 'Santa Clara',
'daly_city' : 'San Mateo',
'danville' : 'Contra Costa',
'dixon' : 'Solano',
'dublin' : 'Alameda',
'east_palo_alto' : 'San Mateo',
'el_cerrito' : 'Contra Costa',
'emeryville' : 'Alameda',
'fairfax' : 'Marin',
'fairfield' : 'Solano',
'foster_city' : 'San Mateo',
'fremont' : 'Alameda',
'gilroy' : 'Santa Clara',
'half_moon_bay' : 'San Mateo',
'hayward' : 'Alameda',
'healdsburg' : 'Sonoma',
'hercules' : 'Contra Costa',
'hillsborough' : 'San Mateo',
'lafayette' : 'Contra Costa',
'larkspur' : 'Marin',
'livermore' : 'Alameda',
'los_altos' : 'Santa Clara',
'los_altos_hills' : 'Santa Clara',
'los_gatos' : 'Santa Clara',
'martinez' : 'Contra Costa',
'menlo_park' : 'San Mateo',
'millbrae' : 'San Mateo',
'mill_valley' : 'Marin',
'milpitas' : 'Santa Clara',
'monte_sereno' : 'Santa Clara',
'moraga' : 'Contra Costa',
'morgan_hill' : 'Santa Clara',
'mountain_view' : 'Santa Clara',
'napa' : 'Napa',
'newark' : 'Alameda',
'novato' : 'Marin',
'oakland' : 'Alameda',
'oakley' : 'Contra Costa',
'orinda' : 'Contra Costa',
'pacifica' : 'San Mateo',
'palo_alto' : 'Santa Clara',
'petaluma' : 'Sonoma',
'piedmont' : 'Alameda',
'pinole' : 'Contra Costa',
'pittsburg' : 'Contra Costa',
'pleasant_hill' : 'Contra Costa',
'pleasanton' : 'Alameda',
'portola_valley' : 'San Mateo',
'redwood_city' : 'San Mateo',
'richmond' : 'Contra Costa',
'rio_vista' : 'Solano',
'rohnert_park' : 'Sonoma',
'ross' : 'Marin',
'st_helena' : 'Napa',
'san_anselmo' : 'Marin',
'san_bruno' : 'San Mateo',
'san_carlos' : 'San Mateo',
'san_francisco' : 'San Francisco',
'san_jose' : 'Santa Clara',
'san_leandro' : 'Alameda',
'san_mateo' : 'San Mateo',
'san_pablo' : 'Contra Costa',
'san_rafael' : 'Marin',
'san_ramon' : 'Contra Costa',
'santa_clara' : 'Santa Clara',
'santa_rosa' : 'Sonoma',
'saratoga' : 'Santa Clara',
'sausalito' : 'Marin',
'sebastopol' : 'Sonoma',
'sonoma' : 'Sonoma',
'south_san_francisco' : 'San Mateo',
'suisun_city' : 'Solano',
'sunnyvale' : 'Santa Clara',
'tiburon' : 'Marin',
'union_city' : 'Alameda',
'vacaville' : 'Solano',
'vallejo' : 'Solano',
'walnut_creek' : 'Contra Costa',
'windsor' : 'Sonoma',
'woodside' : 'San Mateo',
'yountville' : 'Napa',
'unincorporated_alameda' : "Alameda",
'unincorporated_contra_costa' : "Contra Costa",
'unincorporated_marin' : "Marin",
'unincorporated_napa' : "Napa",
'unincorporated_san_francisco' : "San Francisco",
'unincorporated_san_mateo' : "San Mateo",
'unincorporated_santa_clara' : "Santa Clara",
'unincorporated_solano' : "Solano",
'unincorporated_sonoma' : "Sonoma"}

cn_to_county = {1 : 'San Francisco',
                2 : 'San Mateo',
                3 : 'Santa Clara',
                4 : 'Alameda',
                5 : 'Contra Costa',
                6 : 'Solano',
                7 : 'Napa',
                8 : 'Sonoma',
                9 : 'Marin'}

sd_mapping = {1 : 'Greater Downtown San Francisco',
              2 : 'San Francisco Richmond District',
              3 : 'San Francisco Mission District',
              4 : 'San Francisco Sunset District',
              5 : 'Daly City and San Bruno',
              6 : 'San Mateo and Burlingame',
              7 : 'Redwood City and Menlo Park',
              8 : 'Palo Alto and Los Altos',
              9 : 'Sunnyvale and Mountain View',
              10 : 'Cupertino and Saratoga',
              11 : 'Central San Jose',
              12 : 'Milpitas and East San Jose',
              13 : 'South San Jose',
              14 : 'Gilroy and Morgan Hill',
              15 : 'Livermore and Pleasanton',
              16 : 'Fremont and Union City',
              17 : 'Hayward and San Leandro',
              18 : 'Oakland and Alameda',
              19 : 'Berkeley and Albany',
              20 : 'Richmond and El Cerrito',
              21 : 'Concord and Martinez',
              22 : 'Walnut Creek',
              23 : 'Danville and San Ramon',
              24 : 'Antioch and Pittsburg',
              25 : 'Vallejo and Benicia',
              26 : 'Fairfield and Vacaville',
              27 : 'Napa',
              28 : 'St Helena',
              29 : 'Petaluma and Rohnert Park',
              30 : 'Santa Rosa and Sebastopol',
              31 : 'Healdsburg and cloverdale',
              32 : 'Novato',
              33 : 'San Rafael',
              34 : 'Mill Valley and Sausalito'}

#calculate growth at the regional level for main variables using taz summaries
def county_calculator(DF1, DF2):
    if ('zone_id' in DF1.columns) & ('zone_id' in DF2.columns):
        DF1.rename(columns={'zone_id': 'TAZ'}, inplace=True)
        DF2.rename(columns={'zone_id': 'TAZ'}, inplace=True)    
        
    if ('TAZ' in DF1.columns) & ('TAZ' in DF2.columns):
        DF_merge = DF1.merge(DF2, on = 'TAZ').fillna(0)
        DF_merge['TOTPOP GROWTH'] = DF_merge['TOTPOP_y']-DF_merge['TOTPOP_x']
        DF_merge['TOTEMP GROWTH'] = DF_merge['TOTEMP_y']-DF_merge['TOTEMP_x']
        DF_merge['AGREMPN GROWTH'] = DF_merge['AGREMPN_y']-DF_merge['AGREMPN_x']
        DF_merge['FPSEMPN GROWTH'] = DF_merge['FPSEMPN_y']-DF_merge['FPSEMPN_x']
        DF_merge['HEREMPN GROWTH'] = DF_merge['HEREMPN_y']-DF_merge['HEREMPN_x']
        DF_merge['MWTEMPN GROWTH'] = DF_merge['MWTEMPN_y']-DF_merge['MWTEMPN_x']
        DF_merge['OTHEMPN GROWTH'] = DF_merge['OTHEMPN_y']-DF_merge['OTHEMPN_x']
        DF_merge['RETEMPN GROWTH'] = DF_merge['RETEMPN_y']-DF_merge['RETEMPN_x']
        DF_merge['TOTHH GROWTH'] = DF_merge['TOTHH_y']-DF_merge['TOTHH_x']
        DF_merge['HHINCQ1 GROWTH'] = DF_merge['HHINCQ1_y']-DF_merge['HHINCQ1_x']
        DF_merge['HHINCQ2 GROWTH'] = DF_merge['HHINCQ2_y']-DF_merge['HHINCQ2_x']
        DF_merge['HHINCQ3 GROWTH'] = DF_merge['HHINCQ3_y']-DF_merge['HHINCQ3_x']
        DF_merge['HHINCQ4 GROWTH'] = DF_merge['HHINCQ4_y']-DF_merge['HHINCQ4_x']
        
        if 'COUNTY_x' in DF_merge.columns:
            DF_merge['COUNTY_NAME_x'] = DF_merge['COUNTY_x'].map(cn_to_county)
            DF_CO_GRWTH = DF_merge.groupby(['COUNTY_NAME_x']).sum().reset_index()
        if 'COUNTY_NAME_x' in DF_merge.columns:
            DF_CO_GRWTH = DF_merge.groupby(['COUNTY_NAME_x']).sum().reset_index()

        DF_CO_GRWTH['TOTEMP GROWTH SHR'] = DF_CO_GRWTH['TOTEMP GROWTH']/(DF_CO_GRWTH['TOTEMP_y'].sum()-DF_CO_GRWTH['TOTEMP_x'].sum())
        DF_CO_GRWTH['TOTHH GROWTH SHR'] = DF_CO_GRWTH['TOTHH GROWTH']/(DF_CO_GRWTH['TOTHH_y'].sum()-DF_CO_GRWTH['TOTHH_x'].sum())

        DF_CO_GRWTH['TOTEMP PCT GROWTH'] = DF_CO_GRWTH['TOTEMP_y']/DF_CO_GRWTH['TOTEMP_x']-1
        DF_CO_GRWTH['TOTHH PCT GROWTH'] = DF_CO_GRWTH['TOTHH_y']/DF_CO_GRWTH['TOTHH_x']-1

        DF_CO_GRWTH['TOTEMP SHR CHNG'] = DF_CO_GRWTH['TOTEMP_y']/DF_CO_GRWTH['TOTEMP_y'].sum()-DF_CO_GRWTH['TOTEMP_x']/DF_CO_GRWTH['TOTEMP_x'].sum()
        DF_CO_GRWTH['TOTHH SHR CHNG'] = DF_CO_GRWTH['TOTHH_y']/DF_CO_GRWTH['TOTHH_y'].sum()-DF_CO_GRWTH['TOTHH_x']/DF_CO_GRWTH['TOTHH_x'].sum()

        DF_COLUMNS = ['COUNTY_NAME_x',
                      'TOTPOP GROWTH',
                      'TOTEMP GROWTH',
                      'AGREMPN GROWTH',
                      'FPSEMPN GROWTH',
                      'HEREMPN GROWTH',
                      'MWTEMPN GROWTH',
                      'OTHEMPN GROWTH',
                      'RETEMPN GROWTH',
                      'TOTHH GROWTH',
                      'HHINCQ1 GROWTH',
                      'HHINCQ2 GROWTH',
                      'HHINCQ3 GROWTH',
                      'HHINCQ4 GROWTH',
                      'TOTEMP GROWTH SHR',
                      'TOTHH GROWTH SHR',
                      'TOTEMP PCT GROWTH',
                      'TOTHH PCT GROWTH',
                      'TOTEMP SHR CHNG',
                      'TOTHH SHR CHNG']

        DF_CO_GRWTH = DF_CO_GRWTH[DF_COLUMNS].copy()
        DF_CO_GRWTH = DF_CO_GRWTH.rename(columns={'COUNTY_NAME_x': 'county'})

        return DF_CO_GRWTH
    else:
        print ('Merge cannot be performed')

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
        DF_merge = DF1.merge(DF2, on = 'TAZ').fillna(0)
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
        DF_merge['TOTHH GROWTH'] = DF_merge['TOTHH_y']-DF_merge['TOTHH_x']
        DF_merge['TOTPOP GROWTH'] = DF_merge['TOTPOP_y']-DF_merge['TOTPOP_x']
        DF_merge['RES_UNITS GROWTH'] = DF_merge['RES_UNITS_y']-DF_merge['RES_UNITS_x']
        DF_merge['MFDU GROWTH'] = DF_merge['MFDU_y']-DF_merge['MFDU_x']
        DF_merge['SFDU GROWTH'] = DF_merge['SFDU_y']-DF_merge['SFDU_x']

        DF_merge['TOTEMP GROWTH SHR'] = DF_merge['TOTEMP GROWTH']/(DF_merge['TOTEMP_y'].sum()/DF_merge['TOTEMP_x'].sum())
        DF_merge['TOTHH GROWTH SHR'] = DF_merge['TOTHH GROWTH']/(DF_merge['TOTHH_y'].sum()/DF_merge['TOTHH_x'].sum())

        DF_merge['TOTEMP PCT GROWTH'] = DF_merge['TOTEMP_y']/DF_merge['TOTEMP_x']-1
        DF_merge['TOTHH PCT GROWTH'] = DF_merge['TOTHH_y']/DF_merge['TOTHH_x']-1

        DF_merge['TOTEMP SHR CHNG'] = DF_merge['TOTEMP_y']/DF_merge['TOTEMP_y'].sum()-DF_merge['TOTEMP_x']/DF_merge['TOTEMP_x'].sum()
        DF_merge['TOTHH SHR CHNG'] = DF_merge['TOTHH_y']/DF_merge['TOTHH_y'].sum()-DF_merge['TOTHH_x']/DF_merge['TOTHH_x'].sum()

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
                         'TOTHH GROWTH',
                         'TOTPOP GROWTH',
                         'RES_UNITS GROWTH',
                         'MFDU GROWTH',
                         'TOTEMP GROWTH SHR',
                         'TOTHH GROWTH SHR',
                         'TOTEMP PCT GROWTH',
                         'TOTHH PCT GROWTH',
                         'TOTEMP SHR CHNG',
                         'TOTHH SHR CHNG']
        
        DF_TAZ_GROWTH = DF_merge[TAZ_DF_COLUMNS].copy()
        DF_TAZ_GROWTH = DF_TAZ_GROWTH.rename(columns={'SD_x': 'SD', 'ZONE_x': 'ZONE', 'COUNTY_x': 'COUNTY'})
        DF_TAZ_GROWTH['SD_NAME'] = DF_TAZ_GROWTH['SD'].map(sd_mapping)
        DF_TAZ_GROWTH['CNTY_NAME'] = DF_TAZ_GROWTH['COUNTY'].map(cn_to_county)

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
                  'nonres_sqft growth',
                  'dr_units growth',
                  'incl_units growth',
                  'subsd_units growth',
                  'totemp growth shr',
                  'tothh growth shr',
                  'totemp pct growth',
                  'tothh pct growth',
                  'totemp shr chng',
                  'tothh shr chng']
    
    if ('juris' in DF1.columns) & ('juris' in DF2.columns):
        DF_merge = DF1.merge(DF2, on = 'juris').fillna(0)
        DF_COLUMNS = ['juris'] + DF_COLUMNS
    elif ('superdistrict' in DF1.columns) & ('superdistrict' in DF2.columns):
        DF_merge = DF1.merge(DF2, on = 'superdistrict').fillna(0)
        DF_merge['sd_name'] = DF_merge['superdistrict'].map(sd_mapping)
        DF_COLUMNS = ['superdistrict','sd_name'] + DF_COLUMNS        
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
    DF_merge['nonres_sqft growth'] = DF_merge['non_residential_sqft_y']-DF_merge['non_residential_sqft_x']
    DF_merge['dr_units growth'] = DF_merge['deed_restricted_units_y']-DF_merge['deed_restricted_units_x']
    DF_merge['incl_units growth'] = DF_merge['inclusionary_units_y']-DF_merge['inclusionary_units_x']
    DF_merge['subsd_units growth'] = DF_merge['subsidized_units_y']-DF_merge['subsidized_units_x']

    DF_merge['totemp growth shr'] = DF_merge['totemp growth']/(DF_merge['totemp_y'].sum()-DF_merge['totemp_x'].sum())
    DF_merge['tothh growth shr'] = DF_merge['tothh growth']/(DF_merge['tothh_y'].sum()-DF_merge['tothh_x'].sum())

    DF_merge['totemp pct growth'] = DF_merge['totemp_y']/DF_merge['totemp_x']-1
    DF_merge['tothh pct growth'] = DF_merge['tothh_y']/DF_merge['tothh_x']-1
    
    DF_merge['totemp shr chng'] = DF_merge['totemp_y']/DF_merge['totemp_y'].sum()-DF_merge['totemp_x']/DF_merge['totemp_x'].sum()
    DF_merge['tothh shr chng'] = DF_merge['tothh_y']/DF_merge['tothh_y'].sum()-DF_merge['tothh_x']/DF_merge['tothh_x'].sum()

    DF_GROWTH = DF_merge[DF_COLUMNS].copy()
    
    return DF_GROWTH

#This is to have an easier way to read summary files, particularly when you don't know the run id, only the folder

#load the file by looking for the file location, geography level, base year, and end year summary files
#for PBA40, baseyear is 2010, and end year is 2040
#for PBA50 (DBP and new runs) baseyear is 2015, and end year is 2050
#return a tuple of baseyear summary file, endyear summary file, and the runid
def FILELOADER(path, geo, baseyear, endyear):
    localpath = ''
    #PBA40 has a different pattern for taz files
    if path == PBA40_DIR:
        localpath = path
        if geo == 'taz':
            pattern_baseyear = "(run[0-9]{1,4}c_%s_summaries_%s.csv)"%(geo, baseyear)
            pattern_endyear  = "(run[0-9]{1,4}c_%s_summaries_%s.csv)"%(geo, endyear)
        else:
            pattern_baseyear = "(run[0-9]{1,4}_%s_summaries_%s.csv)"%(geo, baseyear)
            pattern_endyear  = "(run[0-9]{1,4}_%s_summaries_%s.csv)"%(geo, endyear)
            
    #DBP has a different pattern from all new BP runs        
    else:
        localpath = os.path.join(URBANSIM_OUTPUT_BOX_DIR, path) #the path is the run folder, must be specificed. 
        pattern_baseyear = "(run[0-9]{1,4}_%s_summaries_%s.csv)"%(geo, baseyear)
        pattern_endyear  = "(run[0-9]{1,4}_%s_summaries_%s.csv)"%(geo, endyear)     
    
    files_baseyear = [f for f in os.listdir(localpath) if re.match(pattern_baseyear, f)]
    filename_baseyear = files_baseyear[0]
    filepath_baseyear = os.path.join(localpath,filename_baseyear)
    summary_baseyear = pd.read_csv(filepath_baseyear)

    files_endyear = [f for f in os.listdir(localpath) if re.match(pattern_endyear, f)]
    filename_endyear = files_endyear[0]
    filepath_endyear = os.path.join(localpath,filename_endyear)
    summary_endyear = pd.read_csv(filepath_endyear)
    
    version = path.split('/')[-1]
    
    return summary_baseyear, summary_endyear, version

#This is to define a separate fileloader for parcel difference data. With the zoningmod category, we should be able to
#summarize growth by different geography types that is more nuanced.
def GEO_SUMMARY_LOADER(path, geo, baseyear, endyear):
    localpath = os.path.join(URBANSIM_OUTPUT_BOX_DIR, path)
    parcel_baseyear_pattern = "(run[0-9]{1,4}_parcel_data_%s.csv)"%(baseyear)
    parcel_endyear_pattern = "(run[0-9]{1,4}_parcel_data_%s.csv)"%(endyear)
    
    parcel_baseyear_search = [f for f in os.listdir(localpath) if re.match(parcel_baseyear_pattern, f)]
    filename_parcel_baseyear =  parcel_baseyear_search[0]
    parcel_baseyear_filepath = os.path.join(localpath,filename_parcel_baseyear)
    parcel_baseyear = pd.read_csv(parcel_baseyear_filepath)
    
    parcel_endyear_search = [f for f in os.listdir(localpath) if re.match(parcel_endyear_pattern, f)]
    filename_parcel_endyear =  parcel_endyear_search[0]
    parcel_endyear_filepath = os.path.join(localpath,filename_parcel_endyear)
    parcel_endyear = pd.read_csv(parcel_endyear_filepath)
    
    version = path.split('/')[-1]
    

    parcel_geobase_file = pd.read_csv(os.path.join(URBANSIM_OUTPUT_BOX_DIR, PARCEL_GEO_DIR))
    parcel_geobase_file_r = parcel_geobase_file[['PARCEL_ID','juris','fbpchcat']]
    parcel_baseyear = parcel_baseyear[['parcel_id','tothh','totemp', 'hhq1','hhq2','hhq3','hhq4']]
    parcel_endyear = parcel_endyear[['parcel_id','tothh','totemp', 'hhq1','hhq2','hhq3','hhq4']]
    parcel_merge = parcel_baseyear.merge(parcel_endyear, on = 'parcel_id').fillna(0)
    parcel_data = parcel_geobase_file_r.merge(parcel_merge, left_on = 'PARCEL_ID',                                                     right_on = 'parcel_id', how = 'left')
    #else:
        #parcel_baseyear = parcel_baseyear[['parcel_id','tothh','totemp', 'hhq1','hhq2','hhq3','hhq4']]
        #parcel_endyear = parcel_endyear[['parcel_id','tothh','totemp', 'hhq1','hhq2','hhq3','hhq4','juris','pba50chcat']]
        #parcel_data = parcel_baseyear.merge(parcel_endyear, on = 'parcel_id', how = 'left').fillna(0)
    
    parcel_data['totemp diff'] = parcel_data['totemp_y']-parcel_data['totemp_x']
    parcel_data['tothh diff'] = parcel_data['tothh_y']-parcel_data['tothh_x']
    parcel_data['hhq1 diff'] = parcel_data['hhq1_y']-parcel_data['hhq1_x']
    parcel_data['hhq2 diff'] = parcel_data['hhq2_y']-parcel_data['hhq2_x']
    parcel_data['hhq3 diff'] = parcel_data['hhq3_y']-parcel_data['hhq3_x']
    parcel_data['hhq4 diff'] = parcel_data['hhq4_y']-parcel_data['hhq4_x']

    parcel_data = parcel_data[['parcel_id','tothh diff','totemp diff','hhq1 diff',                               'hhq2 diff','hhq3 diff','hhq4 diff','juris','fbpchcat']].copy()
        
    #geography summaries
    parcel_geo = parcel_data.loc[parcel_data['fbpchcat'].str.contains(geo, na=False)]
    parcel_geo = parcel_geo.groupby(['juris']).agg({'tothh diff':'sum','totemp diff':'sum',                                                        'hhq1 diff':'sum', 'hhq2 diff':'sum',                                                         'hhq3 diff':'sum', 'hhq4 diff':'sum', }).reset_index()
    parcel_geo['geo_category'] = 'yes_%s'%(geo)
    parcel_geo_no = parcel_data.loc[~parcel_data['fbpchcat'].str.contains(geo, na=False)]
    parcel_geo_no = parcel_geo_no.groupby(['juris']).agg({'tothh diff':'sum','totemp diff':'sum',                                                        'hhq1 diff':'sum', 'hhq2 diff':'sum',                                                         'hhq3 diff':'sum', 'hhq4 diff':'sum', }).reset_index()
    parcel_geo_no['geo_category'] = 'no_%s'%(geo)
    
    parcel_geo_summary = pd.concat([parcel_geo, parcel_geo_no], ignore_index = True)
    parcel_geo_summary.sort_values(by = 'juris', inplace = True)
    parcel_geo_summary['VERSION'] = version
    
    return parcel_geo_summary


##Similar to above, this is to define a separate fileloader to produce summaries for overlapping geographies. W
def TWO_GEO_SUMMARY_LOADER(path, geo1, geo2, baseyear, endyear):
    localpath = os.path.join(URBANSIM_OUTPUT_BOX_DIR, path)
    parcel_baseyear_pattern = "(run[0-9]{1,4}_parcel_data_%s.csv)"%(baseyear)
    parcel_endyear_pattern = "(run[0-9]{1,4}_parcel_data_%s.csv)"%(endyear)
    
    parcel_baseyear_search = [f for f in os.listdir(localpath) if re.match(parcel_baseyear_pattern, f)]
    filename_parcel_baseyear =  parcel_baseyear_search[0]
    parcel_baseyear_filepath = os.path.join(localpath,filename_parcel_baseyear)
    parcel_baseyear = pd.read_csv(parcel_baseyear_filepath)
    
    parcel_endyear_search = [f for f in os.listdir(localpath) if re.match(parcel_endyear_pattern, f)]
    filename_parcel_endyear =  parcel_endyear_search[0]
    parcel_endyear_filepath = os.path.join(localpath,filename_parcel_endyear)
    parcel_endyear = pd.read_csv(parcel_endyear_filepath)
    
    version = path.split('/')[-1]
    
    #if path == DBP_DIR:
    parcel_geobase_file = pd.read_csv(os.path.join(URBANSIM_OUTPUT_BOX_DIR, PARCEL_GEO_DIR))
    parcel_geobase_file_r = parcel_geobase_file[['PARCEL_ID','juris','fbpchcat']]
    parcel_baseyear = parcel_baseyear[['parcel_id','tothh','totemp', 'hhq1','hhq2','hhq3','hhq4']]
    parcel_endyear = parcel_endyear[['parcel_id','tothh','totemp', 'hhq1','hhq2','hhq3','hhq4']]
    parcel_merge = parcel_baseyear.merge(parcel_endyear, on = 'parcel_id').fillna(0)
    parcel_data = parcel_geobase_file_r.merge(parcel_merge, left_on = 'PARCEL_ID',                                                     right_on = 'parcel_id', how = 'left')
    #else:
        #parcel_baseyear = parcel_baseyear[['parcel_id','tothh','totemp', 'hhq1','hhq2','hhq3','hhq4']]
        #parcel_endyear = parcel_endyear[['parcel_id','tothh','totemp', 'hhq1','hhq2','hhq3','hhq4','juris','fbpchcat']]
        #parcel_data = parcel_baseyear.merge(parcel_endyear, on = 'parcel_id', how = 'left').fillna(0)
    
    parcel_data['totemp diff'] = parcel_data['totemp_y']-parcel_data['totemp_x']
    parcel_data['tothh diff'] = parcel_data['tothh_y']-parcel_data['tothh_x']
    parcel_data['hhq1 diff'] = parcel_data['hhq1_y']-parcel_data['hhq1_x']
    parcel_data['hhq2 diff'] = parcel_data['hhq2_y']-parcel_data['hhq2_x']
    parcel_data['hhq3 diff'] = parcel_data['hhq3_y']-parcel_data['hhq3_x']
    parcel_data['hhq4 diff'] = parcel_data['hhq4_y']-parcel_data['hhq4_x']

    parcel_data = parcel_data[['parcel_id','tothh diff','totemp diff','hhq1 diff',                               'hhq2 diff','hhq3 diff','hhq4 diff','juris','fbpchcat']].copy()
    
    #two geographies
    parcel_geo2 = parcel_data.loc[parcel_data['fbpchcat'].str.contains(geo1, na=False)]
    parcel_geo2 = parcel_geo2.loc[parcel_geo2['fbpchcat'].str.contains(geo2, na=False)]
    parcel_geo2_group = parcel_geo2.groupby(['juris']).agg({'tothh diff':'sum','totemp diff':'sum',                                                        'hhq1 diff':'sum', 'hhq2 diff':'sum',                                                         'hhq3 diff':'sum', 'hhq4 diff':'sum', }).reset_index()
    parcel_geo2_group['geo_category'] = 'yes_%s'%(geo1+geo2)
    
    parcel_geo2_no_1 = parcel_data.loc[parcel_data['fbpchcat'].str.contains(geo1, na=False)]
    parcel_geo2_no_1 = parcel_geo2_no_1.loc[~parcel_geo2_no_1['fbpchcat'].str.contains(geo2, na=False)]
    parcel_geo2_no_2 = parcel_data.loc[parcel_data['fbpchcat'].str.contains(geo2, na=False)]
    parcel_geo2_no_2 = parcel_geo2_no_2.loc[~parcel_geo2_no_2['fbpchcat'].str.contains(geo1, na=False)]
    parcel_geo2_no_3 = parcel_data.loc[~parcel_data['fbpchcat'].str.contains(geo1 + "|" + geo2, na=False)]
    
    parcel_geo2_no = pd.concat([parcel_geo2_no_1, parcel_geo2_no_2, parcel_geo2_no_3], ignore_index = True)
    parcel_geo2_no_group = parcel_geo2_no.groupby(['juris']).agg({'tothh diff':'sum','totemp diff':'sum',                                                        'hhq1 diff':'sum', 'hhq2 diff':'sum',                                                         'hhq3 diff':'sum', 'hhq4 diff':'sum', }).reset_index()
    parcel_geo2_no_group['geo_category'] = 'no_%s'%(geo1+geo2)
    
    parcel_geo2_summary = pd.concat([parcel_geo2_group, parcel_geo2_no_group], ignore_index = True)
    parcel_geo2_summary['VERSION'] = version
    
    return parcel_geo2_summary

if __name__ == "__main__":
    
    #process taz file first, since it is different from other files
    GEO = 'taz'
    DF_LIST = []
    DF_COUNTY_LIST = []
    
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
        
        DF_COUNTY = county_calculator(summary_baseyear, summary_endyear)
        if summary_runid == 'run7224c':
            new_names = [(i,'PBA40_'+ i) for i in DF_COUNTY.iloc[:, 1:].columns.values]
            DF_COUNTY.rename(columns = dict(new_names), inplace=True)
        elif summary_runid == 'run98':
            new_names = [(i,'DBP_'+ i) for i in DF_COUNTY.iloc[:, 1:].columns.values]
            DF_COUNTY.rename(columns = dict(new_names), inplace=True)
        else:
            new_names = [(i,summary_runid +'_'+ i) for i in DF_COUNTY.iloc[:, 1:].columns.values]
            DF_COUNTY.rename(columns = dict(new_names), inplace=True)

        DF_COUNTY_LIST.append(DF_COUNTY)
        
    DF_MERGE = reduce(lambda left,right: pd.merge(left, right, on = 'TAZ', how='outer'), DF_LIST)
    DF_MERGE.to_csv(OUTPUT_FILE.format(GEO), index = False)

    DF_COUNTY_MERGE = reduce(lambda left,right: pd.merge(left, right, on = 'county', how='outer'), DF_COUNTY_LIST)
    DF_COUNTY_MERGE.to_csv(OUTPUT_FILE.format('county'), index = False)
    
    #then process other geography summaries     
    GEO = ['juris','superdistrict']
    DF_LIST = []
                    
    for geo in GEO:
        #PDA summary comparisons should exclude PBA40 and DBP, because they used PBA40 PDAs,
        #for PBA50 PDAs, only include new runs
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
            
        DF_MERGE = reduce(lambda left,right: pd.merge(left, right, on = geo, how='outer'), DF_LIST)
        DF_MERGE.to_csv(OUTPUT_FILE.format(geo), index = False)
        DF_LIST = []
    
    #summary from parcel data
    baseyear = 2015
    endyear = 2050
    GEO = ['GG','tra','HRA', 'DIS']
    DF_LIST = []
    #PATH_LIST_PARCEL = filter(lambda x: (x != PBA40_DIR)&(x != DBP__CLEANER_DIR),PATH_LIST)
    for geo in GEO:
        for path in PATH_LIST_PARCEL:
            DF_JURIS = GEO_SUMMARY_LOADER(path, geo, baseyear, endyear)
            DF_LIST.append(DF_JURIS)
        
        DF_UNION = pd.concat(DF_LIST)
        DF_UNION['county'] = DF_UNION['juris'].map(juris_to_county)
        DF_UNION.sort_values(by = ['VERSION','county','juris','geo_category'],ascending=[False, True, True, False], inplace=True)
        DF_UNION.set_index(['VERSION','county','juris','geo_category'], inplace=True)
        DF_UNION.to_csv(OUTPUT_FILE.format(geo))
        DF_LIST = []
    
    #summaries for overlapping geos
    geo_1, geo_2, geo_3 = 'tra','DIS','HRA'
    DF_LIST =[]
    DF_LIST_2 = []
    for path in PATH_LIST_PARCEL:
        DF_TWO_GEO = TWO_GEO_SUMMARY_LOADER(path, geo_1, geo_2, baseyear, endyear)
        DF_TWO_GEO_2 = TWO_GEO_SUMMARY_LOADER(path, geo_1, geo_3, baseyear, endyear)
        DF_LIST.append(DF_TWO_GEO)
        DF_LIST_2.append(DF_TWO_GEO_2)
    
    DF_MERGE = pd.concat(DF_LIST)
    DF_MERGE['county'] = DF_MERGE['juris'].map(juris_to_county)
    DF_MERGE.sort_values(by = ['VERSION','county','juris','geo_category'],ascending=[False,True, True, False], inplace=True)
    DF_MERGE.set_index(['VERSION','county','juris','geo_category'], inplace=True)
    DF_MERGE.to_csv(OUTPUT_FILE.format(geo_1+geo_2))
    
    DF_MERGE_2 = pd.concat(DF_LIST_2)
    DF_MERGE_2['county'] = DF_MERGE_2['juris'].map(juris_to_county)
    DF_MERGE_2.sort_values(by = ['VERSION','county','juris','geo_category'],ascending=[False, True, True, False], inplace=True)
    DF_MERGE_2.set_index(['VERSION','county','juris','geo_category'], inplace=True)
    DF_MERGE_2.to_csv(OUTPUT_FILE.format(geo_1+geo_3))

