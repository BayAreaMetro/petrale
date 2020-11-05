USAGE="""

  Given a hybrid configuration index, generates UrbanSim inpput files.

  Input:  p10_plu_boc_allAttrs.csv, p10 combined with pba40 and basis boc data output by 1_PLU_BOC_data_combine.py
          hybrid configuration index indicating which variable/jurisdiction will use BASIS data verus PBA40 data

  Output: 

"""

import pandas as pd
import numpy as np
import argparse, os, logging, sys, time
import dev_capacity_calculation_module

today = time.strftime('%Y_%m_%d')

if os.getenv('USERNAME')    =='ywang':
    BOX_DIR                 = 'C:\\Users\\{}\\Box\\Modeling and Surveys\\Urban Modeling\\Bay Area UrbanSim\\PBA50'.format(os.getenv('USERNAME'))
    M_DIR                   = 'M:\\Data\\Urban\\BAUS\\PBA50'
    GITHUB_PETRALE_DIR      = 'C:\\Users\\{}\\Documents\\GitHub\\petrale\\'.format(os.getenv('USERNAME'))
elif os.getenv('USERNAME')  =='lzorn':
    BOX_DIR                 = 'C:\\Users\\{}\\Box\\Modeling and Surveys\\Urban Modeling\\Bay Area UrbanSim\\PBA50'.format(os.getenv('USERNAME'))
    M_DIR                   = 'M:\\Data\\Urban\\BAUS\\PBA50'
    GITHUB_PETRALE_DIR      = 'X:\\petrale'


# input file locations
PREV_ZONING_PARCELS_FILE    = os.path.join(M_DIR, 'Horizon', 'Large General Input Data', '2015_12_21_zoning_parcels.csv')
PLU_BOC_M_DIR               = os.path.join(M_DIR, 'Final_Blueprint', 'Base zoning', 'output')
PLU_BOC_FILE                = os.path.join(PLU_BOC_M_DIR, '2020_10_20_p10_plu_boc_allAttrs.csv')
HYBRID_INDEX_DIR            = os.path.join(GITHUB_PETRALE_DIR, 'policies\\plu\\hybrid_index')
# TODO: change to idx_urbansim.csv when we have one
HYBRID_INDEX_FILE           = os.path.join(HYBRID_INDEX_DIR, "idx_urbansim.csv")

# output file locations
HYBRID_ZONING_OUTPUT_DIR    = os.path.join(BOX_DIR, 'Policies\\Base zoning\\outputs\\hybrid_base_zoning')
# In test mode (specified by --test), outputs to cwd and without date prefix; otherwise, outputs to HYBRID_ZONING_OUTPUT_DIR with date prefix
HYBRID_PARCELS_FILE         = 'p10_plu_boc_hybrid.csv'
LOG_FILE                    = "create_hybrid_urbansim_input.log"
# UrbanSim Inputs
ZONING_PARCELS_FILE         = 'zoning_parcels_hybrid_pba50.csv'
ZONING_LOOKUP_FILE          = 'zoning_lookup_hybrid_pba50.csv'


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=USAGE, formatter_class=argparse.RawDescriptionHelpFormatter,)
    parser.add_argument("--test", action="store_true", help="Test mode")
    args = parser.parse_args()

    if args.test == False:
        LOG_FILE            = os.path.join(HYBRID_ZONING_OUTPUT_DIR, "{}_{}".format(today, LOG_FILE))
        HYBRID_PARCELS_FILE = os.path.join(HYBRID_ZONING_OUTPUT_DIR, "{}_{}".format(today, HYBRID_PARCELS_FILE))
        ZONING_PARCELS_FILE = os.path.join(HYBRID_ZONING_OUTPUT_DIR, "{}_{}".format(today, ZONING_PARCELS_FILE))
        ZONING_LOOKUP_FILE  = os.path.join(HYBRID_ZONING_OUTPUT_DIR, "{}_{}".format(today, ZONING_LOOKUP_FILE))

    pd.set_option('max_columns',   200)
    pd.set_option('display.width', 200)

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

    plu_boc = pd.read_csv(PLU_BOC_FILE)
    logger.info("Read {} lines from {}".format(len(plu_boc), PLU_BOC_FILE))
    logger.debug("head:\n{}".format(plu_boc.head()))

    hybrid_idx = pd.read_csv(HYBRID_INDEX_FILE)
    logger.info("Read {} lines from {}".format(len(hybrid_idx), HYBRID_INDEX_FILE))
    logger.debug("head:\n{}".format(hybrid_idx.head()))

    # create the parcel data set with hybrid index attached
    plu_boc_hybrid = dev_capacity_calculation_module.create_hybrid_parcel_data_from_juris_idx(logger, plu_boc, hybrid_idx)
    plu_boc_hybrid = pd.merge(left=plu_boc, right=plu_boc_hybrid, how="left", on=['PARCEL_ID', 'juris_zmod'])
            
    # calculate 'allow_res' and 'allow_nonres' based on the allowable development type
    allowed_urbansim = dev_capacity_calculation_module.set_allow_dev_type(plu_boc_hybrid,'urbansim')
        
    plu_boc_hybrid = pd.merge(left = plu_boc_hybrid,
                              right= allowed_urbansim, 
                              on   = 'PARCEL_ID', 
                              how  = 'left')

    logger.info('Saving hybrid zoning for {} parcels to {}'.format(len(plu_boc_hybrid),HYBRID_PARCELS_FILE))
    logger.debug('plu_boc_hybrid dtypes:\n{}'.format(plu_boc_hybrid.dtypes))
    plu_boc_hybrid.to_csv(HYBRID_PARCELS_FILE,index = False)

    logger.info('Create BAUS base zoning input files:')

    # select hybrid fields
    plu_boc_urbansim_cols = ['PARCEL_ID','geom_id','county_id','county_name', 'juris_zmod', 'jurisdiction_id', 'ACRES',
                             'fbpzoningm_zmod','nodev_zmod','name_pba40','plu_code_basis'] + \
                            ['{}_urbansim'.format(devType)       for devType   in dev_capacity_calculation_module.ALLOWED_BUILDING_TYPE_CODES] + \
                            ['max_{}_urbansim'.format(intensity) for intensity in dev_capacity_calculation_module.INTENSITY_CODES]

    plu_boc_urbansim = plu_boc_hybrid[plu_boc_urbansim_cols].copy()

    # rename the fields to remove '_urbansim'
    rename_cols = {}
    for col in plu_boc_urbansim_cols:
        if col.endswith('_urbansim'):
            rename_cols[col] = col[:-9]
    plu_boc_urbansim.rename(columns=rename_cols, inplace=True)

    # convert allowed types to integer
    for attr in dev_capacity_calculation_module.ALLOWED_BUILDING_TYPE_CODES:
        plu_boc_urbansim[attr] = plu_boc_urbansim[attr].fillna(-1).astype(int)
    plu_boc_urbansim.replace({-1: None}, inplace = True)

    # create zoning_lookup table with unique jurisdiction and zoning attributes
    zoning_lookup_pba50 = plu_boc_urbansim[['county_name','juris_zmod'] + \
      dev_capacity_calculation_module.ALLOWED_BUILDING_TYPE_CODES + \
      ['max_dua','max_far','max_height']].drop_duplicates()     

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

    # bring into other attributes from previous parcel zoning file
    zoning_parcels_prev  = pd.read_csv(PREV_ZONING_PARCELS_FILE, usecols = ['geom_id','prop'])
    zoning_parcels_pba50 = zoning_parcels_pba50.merge(zoning_parcels_prev, on = 'geom_id', how = 'left')          


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
    zoning_lookup_pba50 = zoning_lookup_pba50[['zoning_id_pba50','juris_zmod','zoning_name_pba50','max_dua','max_far','max_height'] + \
                                               dev_capacity_calculation_module.ALLOWED_BUILDING_TYPE_CODES]

    # change field names to be consistent with the previous version
    zoning_lookup_pba50.rename(columns = {'zoning_id_pba50'  :'id',
                                          'juris_zmod'       :'juris',
                                          'zoning_name_pba50':'name'}, inplace = True)
    logger.info('zoning_lookup has {} unique zoning_ids; zoning_lookup table header:'.format(len(zoning_lookup_pba50)))
    logger.info(zoning_lookup_pba50.head())         

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
    # remove lines with null geom_id
    logger.info('zoning_parcels_pba50 is length {} but has {} rows with null geom_id; removing'.format(
                len(zoning_parcels_pba50),
                len(zoning_parcels_pba50.loc[pd.isnull(zoning_parcels_pba50['geom_id'])])))
    zoning_parcels_pba50 = zoning_parcels_pba50.loc[pd.notnull(zoning_parcels_pba50['geom_id']),]
    logger.info('zoning_parcels_pba50 is length {}'.format(len(zoning_parcels_pba50)))
    
    # so we can convert geom_id to int
    zoning_parcels_pba50['geom_id'] = zoning_parcels_pba50['geom_id'].round(0).astype(np.int64)

    logger.info('zoning_parcels_pba50 has {} records; table head:\n{}'.format(len(zoning_parcels_pba50), zoning_parcels_pba50.head()))

    # export
    logger.info('Export zoning_lookup table with the following attributes: {}'.format(zoning_lookup_pba50.dtypes))
    zoning_parcels_pba50.to_csv(ZONING_PARCELS_FILE,index = False)   

    logger.info('Export zoning_parcels table with the following attributes: {}'.format(zoning_parcels_pba50.dtypes))
    zoning_lookup_pba50.to_csv(ZONING_LOOKUP_FILE,index = False)
