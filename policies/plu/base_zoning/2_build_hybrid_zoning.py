import pandas as pd
import numpy as np
import os, glob, logging
import time

NOW = time.strftime("%Y_%m%d_%H%M")
today = time.strftime('%Y_%m_%d')

"""
Input: p10 combined pba40 plu and basis boc data, with 
Output: p10 combined pba40 plu and basis boc data, with: 
    1) NaN in basis allowed development types filled in using pba40 data
    2) basis allowed development types replaced by pba40 data following the 'hybrid index'
"""

if os.getenv('USERNAME')    =='ywang':
    BOX_DIR                 = 'C:\\Users\\{}\\Box\\Modeling and Surveys\\Urban Modeling\\Bay Area UrbanSim 1.5\\PBA50'.format(os.getenv('USERNAME'))
    GITHUB_PETRALE_DIR      = 'C:\\Users\\{}\\Documents\\GitHub\\petrale\\'.format(os.getenv('USERNAME'))
    
# input file locations
HYBRID_INDEX_DIR            = os.path.join(GITHUB_PETRALE_DIR, 'policies\\plu\\base_zoning\\hybrid_index')
PBA40_ZONING_BOX_DIR        = os.path.join(BOX_DIR, 'OLD PBA50 Large General Input Data')
PBA50_ZONINGMOD_DIR         = os.path.join(BOX_DIR, 'Policies\\Zoning Modifications')
RAW_PLU_BOC_DIR             = os.path.join(BOX_DIR, 'Policies\\Base zoning\\outputs')
OTHER_INPUTS_DIR            = os.path.join(BOX_DIR, 'Policies\\Base zoning\\inputs')

# output file location
DATA_OUTPUT_DIR             = os.path.join(BOX_DIR, 'Policies\\Base zoning\\outputs\\hybrid_base_zoning')
QA_QC_DIR                   = os.path.join(BOX_DIR, 'Policies\\Base zoning\\outputs\\QAQC')
LOG_FILE                    = os.path.join(DATA_OUTPUT_DIR,'build_hybrid_zoning_{}.log'.format(NOW))


ALLOWED_BUILDING_TYPE_CODES = ["HS","HT","HM","OF","HO","SC","IL","IW","IH","RS","RB","MR","MT","ME"]
RES_BUILDING_TYPE_CODES     = ["HS","HT","HM",                                        "MR"          ]
NONRES_BUILDING_TYPE_CODES  = [               "OF","HO","SC","IL","IW","IH","RS","RB","MR","MT","ME"]



def countMissing(df):
    for btype in ALLOWED_BUILDING_TYPE_CODES:
        null_btype_count = len(df.loc[df["{}_basis".format(btype)].isnull()])
        print('Number of parcels missing allowable type for {}: {:,} or {:.1f}%'.format(btype,
           null_btype_count, 100.0*null_btype_count/len(df)))


def set_allow_dev_type(df_original,boc_source):
    """
    Assign allow residential and/or non-residential by summing the columns for the residential/nonresidential allowed building type codes
    Returns dataframe with PARCEL_ID, allow_res_[boc_source], allow_nonres_[boc_source]

    """

    # don't modify passed df
    df = df_original.copy()

    # note that they can't be null because then they won't sum -- so make a copy and fillna with 0
    for dev_type in ALLOWED_BUILDING_TYPE_CODES:
        df[dev_type+"_"+boc_source] = df[dev_type+"_"+boc_source].fillna(value=0.0)    
    
    # allow_res is sum of allowed building types that are residential
    res_allowed_columns = [btype+'_'+boc_source for btype in RES_BUILDING_TYPE_CODES]
    df['allow_res_' +boc_source] = df[res_allowed_columns].sum(axis=1)
    
    # allow_nonres is the sum of allowed building types that are non-residential
    nonres_allowed_columns = [btype+'_'+boc_source for btype in NONRES_BUILDING_TYPE_CODES]
    df['allow_nonres_'+boc_source] = df[nonres_allowed_columns].sum(axis=1)
    
    return df[['PARCEL_ID',
               "allow_res_"    +boc_source,
               "allow_nonres_" +boc_source]]



def apply_hybrid_idx(df_origional,hybrid_idx):
    """
    Apply hybrid index to raw plu_boc data. 
    Returns plu_boc with updated allowable dev type and intensity parameters for BASIS fields, 
    along with '_idx' for each parameter to indicate the data source - '1' for BASIS '0' for PBA40
    """

    # don't modify passed df
    df = df_origional.copy()
    
    for juris in juris_list:
        
        print('')
        print('Apply hybrid index for: {}'.format(juris))

        for devType in ALLOWED_BUILDING_TYPE_CODES:
            df[btype+'_idx'] = 1
            if hybrid_idx[devType+'_idx'][juris] == 0:
                print('Use PBA40 data for {}'.format(devType))
                #print('Before applying the index, parcel counts by data source for {}:'.format(devType))
                #display(df.loc[df.juris_zmod == juris][devType+'_idx'].value_counts())
                
                replace_idx = (df.juris_zmod == juris) & (df[devType+'_idx'] != 'PBA40_fill_na')
                df.loc[replace_idx, devType+'_basis'] = df.loc[replace_idx, devType+'_pba40']
                df.loc[replace_idx, devType+'_idx'] = 0
                #print('After applying the index, parcel counts by data source for {}:'.format(devType))
                #display(df.loc[df.juris_zmod == juris][devType+'_idx'].value_counts())   
                
            elif hybrid_idx[devType+'_idx'][juris] == 1:
                print('Use BASIS data for {}'.format(devType))
        

        for intensity in ['max_dua','max_far','max_height']:
            df[intensity+'_idx'] = 1
            if hybrid_idx[intensity+'_idx'][juris] == 0:
                print('Use PBA40 data for {}'.format(intensity))
                #print('Before applying the index, parcel counts by data source for {}:'.format(intensity))
                #display(df.loc[df.juris_zmod == juris][intensity+'_idx'].value_counts())
                
                replace_idx = df.juris_zmod == juris
                df.loc[replace_idx, intensity+'_basis'] = df.loc[replace_idx, intensity+'_pba40']
                df.loc[replace_idx, intensity+'_idx'] = 0
                #print('After applying the index, parcel counts by data source for {}:'.format(intensity))
                #display(df.loc[df.juris_zmod == juris][intensity+'_idx'].value_counts())
                
            elif hybrid_idx[intensity+'_idx'][juris] == 1:
                print('Use BASIS data for {}'.format(intensity))

    return df


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
    logger.info("DATA_OUTPUT_DIR = {}".format(DATA_OUTPUT_DIR))


    ## P10 parcels with pba40 plu and basis boc data
    plu_boc_file = os.path.join(RAW_PLU_BOC_DIR, today+'_p10_plu_boc_allAttrs.csv')
    plu_boc = pd.read_csv(plu_boc_file)
    logger.info("Read {:,} rows from {}".format(len(plu_boc), plu_boc_file))
    logger.info(plu_boc.head())



    logger.info('Count number of parcels missing allowable development types in the BASIS data:')
    countMissing(plu_boc)

    
    ## Hybrid version 0: fill in missing allowable dev types in BASIS using PBA40 data

    plu_boc_filled_devTypeNa = plu_boc.copy()

    for btype in ALLOWED_BUILDING_TYPE_CODES:
        plu_boc_filled_devTypeNa[btype+'_idx'] = 1
        missing_idx = (plu_boc_filled_devTypeNa[btype+'_basis'].isnull()) & (plu_boc_filled_devTypeNa['nodev_zmod'] == 0)
        plu_boc_filled_devTypeNa.loc[missing_idx, btype+'_basis'] = plu_boc_filled_devTypeNa.loc[missing_idx, btype+'_pba40']
        plu_boc_filled_devTypeNa.loc[missing_idx, btype+'_idx'] = 'PBA40_fill_na'

    logger.info('\n After filling nan in BASIS allowable development types using PBA40 data:')
    countMissing(plu_boc_filled_devTypeNa)

    # export the hybrid version
    plu_boc_filled_devTypeNa.to_csv(os.path.join(DATA_OUTPUT_DIR, today+'_p10_plu_boc_fill_naType.csv'),index = False)

    logger.info('Print unique data source index for allowable development types (should only be "PBA40_fill_na" or "1"):')
    for i in ALLOWED_BUILDING_TYPE_CODES:
        logger.info('{}: {}'.format(i,plu_boc_filled_devTypeNa[i+'_idx'].unique()))


    
    ## Apply the hybrid index of each hybrid version

    for hybrid_idx_file in list(glob.glob(HYBRID_INDEX_DIR+'/*.csv')):
        hybrid_name = os.path.basename(hybrid_idx_file).split('.')[0][4:]
        logger.info('Hybrid version: {}'.format(hybrid_name))
        hybrid_idx = pd.read_csv(hybrid_idx_file)
        hybrid_idx.rename(columns = {'MAX_FAR_idx'   : 'max_far_idx', 
                                     'MAX_DUA_idx'   : 'max_dua_idx',
                                     'MAX_HEIGHT_idx': 'max_height_idx'}, inplace = True)

        hybrid_idx.set_index('juris_name',inplace = True)
        juris_list = list(hybrid_idx.index.values)
        
        for devType in ALLOWED_BUILDING_TYPE_CODES:
            logger.info('Before applying index, parcel counts by data source for develpment type {}:'.format(devType))
            logger.info(plu_boc_filled_devTypeNa[devType+'_idx'].value_counts())
              
        plu_boc_hybrid = apply_hybrid_idx(plu_boc_filled_devTypeNa,hybrid_idx)
        
        for devType in ALLOWED_BUILDING_TYPE_CODES:
            logger.info('After applying index, parcel counts by data source for develpment type {}:'.format(devType))
            logger.info(plu_boc_hybrid[devType+'_idx'].value_counts())
            
        for intensity in ['max_far','max_far','max_height']:
            logger.info('Parcel counts by data source for density type {}:'.format(intensity))
            logger.info(plu_boc_hybrid[intensity+'_idx'].value_counts())
            
        # recalculate 'allow_res' and 'allow_nonres' based on the allowable development type
        allowed_basis = set_allow_dev_type(plu_boc_hybrid,'basis')
        allowed_pba40 = set_allow_dev_type(plu_boc_hybrid,'pba40')
        
        # drop the previous 'allow_res' and 'allow_nonres' and insert the new ones
        plu_boc_hybrid.drop(columns = ['allow_res_basis', 'allow_nonres_basis', 
                                       'allow_res_pba40', 'allow_nonres_pba40'], inplace = True)
        plu_boc_hybrid = plu_boc_hybrid.merge(allowed_basis, 
                                              on = 'PARCEL_ID', 
                                              how = 'left').merge(allowed_pba40, 
                                                                  on = 'PARCEL_ID', 
                                                                  how = 'left')
      
        plu_boc_hybrid.to_csv(os.path.join(DATA_OUTPUT_DIR, today+'_p10_plu_boc_'+hybrid_name+'.csv'),index = False)