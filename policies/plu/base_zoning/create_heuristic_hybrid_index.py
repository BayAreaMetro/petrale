"""
Input: interim development capacity results from zoning attributes comparison hybrid index.
Output: urbansim version of hybrid index used to construct urbansim base zoning input
"""

import pandas as pd
import numpy as np
import time
import os, glob, logging

import dev_capacity_calculation_module

NOW = time.strftime("%Y_%m%d_%H%M")
today = time.strftime('%Y_%m_%d')


if os.getenv('USERNAME')    =='ywang':
    BOX_DIR                 = 'C:\\Users\\{}\\Box\\Modeling and Surveys\\Urban Modeling\\Bay Area UrbanSim 1.5\\PBA50\\Policies\\Base zoning'.format(os.getenv('USERNAME'))
    GITHUB_PETRALE_DIR      = 'C:\\Users\\{}\\Documents\\GitHub\\petrale\\'.format(os.getenv('USERNAME'))
    
# input file locations
HYBRID_ZONING_INTERIM_DIR   = os.path.join(BOX_DIR, 'outputs\\hybrid_base_zoning\\interim')
JURIS_ID_DIR                = os.path.join(GITHUB_PETRALE_DIR,'zones', 'jurisdictions')

# output file locations
INTRIM_CAPACITY_DIR         = os.path.join(BOX_DIR, 'outputs\\capacity\\interim')
HYBRID_INDEX_DIR            = os.path.join(GITHUB_PETRALE_DIR, 'policies\\plu\\base_zoning\\hybrid_index')
LOG_FILE                    = os.path.join(HYBRID_INDEX_DIR,'select_hybrid_idx_{}.log'.format(NOW))

ALLOWED_BUILDING_TYPE_CODES = ["HS","HT","HM","OF","HO","SC","IL","IW","IH","RS","RB","MR","MT","ME"]
RES_BUILDING_TYPE_CODES     = ["HS","HT","HM",                                        "MR"          ]
NONRES_BUILDING_TYPE_CODES  = [               "OF","HO","SC","IL","IW","IH","RS","RB","MR","MT","ME"]
INTENSITY_CODES             = ['MAX_DUA','MAX_FAR','MAX_HEIGHT']
JURIS_ADJUSTS_CODES         = ['proportion_adj_dua', 'proportion_adj_far','proportion_adj_height']



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

    logger.info("BOX_DIR         = {}".format(BOX_DIR))
    logger.info("DATA_OUTPUT_DIR = {}".format(HYBRID_INDEX_DIR))


    # Prepare a dataframe with jurisdiction as one field 

    juris_ls_file = os.path.join(JURIS_ID_DIR,'juris_county_id.csv')
    juris_ls = pd.read_csv(juris_ls_file,
                           usecols = ['juris_name_full', 'county_name'])
    juris_ls.rename(columns = {'juris_name_full': 'juris_zmod'}, inplace = True)
    logger.info('Get {} unique jurisdiction names'.format(len(juris_ls)))


    # Calculate capacity, compare capacity, and decide on indexes
    """
    4 Steps: 
        - Read interim zoning hybrid index for each zoning attribute
        - Calculate the parcel-level development capacities of PBA40 and Urbansim hybrid zoning under each interim hybrid version
        - Aggregate to jurisdiction-level development capacity
        - Use the following rules to compare PBA40 and Urbansim hybrid capacities to decide which data source to use for each
          jurisdiction and each zoning attribute
    """

    for hybrid_zoning_file in list(glob.glob(HYBRID_ZONING_INTERIM_DIR+'/*.csv')):

        # prep the three arguments for function "dev_capacity_calculation_module.zoning_to_capacity()"
        hybrid_zoning = hybrid_zoning_file
        hybrid_version = os.path.basename(hybrid_zoning_file).split('.')[0][4:].split('_')[6]
        capacity_output_dir = INTRIM_CAPACITY_DIR
        
        logger.info('Hybrid version: {}'.format(hybrid_version))
        logger.info('Hybrid zoning: {}'.format(hybrid_zoning))
        
        # calculate parcel-level development capacity
        capacity_by_parcel = dev_capacity_calculation_module.zoning_to_capacity(hybrid_zoning, hybrid_version+'_comp', capacity_output_dir)
        
        # aggregate to jurisdiction-level development capacity
        capacity_by_parcel.fillna(0, inplace = True)
        capacity_by_juris = capacity_by_parcel.groupby(['juris_zmod'])[['units_pba40','units_urbansim','sqft_pba40','sqft_urbansim']].sum().reset_index()
        
        # Use "intensity" interim hybrid capacity comparison to determine intensity attributes' indexes 
        if hybrid_version == 'intensity':
            logger.info('Get index for {}'.format(hybrid_version))
            
            # Jurisdictions whose hybrid-version total SQFT is within 20% discrepancy of PBA40 SQFT  
            sqft_good_idx = (abs(capacity_by_juris.sqft_urbansim - capacity_by_juris.sqft_pba40) / capacity_by_juris.sqft_pba40) <= 0.2
            
            # Jurisdictions whose hybrid-version total units is within 20% discrepancy of PBA40 units
            units_good_idx = (abs(capacity_by_juris.units_urbansim - capacity_by_juris.units_pba40) / capacity_by_juris.units_pba40) <= 0.2
            
            # Set the default intensity indexes as 0 (PBA40)
            for i in INTENSITY_CODES:
                logger.info('Add field {}'.format(i+'_idx'))
                capacity_by_juris[i+'_idx'] = 0
            
            # If SQFT discrepancy is small enough (<=20%), use BASIS MAX_FAR and MAX_HEIGHT
            capacity_by_juris.loc[sqft_good_idx,'MAX_FAR_idx'] = 1
            capacity_by_juris.loc[sqft_good_idx,'MAX_HEIGHT_idx'] = 1
            # If UNITS discrepancy is small enough (<=20%), use BASIS MAX_FAR and MAX_HEIGHT
            capacity_by_juris.loc[units_good_idx,'MAX_DUA_idx'] = 1
            
            # Take the relevant fields
            idx_comp = capacity_by_juris[['juris_zmod','MAX_DUA_idx', 'MAX_FAR_idx', 'MAX_HEIGHT_idx']]
            
            # A quick overview of the data source stats
            for i in INTENSITY_CODES:
                logger.info('Stats on hybrid for zoning attribute {}:\n{}'.format(i,idx_comp[i+'_idx'].value_counts()))
            
            # Join the indexes to jurisdiction list
            juris_ls = juris_ls.merge(idx_comp, on = 'juris_zmod', how = 'left')
     

        # Use "MR" interim hybrid capacity comparison to determine HM' index
        if hybrid_version == 'MR':
            logger.info('Get index for {}'.format(hybrid_version))
            
            # Since MR is residential-commercial mixed-use, both total SQFT and UNITS must be within 20% discrepancies
            units_sqft_good_idx = ((abs(capacity_by_juris.sqft_urbansim - capacity_by_juris.sqft_pba40) / capacity_by_juris.sqft_pba40) <= 0.2) & ((abs(capacity_by_juris.units_urbansim - capacity_by_juris.units_pba40) / capacity_by_juris.units_pba40) <= 0.2)
            
            # Set the default intensity indexes as 0 (PBA40)
            logger.info('Add field {}'.format(hybrid_version+'_idx'))
            capacity_by_juris[hybrid_version+'_idx'] = 0
            
            # If both total UNITS and SQFT discrepancies are small enough (<=20%), use BASIS MR
            capacity_by_juris.loc[units_sqft_good_idx,hybrid_version+'_idx'] = 1
            
            idx_comp = capacity_by_juris[['juris_zmod',hybrid_version+'_idx']]
            logger.info('Stats on hybrid for zoning attribute {}:\n{}'.format(hybrid_version,idx_comp[hybrid_version+'_idx'].value_counts()))
            juris_ls = juris_ls.merge(idx_comp, on = 'juris_zmod', how = 'left')
     

        # Indexes for residential-only development types 
        if hybrid_version in [devType for devType in RES_BUILDING_TYPE_CODES if devType not in ['MR']]:
            logger.info('Get index for {}'.format(hybrid_version))
            
            # For residential-only development types, only consider total UNITS discrepancy
            units_good_idx = (abs(capacity_by_juris.units_urbansim - capacity_by_juris.units_pba40) / capacity_by_juris.units_pba40) <= 0.2
            
            # Set the default intensity indexes as 0 (PBA40)     
            logger.info('Add field {}'.format(hybrid_version+'_idx'))
            capacity_by_juris[hybrid_version+'_idx'] = 0
            
            # If total UNITS discrepancy is small enough (<=20%), use BASIS development type value
            capacity_by_juris.loc[units_good_idx,hybrid_version+'_idx'] = 1
            idx_comp = capacity_by_juris[['juris_zmod',hybrid_version+'_idx']]
            logger.info('Stats on hybrid for zoning attribute {}:\n{}'.format(hybrid_version,idx_comp[hybrid_version+'_idx'].value_counts()))
            juris_ls = juris_ls.merge(idx_comp, on = 'juris_zmod', how = 'left')
     

        # Indexes for non-residential-only development types     
        if hybrid_version in [devType for devType in NONRES_BUILDING_TYPE_CODES if devType not in ['MR']]:
            logger.info('Get index for {}'.format(hybrid_version))
            
            # For non-residential-only development types, only consider total UNITS discrepancy
            sqft_good_idx = (abs(capacity_by_juris.sqft_urbansim - capacity_by_juris.sqft_pba40) / capacity_by_juris.sqft_pba40) <= 0.2
            
            # Set the default intensity indexes as 0 (PBA40)
            logger.info('Add field {}'.format(hybrid_version+'_idx'))
            capacity_by_juris[hybrid_version+'_idx'] = 0
            
            # If total SQFT discrepancy is small enough (<=20%), use BASIS development type value        
            capacity_by_juris.loc[sqft_good_idx,hybrid_version+'_idx'] = 1
            idx_comp = capacity_by_juris[['juris_zmod',hybrid_version+'_idx']]
            logger.info('Stats on hybrid for zoning attribute {}:\n{}'.format(hybrid_version,idx_comp[hybrid_version+'_idx'].value_counts()))
            juris_ls = juris_ls.merge(idx_comp, on = 'juris_zmod', how = 'left')   


    # Add jurisdiction-level proportional adjustments, default at 1
    for adjust in JURIS_ADJUSTS_CODES:
        juris_ls[adjust] = 1

    # Export urbansim heuristic index 
    logger.info('Export urbansim heuristic zoning hybrid index for {} jurisdictions. Head:\n{}Dtypes:\n{}'.format(len(juris_ls), juris_ls.head(), juris_ls.dtypes))
    juris_ls.to_csv(os.path.join(HYBRID_INDEX_DIR,'idx_urbansim_heuristic.csv'), index = False)
