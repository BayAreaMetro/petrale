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

## comment out one of the followng two lines based on the purpose of the build_hybrid run:
process = 'interim'   # run interim versions of hybrid indexes which are used to evaluate individual BASIS BOC zoning attributes
#process = 'urbansim'  # run urbansim input version of hybrid index

if os.getenv('USERNAME')    =='ywang':
    BOX_DIR                 = 'C:\\Users\\{}\\Box\\Modeling and Surveys\\Urban Modeling\\Bay Area UrbanSim 1.5\\PBA50'.format(os.getenv('USERNAME'))
    GITHUB_PETRALE_DIR      = 'C:\\Users\\{}\\Documents\\GitHub\\petrale\\'.format(os.getenv('USERNAME'))
    
# input file locations
HYBRID_INDEX_DIR            = os.path.join(GITHUB_PETRALE_DIR, 'policies\\plu\\base_zoning\\hybrid_index')
INTERIM_INDEX_DIR           = os.path.join(GITHUB_PETRALE_DIR, 'policies\\plu\\base_zoning\\hybrid_index\\interim')
PBA40_ZONING_BOX_DIR        = os.path.join(BOX_DIR, 'OLD Horizon Large General Input Data')
PBA50_ZONINGMOD_DIR         = os.path.join(BOX_DIR, 'Policies\\Zoning Modifications')
RAW_PLU_BOC_DIR             = os.path.join(BOX_DIR, 'Policies\\Base zoning\\outputs')
OTHER_INPUTS_DIR            = os.path.join(BOX_DIR, 'Policies\\Base zoning\\inputs')

# output file location
HYBRID_ZONING_OUTPUT_DIR    = os.path.join(BOX_DIR, 'Policies\\Base zoning\\outputs\\hybrid_base_zoning')
INTERIM_HYBRIND_ZONING_DIR  = os.path.join(BOX_DIR, 'Policies\\Base zoning\\outputs\\hybrid_base_zoning\\interim')
ZONING_FOR_URBANSIM_DIR     = os.path.join(BOX_DIR, 'Policies\\Base zoning\\outputs\\for_urbansim')
QA_QC_DIR                   = os.path.join(BOX_DIR, 'Policies\\Base zoning\\outputs\\QAQC')
LOG_FILE                    = os.path.join(HYBRID_ZONING_OUTPUT_DIR,'build_hybrid_zoning_{}.log'.format(NOW))


ALLOWED_BUILDING_TYPE_CODES = ["HS","HT","HM","OF","HO","SC","IL","IW","IH","RS","RB","MR","MT","ME"]
RES_BUILDING_TYPE_CODES     = ["HS","HT","HM",                                        "MR"          ]
NONRES_BUILDING_TYPE_CODES  = [               "OF","HO","SC","IL","IW","IH","RS","RB","MR","MT","ME"]



def countMissing(df, attr):
    null_attr_count = len(df.loc[df["{}_basis".format(attr)].isnull()])
    logger.info('Number of parcels missing {} info: {:,} or {:.1f}%'.format(attr,
                null_attr_count, 100.0*null_attr_count/len(df)))


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
    
    # create fileds for hybrid zoning attributes as urbansim input
    for zoning in ALLOWED_BUILDING_TYPE_CODES + ['max_dua','max_far','max_height']:
        df[zoning+'_urbansim'] = df[zoning+'_basis']
    # create fields for intensity index and set the default as 1 (use BASIS data)
    for intensity in ['max_dua','max_far','max_height']:
        df[intensity+'_idx'] = 1

    for juris in juris_list:
        
        logger.info('Apply hybrid index for: {}'.format(juris))

        for devType in ALLOWED_BUILDING_TYPE_CODES:
            if hybrid_idx[devType+'_idx'][juris] == 0:
                logger.info('Use PBA40 data for {}'.format(devType))
                #print('Before applying the index, parcel counts by data source for {}:'.format(devType))
                #display(df.loc[df.juris_zmod == juris][devType+'_idx'].value_counts())
                
                replace_idx = (df.juris_zmod == juris) & (df[devType+'_idx'] != '0_fill_na')
                df.loc[replace_idx, devType+'_urbansim'] = df.loc[replace_idx, devType+'_pba40']
                df.loc[replace_idx, devType+'_idx'] = 0
                #print('After applying the index, parcel counts by data source for {}:'.format(devType))
                #display(df.loc[df.juris_zmod == juris][devType+'_idx'].value_counts())   
                
            elif hybrid_idx[devType+'_idx'][juris] == 1:
                logger.info('Use BASIS data for {}'.format(devType))
        

        for intensity in ['max_dua','max_far','max_height']:
            if hybrid_idx[intensity+'_idx'][juris] == 0:
                logger.info('Use PBA40 data for {}'.format(intensity))
                #print('Before applying the index, parcel counts by data source for {}:'.format(intensity))
                #display(df.loc[df.juris_zmod == juris][intensity+'_idx'].value_counts())
                
                replace_idx = df.juris_zmod == juris
                df.loc[replace_idx, intensity+'_urbansim'] = df.loc[replace_idx, intensity+'_pba40']
                df.loc[replace_idx, intensity+'_idx'] = 0
                #print('After applying the index, parcel counts by data source for {}:'.format(intensity))
                #display(df.loc[df.juris_zmod == juris][intensity+'_idx'].value_counts())
                
            elif hybrid_idx[intensity+'_idx'][juris] == 1:
                logger.info('Use BASIS data for {}'.format(intensity))

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
    logger.info("DATA_OUTPUT_DIR = {}".format(HYBRID_ZONING_OUTPUT_DIR))


    ## P10 parcels with pba40 plu and basis boc data
    #plu_boc_file = os.path.join(RAW_PLU_BOC_DIR, today+'_p10_plu_boc_allAttrs.csv')
    plu_boc_file = os.path.join(RAW_PLU_BOC_DIR, '2020_05_18_p10_plu_boc_allAttrs.csv')
    
    plu_boc = pd.read_csv(plu_boc_file)
    logger.info("Read {:,} rows from {}".format(len(plu_boc), plu_boc_file))
    logger.info(plu_boc.head())



    logger.info('Count number of parcels missing allowable development types in the BASIS data:')
    for devType in ALLOWED_BUILDING_TYPE_CODES:
        countMissing(plu_boc, devType)

    
    ## Step 1: fill in missing allowable dev types in BASIS using PBA40 data

    plu_boc_filled_devTypeNa = plu_boc.copy()

    for btype in ALLOWED_BUILDING_TYPE_CODES:
        plu_boc_filled_devTypeNa[btype+'_idx'] = 1
        missing_type_idx = (plu_boc_filled_devTypeNa[btype+'_basis'].isnull()) & (plu_boc_filled_devTypeNa['nodev_zmod'] == 0)
        plu_boc_filled_devTypeNa.loc[missing_type_idx, btype+'_basis'] = plu_boc_filled_devTypeNa.loc[missing_type_idx, btype+'_pba40']
        plu_boc_filled_devTypeNa.loc[missing_type_idx, btype+'_idx'] = '0_fill_na'

    logger.info('\n After filling nan in BASIS allowable development types using PBA40 data:')
    for devType in ALLOWED_BUILDING_TYPE_CODES:
        countMissing(plu_boc_filled_devTypeNa, devType)


    ## Step 2: fill in missing max_height in BASIS using PBA40 data

    logger.info('Count number of parcels missing max_height in the BASIS data:')
    countMissing(plu_boc_filled_devTypeNa, 'max_height')

    plu_boc_filled_TpHt_Na = plu_boc_filled_devTypeNa.copy()
    plu_boc_filled_TpHt_Na['max_height_idx'] = 1
    missing_height_idx = (plu_boc_filled_TpHt_Na['max_height_basis'].isnull()) & (plu_boc_filled_TpHt_Na['nodev_zmod'] == 0)
    plu_boc_filled_TpHt_Na.loc[missing_height_idx, 'max_height_basis'] = plu_boc_filled_TpHt_Na.loc[missing_height_idx, 'max_height_pba40']
    plu_boc_filled_TpHt_Na.loc[missing_height_idx, 'max_height_idx'] = '0_fill_na'

    logger.info('\n After filling nan in BASIS max_height using PBA40 data:')
    countMissing(plu_boc_filled_TpHt_Na, 'max_height')


    ## Step 3: apply the hybrid index of each hybrid version

    # interim indexes used to evaluate zoning attributes separately
    if process == 'interim':
        HYBRID_INDEX_DIR = INTERIM_INDEX_DIR

    for hybrid_idx_file in list(glob.glob(HYBRID_INDEX_DIR+'/*.csv')):
        hybrid_name = os.path.basename(hybrid_idx_file).split('.')[0][4:]
        logger.info('Hybrid version: {}'.format(hybrid_name))
        hybrid_idx = pd.read_csv(hybrid_idx_file)
        hybrid_idx.rename(columns = {'MAX_FAR_idx'   : 'max_far_idx', 
                                     'MAX_DUA_idx'   : 'max_dua_idx',
                                     'MAX_HEIGHT_idx': 'max_height_idx'}, inplace = True)

        hybrid_idx.set_index('juris_name',inplace = True)
        juris_list = list(hybrid_idx.index.values)

        # make a copy so we don't modify the zoning data before hybrid
        plu_boc_before_hybrid = plu_boc_filled_TpHt_Na.copy()
        
        for devType in ALLOWED_BUILDING_TYPE_CODES:
            logger.info('Before applying index, parcel counts by data source for develpment type {}:'.format(devType))
            logger.info(plu_boc_before_hybrid[devType+'_idx'].value_counts())
              
        plu_boc_hybrid = apply_hybrid_idx(plu_boc_before_hybrid,hybrid_idx)
        
        for devType in ALLOWED_BUILDING_TYPE_CODES:
            logger.info('After applying index, parcel counts by data source for develpment type {}:'.format(devType))
            logger.info(plu_boc_hybrid[devType+'_idx'].value_counts())
            
        for intensity in ['max_far','max_far','max_height']:
            logger.info('Parcel counts by data source for density type {}:'.format(intensity))
            logger.info(plu_boc_hybrid[intensity+'_idx'].value_counts())
            
        # recalculate 'allow_res' and 'allow_nonres' based on the allowable development type
        allowed_basis = set_allow_dev_type(plu_boc_hybrid,'basis')
        allowed_pba40 = set_allow_dev_type(plu_boc_hybrid,'pba40')
        allowed_urbansim = set_allow_dev_type(plu_boc_hybrid,'urbansim')
        
        # drop the previous 'allow_res' and 'allow_nonres' and insert the new ones
        plu_boc_hybrid.drop(columns = ['allow_res_basis', 'allow_nonres_basis', 
                                       'allow_res_pba40', 'allow_nonres_pba40'], inplace = True)
        plu_boc_hybrid = plu_boc_hybrid.merge(allowed_basis, 
                                              on = 'PARCEL_ID', 
                                              how = 'left').merge(allowed_pba40, 
                                                                  on = 'PARCEL_ID', 
                                                                  how = 'left').merge(allowed_urbansim,
                                                                                      on = 'PARCEL_ID', 
                                                                                      how = 'left' ) 

        logger.info('Export hybrid zoning of {} record:'.format(len(plu_boc_hybrid)))
        logger.info(plu_boc_hybrid.dtypes)

        # export hybrind zoning file to "interim" or "final" folder based on if they are for evaluation or for UrbanSim use
        if process == 'interim':
            HYBRID_ZONING_OUTPUT_DIR = INTERIM_HYBRIND_ZONING_DIR
        
        plu_boc_hybrid.to_csv(os.path.join(HYBRID_ZONING_OUTPUT_DIR, today+'_p10_plu_boc_'+hybrid_name+'.csv'),index = False)


        # For urbansim version of the hybrid, create BAUS base zoning input files and export
        if hybrid_name == 'urbansim':
            logger.info('Create BAUS base zoning input files:')

            # select hybrid fields
            plu_boc_urbansim_cols = ['PARCEL_ID','geom_id','county_id','county_name', 'juris_zmod', 'jurisdiction_id', 'ACRES',
                                     'pba50zoningmodcat_zmod','nodev_zmod','name_pba40','plu_code_basis'] + [
                                     devType + '_urbansim' for devType in ALLOWED_BUILDING_TYPE_CODES] + [
                                     intensity + '_urbansim' for intensity in ['max_dua','max_far','max_height']]

            plu_boc_urbansim = plu_boc_hybrid[plu_boc_urbansim_cols]

            # rename the fields to remove '_urbansim'
            plu_boc_urbansim.columns = ['PARCEL_ID','geom_id','county_id','county_name', 'juris_zmod', 'jurisdiction_id', 'ACRES',
                                        'pba50zoningmodcat_zmod','nodev_zmod','name_pba40','plu_code_basis'] + ALLOWED_BUILDING_TYPE_CODES + [
                                        'max_dua','max_far','max_height']

            # convert allowed types to integer
            for attr in ALLOWED_BUILDING_TYPE_CODES:
                plu_boc_urbansim[attr] = plu_boc_urbansim[attr].fillna(-1).astype(int)
            plu_boc_urbansim.replace({-1: None}, inplace = True)

            # create zoning_lookup table with unique jurisdiction and zoning attributes
            zoning_lookup_pba50 = plu_boc_urbansim[['county_name','juris_zmod'] + ALLOWED_BUILDING_TYPE_CODES + ['max_dua','max_far','max_height']].drop_duplicates()     

            # sort zoning type by county and jurisdiction and assign zoning_id
            zoning_lookup_pba50.sort_values(by=['county_name', 'juris_zmod'], inplace = True)
            zoning_lookup_pba50['zoning_id_pba50'] = range(1,len(zoning_lookup_pba50) + 1)
            logger.info('Zoning lookup table has {} unique types (juris + zoning attributes), header:'.format(len(zoning_lookup_pba50)))
            logger.info(zoning_lookup_pba50.head())
            
            # create zoning_parcels file and attach zoning_id 
            plu_boc_urbansim_ID = plu_boc_urbansim.merge(zoning_lookup_pba50,
                                                         on = list(zoning_lookup_pba50)[:-1],
                                                         how = 'left')
            zoning_parcels_pba50 = plu_boc_urbansim_ID[['PARCEL_ID','geom_id','juris_zmod','jurisdiction_id','zoning_id_pba50','nodev_zmod']]

            # bring into other attributes from Horizon:
            zoning_parcels_pba40_file = os.path.join(PBA40_ZONING_BOX_DIR, '2015_12_21_zoning_parcels.csv')
            zoning_parcels_pba40 = pd.read_csv(zoning_parcels_pba40_file, 
            								  usecols = ['geom_id','prop'])
            zoning_parcels_pba50 = zoning_parcels_pba50.merge(zoning_parcels_pba40, on = 'geom_id', how = 'left')          


            ## assign zoning name to each zoning_id based on the most frequent occurance of zoning name among all the parcels with the same zoning_id
            zoning_names = plu_boc_urbansim[['PARCEL_ID','name_pba40','plu_code_basis']]

            # merge zoning names of pba40 and BASIS into zoning_parcels
            zoning_names['name_pba40'] = zoning_names['name_pba40'].apply(lambda x: str(x)+'_pba40')
            zoning_names['plu_code_basis'] = zoning_names['plu_code_basis'].apply(lambda x: str(x)+'_basis')
            parcel_zoning_names = zoning_parcels_pba50[['PARCEL_ID','zoning_id_pba50']].merge(zoning_names,
                                                                                              on = 'PARCEL_ID',
                                                                                              how = 'left')
            # use name_pba40 as the default for pab50 zoning name, unless it is null, then use basis zoning name
            parcel_zoning_names['zoning_name_pba50'] = zoning_names['name_pba40']
            name_null_index = parcel_zoning_names.name_pba40.isnull()
            parcel_zoning_names.loc[name_null_index,'zoning_name_pba50'] = parcel_zoning_names.loc[name_null_index,'plu_code_basis']

            # find the most frenquent zoning name of each zoning_id
            name_by_zone = parcel_zoning_names[['zoning_id_pba50','zoning_name_pba50']].groupby(['zoning_id_pba50']).agg(lambda x:x.value_counts().index[0]).reset_index()
            zoning_lookup_pba50 = zoning_lookup_pba50.merge(name_by_zone,
                                                            on = 'zoning_id_pba50',
                                                            how = 'left')
            # attach zoning name to the zoning lookup table
            zoning_lookup_pba50 = zoning_lookup_pba50[['zoning_id_pba50','juris_zmod','zoning_name_pba50','max_dua','max_far','max_height'] + ALLOWED_BUILDING_TYPE_CODES]
            # change field names to be consistent with the previous version
            zoning_lookup_pba50.rename(columns = {'zoning_id_pba50'  :'id',
            									  'juris_zmod'       :'juris',
            									  'zoning_name_pba50':'name'}, inplace = True)
            logger.info('zoning_lookup has {} unique zoning_ids; zoning_lookup table header:'.format(len(zoning_lookup_pba50)))
            logger.info(zoning_lookup_pba50.head())
            
            # export
            logger.info('Export zoning_lookup table with the following attributes: {}'.format(zoning_lookup_pba50.dtypes))
            zoning_parcels_pba50.to_csv(os.path.join(ZONING_FOR_URBANSIM_DIR, today+'_zoning_parcels_pba50.csv'),index = False)            

            # lastly, append zone name to zoning_parcel
            zoning_parcels_pba50 = zoning_parcels_pba50.merge(zoning_lookup_pba50[['id','name']], 
                                                              left_on = 'zoning_id_pba50', 
                                                              right_on = 'id',
                                                              how = 'left')
            # rename fields to be consistent with the model
            zoning_parcels_pba50.rename(columns = {'juris_zmod'     : 'juris_id',
                                                   'zoning_id_pba50': 'zoning_id',
                                                   'jurisdiction_id': 'juris',
                                                   'nodev_zmod'     : 'nodev',
                                                   'name'           : 'zoning'}, inplace = True)
            logger.info('zoning_parcels_pba50 has {} records; table header:'.format(len(zoning_parcels_pba50)))
            logger.info(zoning_parcels_pba50.head())

            # export 
            logger.info('Export zoning_parcels table with the following attributes: {}'.format(zoning_parcels_pba50.dtypes))
            zoning_lookup_pba50.to_csv(os.path.join(ZONING_FOR_URBANSIM_DIR, today+'_zoning_lookup_pba50.csv'),index = False)
