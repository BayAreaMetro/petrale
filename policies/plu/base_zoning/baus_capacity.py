
USAGE="""

  Calculate development capacity at the jurisdiction level based on BAUS run results. 

  Input:  parcel_data_2050.csv, BAUS output parcel data
          building_data_2050.csv, BAUS output building data
          parcels_geography.csv, BAUS input data with parcel_id - jurisdiction mapping

  Output: baus_capacity_parcel.csv
          baus_capacity_juris.csv

  Run with (v1.7.1 Final Draft Blueprint Scenario 23 as an example): 
    python baus_capacity.py --baus_output_dir "Draft Blueprint runs\Blueprint Plus Crossing (s23)\v1.7.1- FINAL DRAFT BLUEPRINT" --baus_run_id 98 --zoningmods_scenario 23

  In test mode (specified by --test), outputs files to cwd and without date prefix; otherwise, outputs to PLU_BOC_DIR with date prefix

"""

import pandas as pd
import numpy as np
import argparse, os, glob, logging, sys, time

NOW = time.strftime("%Y_%m%d_%H%M")
today = time.strftime('%Y_%m_%d')


if os.getenv('USERNAME')  =='ywang':
    BOX_DIR               = 'C:\\Users\\{}\\Box\\Modeling and Surveys\\Urban Modeling\\Bay Area UrbanSim 1.5\\PBA50'.format(os.getenv('USERNAME'))
    ZONED_CAPACITY_DIR    = os.path.join(BOX_DIR, 'Policies', 'Zoning Modifications', 'capacity')
    URBANSIM_INPUT_DIR    = os.path.join(BOX_DIR, 'Current PBA50 Large General Input Data')


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=USAGE, formatter_class=argparse.RawDescriptionHelpFormatter,)
    parser.add_argument("--baus_output_dir", help="urbansim run results folder")
    parser.add_argument("--baus_run_id", help="urbansim run id in integer")
    parser.add_argument("--zoningmods_scenario", choices=["21","22","23"], help="zoningmods scenario, choosing from '21', '22', '23'")
    parser.add_argument("--test", action="store_true", help="Test mode")
    args = parser.parse_args()

    # inputs
    URBANSIM_INPUT_FILE           = os.path.join(URBANSIM_INPUT_DIR, '2020_07_10_parcels_geography.csv')
    BAUS_OUTPUT_PARCEL_FILE       = "run{}_parcel_data_2050.csv".format(str(args.baus_run_id))
    BAUS_OUTPUT_BUILDING_FILE     = "run{}_building_data_2050.csv".format(str(args.baus_run_id))

    # outputs
    BAUS_CAPACITY_JURIS_FILE      = 'baus_capacity_juris_{}.csv'.format(args.zoningmods_scenario)
    BAUS_CAPACITY_PARCEL_FILE     = 'baus_capacity_parcel_{}.csv'.format(args.zoningmods_scenario)
    LOG_FILE                      = 'baus_capacity_{}.log'.format(args.zoningmods_scenario)

    if args.test == False:
        BAUS_CAPACITY_JURIS_FILE  = os.path.join(ZONED_CAPACITY_DIR, "{}_{}".format(today, BAUS_CAPACITY_JURIS_FILE))
        BAUS_CAPACITY_PARCEL_FILE = os.path.join(ZONED_CAPACITY_DIR, "{}_{}".format(today, BAUS_CAPACITY_PARCEL_FILE))
        LOG_FILE                  = os.path.join(ZONED_CAPACITY_DIR, "{}_{}".format(today, LOG_FILE))


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

    logger.info("ZONED_CAPACITY_DIR    = {}".format(ZONED_CAPACITY_DIR))
    logger.info("BAUS_CAPACITY_FILE = {}".format(BAUS_CAPACITY_JURIS_FILE))


    # Read baus output parcel data
    baus_parcel_file = os.path.join(BOX_DIR, args.baus_output_dir, BAUS_OUTPUT_PARCEL_FILE)
    parcel_cols = ['parcel_id', 'zoned_du_underbuild', 'zoned_du', 'zoned_du_underbuild_nodev', 'totemp']
    baus_parcel = pd.read_csv(baus_parcel_file,
                              usecols = parcel_cols)
    logger.info('Read {:,} rows from {}, with {:,} unique parcel_ids'.format(len(baus_parcel), 
                                                                             baus_parcel_file, 
                                                                             len(baus_parcel.parcel_id.unique())))

    # Read baus output building data
    baus_blg_file = os.path.join(BOX_DIR, args.baus_output_dir, BAUS_OUTPUT_BUILDING_FILE)
    blg_cols = ['residential_units', 'non_residential_sqft', 'parcel_id', 'job_spaces']
    baus_blg = pd.read_csv(baus_blg_file,
                           usecols = blg_cols)
    logger.info('Read {:,} rows from {}, with {:,} unique parcel_ids'.format(len(baus_blg), 
                                                                             baus_blg_file, 
                                                                             len(baus_blg.parcel_id.unique())))
    # Aggregate building data to parcel level
    baus_blg_agg = baus_blg.groupby(['parcel_id']).sum().reset_index()

    # Merge parcel and building data to get baus output capacity
    baus_capacity = baus_parcel.merge(baus_blg_agg,
                                      on = 'parcel_id',
                                      how = 'outer')

    # Read parcel_id to jurisdiction mapping and join to capacity
    parcel_juris = pd.read_csv(URBANSIM_INPUT_FILE,
                               usecols = ['PARCEL_ID','juris_name_full'])
    baus_capacity = baus_capacity.merge(parcel_juris,
                                        left_on = 'parcel_id',
                                        right_on = 'PARCEL_ID',
                                        how = 'outer')

    # Add 'baus' label to field names
    baus_capacity.rename(columns = {'residential_units'        :'res_units_baus',
                                    'job_spaces'               :'job_spaces_baus',
                                    'non_residential_sqft'     :'nonRes_sqft_baus',
                                    'zoned_du_underbuild'      :'zoned_du_underbuild_baus',
                                    'zoned_du'                 :'zoned_du_baus',
                                    'zoned_du_underbuild_nodev':'zoned_du_underbuild_noProt_baus',
                                    'totemp'                   :'totemp_baus'}, inplace = True)

    logger.info('Export baus development capacity by parcel with header: \n {}'.format(baus_capacity.head()))
    baus_capacity.to_csv(BAUS_CAPACITY_PARCEL_FILE, index = False)


    # Aggregate to jurisdiction level
    baus_capacity_juris = baus_capacity.groupby(['juris_name_full'])['zoned_du_baus',
                                                                     'zoned_du_underbuild_baus',
                                                                     'zoned_du_underbuild_noProt_baus',
                                                                     'res_units_baus',
                                                                     'nonRes_sqft_baus',
                                                                     'job_spaces_baus',
                                                                     'totemp_baus'].sum().reset_index()
    baus_capacity_juris['nonRes_Ksqft_baus'] = baus_capacity_juris['nonRes_sqft_baus'] / 1000.0
    baus_capacity_juris.drop(columns = ['nonRes_sqft_baus'], inplace = True)

    logger.info('Export baus development capacity by jurisdiction with header: \n {}'.format(baus_capacity_juris.head()))
    baus_capacity_juris.to_csv(BAUS_CAPACITY_JURIS_FILE, index = False)