USAGE="""

  Given a set of base zoning (parcel-level) and zoning_mods (representing one upzoning scheme) data, 
  calculate the raw and net development capacity under the upzoning scheme.

  Input:  p10, parcels with PARCEL_ID, ACRES attributes
          zoning_parcels_hybrid_pba50.csv, p10 combined with zoning_id data output by 4_create_hybrid_urbansim_input.py
          zoning_lookup_hybrid_pba50.csv, lookup table of zoning_id to allowable development types and intensities
          p10_pba50_attr.csv, p10 combined with zoningmods categories data
  Output: upzoning_capacity.csv

  Run with (scenario 23 as an example): python calculate_upzoning_capacity.py --zoningmods_scenario "23" --test

  In test mode (specified by --test), outputs files to cwd and without date prefix; otherwise, outputs to PLU_BOC_DIR with date prefix

"""

import pandas as pd
import numpy as np
import argparse, os, glob, logging, sys, time
import dev_capacity_calculation_module

NOW = time.strftime("%Y_%m%d_%H%M")
today = time.strftime('%Y_%m_%d')


if os.getenv('USERNAME')     =='ywang':
    BOX_DIR                  = 'C:\\Users\\{}\\Box\\Modeling and Surveys\\Urban Modeling\\Bay Area UrbanSim 1.5\\PBA50'.format(os.getenv('USERNAME'))
    BOX_SMELT_DIR            = 'C:\\Users\\{}\\Box\\baydata\\smelt\\2020 03 12'.format(os.getenv('USERNAME'))
    GITHUB_URBANSIM_DIR      = 'C:\\Users\\{}\\Documents\\GitHub\\bayarea_urbansim\\data'.format(os.getenv('USERNAME'))
elif os.getenv('USERNAME')   =='lzorn':
    BOX_DIR                  = 'C:\\Users\\{}\\Box\\Modeling and Surveys\\Urban Modeling\\Bay Area UrbanSim 1.5\\PBA50'.format(os.getenv('USERNAME'))
    BOX_SMELT_DIR            = 'C:\\Users\\{}\\Box\\baydata\\smelt\\2020 03 12'.format(os.getenv('USERNAME'))
    GITHUB_URBANSIM_DIR      = 'C:\\Users\\{}\\Documents\\GitHub\\bayarea_urbansim\\data'.format(os.getenv('USERNAME'))

# input files
URBANSIM_BASEZONING_DIR      = os.path.join(BOX_DIR, 'Current PBA50 Large General Input Data')
PARCEL_ZONING_ID_FILE        = os.path.join(URBANSIM_BASEZONING_DIR, '2020_06_22_zoning_parcels_hybrid_pba50.csv')
BASEZONING_LOOKUP_FILE       = os.path.join(URBANSIM_BASEZONING_DIR, '2020_06_22_zoning_lookup_hybrid_pba50.csv')

PBA50_ZONINGMODS_DIR         = os.path.join(BOX_DIR, 'Policies\\Zoning Modifications')
PARCEL_ZONINGMODS_PBA50_FILE = os.path.join(PBA50_ZONINGMODS_DIR, 'p10_pba50_attr_20200416.csv')

# output file
# In test mode (specified by --test), outputs to cwd and without date prefix; otherwise, outputs to URBANSIM_UPZONING_DIR with date prefix
BOX_UPZONING_DIR             = os.path.join(BOX_DIR, 'Policies\\Zoning Modifications\\capacity')


# raw and net development capacity metrics
RAW_CAPACITY_CODES           = ['zoned_du',                   'zoned_Ksqft',                   'job_spaces']
NET_CAPACITY_CODES           = ['zoned_du_vacant',            'zoned_Ksqft_vacant',            'job_spaces_vacant',
                                'zoned_du_underbuild',        'zoned_Ksqft_underbuild',        'job_spaces_underbuild',
                                'zoned_du_underbuild_noProt', 'zoned_Ksqft_underbuild_noProt', 'job_spaces_underbuild_noProt']


def apply_upzoning_to_parcel_data(logger, parcel_basezoning_original, upzoning_scenario):
    """
    Apply upzoning to parcels by adjusting the allowable development types and intensities.

     * upzoning_scenario: version of zoning_mods for upzoning, e.g. 's20', 's21', 's22', 
                         's23' for Draft/Final Blueprint

    Returns a dataframe with columns PARCEL_ID, juris_zmod, plus XX_upzoning for each allowed 
    development type or intensity attribute.
    """
    


    # Make a copy and add '_basezoning' to basezoning attributes
    parcel_basezoning = parcel_basezoning_original.copy()


    # Read zoningmods lookup data and merge with parcels
    zmods_upzoning_file = os.path.join(GITHUB_URBANSIM_DIR, 'zoning_mods_'+upzoning_scenario+'.csv')

    if not os.path.exists(zmods_upzoning_file):
            print('Error: file {} not found'.format(zmods_upzoning_file))
            raise

    use_cols = ['pba50zoningmodcat','add_bldg', 'drop_bldg', 
                'dua_up', 'far_up', 'dua_down', 'far_down', 'res_rent_cat']
    zmods_upzoning_df = pd.read_csv(zmods_upzoning_file, usecols = use_cols)

    # Merge upzoning with basezoning
    parcel_basezoning_zoningmods = parcel_basezoning.merge(zmods_upzoning_df,
                                                           on = 'pba50zoningmodcat', 
                                                           how = 'left')

    keep_cols = list(parcel_basezoning)

    # create allowed development type and intensity columns for upzoning
    # and default to base zoning
    for dev_type in dev_capacity_calculation_module.ALLOWED_BUILDING_TYPE_CODES:
        parcel_basezoning_zoningmods["{}_{}".format(dev_type, upzoning_scenario)] = \
                parcel_basezoning_zoningmods["{}_basezoning".format(dev_type)]
        # keep the new column
        keep_cols.append("{}_{}".format(dev_type, upzoning_scenario))

    for intensity in dev_capacity_calculation_module.INTENSITY_CODES:
        parcel_basezoning_zoningmods["max_{}_{}".format(intensity, upzoning_scenario)] = \
                parcel_basezoning_zoningmods["max_{}_basezoning".format(intensity)]
        # keep the new column
        keep_cols.append("max_{}_{}".format(intensity, upzoning_scenario))


    # Get a list of development types that have modifications in pba50zoningmod
    add_bldg_types = list(zmods_upzoning_df.add_bldg.dropna().unique())
    logger.info('Development types enabled disallowed by upzoning:\n{}'.format(add_bldg_types))
    drop_bldg_types = list(zmods_upzoning_df.drop_bldg.dropna().unique())
    logger.info('Development types disallowed by upzoning:\n{}'.format(drop_bldg_types))


    # Make a copy and then modify the alowed dev types
    #zoning_modify_type = zoning_base_pba50.copy()

    if len(add_bldg_types) > 0:
        for devType in add_bldg_types:
            add_bldg_parcels = parcel_basezoning_zoningmods.add_bldg == devType
            parcel_basezoning_zoningmods.loc[add_bldg_parcels, devType+'_'+upzoning_scenario] = 1

    if len(drop_bldg_types) > 0:
        for devType in drop_bldg_types:
            drop_bldg_parcels = parcel_basezoning_zoningmods.drop_bldg == devType
            parcel_basezoning_zoningmods.loc[drop_bldg_parcels,devType+'_'+upzoning_scenario] = 0

    # Compare allowed dev types before and after applying pba50zoningmod
    for devType in add_bldg_types + drop_bldg_types:
        logger.info('Out of {:,} parcels: \n {:,} parcels allow {} before applying pba50zoningmod dev type adjustment;\
                    \n {:,} parcels allow {} after applying pba50zoningmod dev type adjustment.'.format(len(parcel_basezoning_zoningmods),
                    len(parcel_basezoning_zoningmods.loc[parcel_basezoning_zoningmods[devType+'_basezoning'] == 1]), devType,
                    len(parcel_basezoning_zoningmods.loc[parcel_basezoning_zoningmods[devType+'_'+upzoning_scenario] == 1]), devType))


    # Make a copy and then modify the intensities
    #zoning_modify_intensity = zoning_modify_type.copy()

    for intensity in ['dua','far']:

        # modify intensity when 'intensity_up' is not null
        up_parcels = parcel_basezoning_zoningmods['{}_up'.format(intensity)].notnull()

        # the effective max_dua is the larger of base zoning max_dua and the pba50 max_dua
        parcel_basezoning_zoningmods.loc[up_parcels, 'max_{}_{}'.format(intensity, upzoning_scenario)] = \
                parcel_basezoning_zoningmods[['max_{}_{}'.format(intensity, upzoning_scenario),'{}_up'.format(intensity)]].max(axis = 1)

        # modify intensity when 'intensity_up' is not null
        down_parcels = parcel_basezoning_zoningmods['{}_down'.format(intensity)].notnull()

        # the effective max_dua is the larger of base zoning max_dua and the pba50 max_dua
        parcel_basezoning_zoningmods.loc[down_parcels, 'max_{}_{}'.format(intensity, upzoning_scenario)] = \
                parcel_basezoning_zoningmods[['max_{}_{}'.format(intensity, upzoning_scenario),'{}_down'.format(intensity)]].min(axis = 1)

        # Compare max_dua and max_far before and after applying pba50zoningmod
        logger.info('Before applying pba50zoningmod intensity adjustment: \n', 
                    parcel_basezoning_zoningmods[['max_'+intensity+'_basezoning']].describe())
        logger.info('After applying pba50zoningmod intensity adjustment: \n', 
                    parcel_basezoning_zoningmods[['max_'+intensity+'_'+upzoning_scenario]].describe())

    parcel_upzoning = parcel_basezoning_zoningmods[keep_cols]
    logger.info('Generate parcel-level upzoning table of {:,} records: \n {}'.format(len(parcel_upzoning), parcel_upzoning.head()))
    return parcel_upzoning


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=USAGE, formatter_class=argparse.RawDescriptionHelpFormatter,)
    parser.add_argument("--zoningmods_scenario", choices=["21","22","23"], help="zoningmods scenario, choosing from '21', '22', '23'")
    parser.add_argument("--test", action="store_true", help="Test mode")
    args = parser.parse_args()


    UPZONING_CAPACITY_PARCEL_FILE = "upzoning_capacity_parcel_{}.csv".format(args.zoningmods_scenario)
    UPZONING_CAPACITY_JURIS_FILE  = "upzoning_capacity_juris_{}.csv".format(args.zoningmods_scenario)
    LOG_FILE                      = "upzoning_capacity_{}.log".format(args.zoningmods_scenario)

    if args.test == False:
        LOG_FILE                      = os.path.join(BOX_UPZONING_DIR, "{}_{}".format(today, LOG_FILE))
        UPZONING_CAPACITY_PARCEL_FILE = os.path.join(BOX_UPZONING_DIR, "{}_{}".format(today, UPZONING_CAPACITY_PARCEL_FILE))
        UPZONING_CAPACITY_JURIS_FILE  = os.path.join(BOX_UPZONING_DIR, "{}_{}".format(today, UPZONING_CAPACITY_JURIS_FILE))

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

    logger.info("BOX_UPZONING_DIR              = {}".format(BOX_UPZONING_DIR))
    logger.info("UPZONING_CAPACITY_PARCEL_FILE = {}".format(UPZONING_CAPACITY_PARCEL_FILE))
    logger.info("UPZONING_CAPACITY_JURIS_FILE  = {}".format(UPZONING_CAPACITY_JURIS_FILE))

    ## Read p10 parcels data
    basemap_p10_file = os.path.join(BOX_SMELT_DIR, 'p10.csv')
    basemap_p10 = pd.read_csv(basemap_p10_file,
                              usecols =['PARCEL_ID', 'ACRES','LAND_VALUE'])
    # conver PARCEL_ID to integer:
    basemap_p10['PARCEL_ID'] = basemap_p10['PARCEL_ID'].apply(lambda x: int(round(x)))
    logger.info("Read {:,} rows from {}".format(len(basemap_p10), basemap_p10_file))
    logger.info("\n{}".format(basemap_p10.head()))
    logger.info('Number of unique PARCEL_ID: {}'.format(len(basemap_p10.PARCEL_ID.unique())))


    ## Read parcel with base zoning data
    parcel_use_cols = ['PARCEL_ID', 'juris_id','zoning_id','nodev']
    parcel_zoning_id = pd.read_csv(PARCEL_ZONING_ID_FILE,
                                   usecols = parcel_use_cols)
    basezoning_lookup = pd.read_csv(BASEZONING_LOOKUP_FILE)
    basezoning_lookup.columns = [col+'_basezoning' for col in basezoning_lookup.columns.values]

    parcel_basezoning = parcel_zoning_id.merge(basezoning_lookup,
                                               left_on = 'zoning_id',
                                               right_on = 'id_basezoning',
                                               how = 'left')
    parcel_basezoning.rename(columns = {'nodev': 'nodev_basezoning'}, inplace = True)
    logger.info("Parcels with base zoning has {} records, with columns:\n{}".format(len(parcel_basezoning), parcel_basezoning.dtypes))

    # Read PBA50 zoningmods
    parcel_zoningmods = pd.read_csv(PARCEL_ZONINGMODS_PBA50_FILE, 
                                    usecols = ['PARCEL_ID', 'pba50zoningmodcat'])
    parcel_zoningmods.PARCEL_ID = parcel_zoningmods.PARCEL_ID.apply(lambda x: int(round(x)))

    ## Add base zoning and PBA50 zoningmods to p10 parcels
    p10_basezoning = basemap_p10.merge(parcel_basezoning,
                                       on = 'PARCEL_ID',
                                       how = 'left').merge(parcel_zoningmods,
                                                           on = 'PARCEL_ID',
                                                           how = 'left')

    logger.info("Running step ------ Applying upzoning {}".format('zoning_mods_'+args.zoningmods_scenario))

    p10_upzoning_pba50 = apply_upzoning_to_parcel_data(logger, p10_basezoning, args.zoningmods_scenario)

    logger.info("Generating p10_upzoning_pba50 with {} records;\n Headers:\n{}".format(len(p10_upzoning_pba50),
                                                                                       p10_upzoning_pba50.head()))

    # export combined zoning data for QA/QC
    #logger.info("Export p10_upzoning_pba50")
    #p10_upzoning_pba50.to_csv('p10_upzoning_pba50_{}.csv'.format(args.zoningmods_scenario), index = False)


    ## B10 buildings with p10 parcels data
    basemap_b10_file = os.path.join(BOX_SMELT_DIR, 'b10.csv')
    basemap_b10 = pd.read_csv(basemap_b10_file)
    # conver PARCEL_ID to integer:
    basemap_b10['parcel_id'] = basemap_b10['parcel_id'].apply(lambda x: int(round(x)))
    logger.info("Read {:,} rows from {}".format(len(basemap_b10), basemap_b10_file))
    logger.info("\n{}".format(basemap_b10.head()))
    logger.info('Number of unique PARCEL_ID: {}'.format(len(basemap_b10.parcel_id.unique())))

    # join parcels to buildings which is used to determine current built-out condition when calculating net capacity
    building_parcel = pd.merge(left=basemap_b10, 
                               right=basemap_p10[['PARCEL_ID','LAND_VALUE']],
                               left_on='parcel_id', 
                               right_on='PARCEL_ID', 
                               how='outer')

    # compute allowed development type - residential vs non-residential for each parcel
    basezoning_allow_dev_type = \
            dev_capacity_calculation_module.set_allow_dev_type(p10_upzoning_pba50, boc_source="basezoning")
    upzoning_allow_dev_type   = \
            dev_capacity_calculation_module.set_allow_dev_type(p10_upzoning_pba50, boc_source=args.zoningmods_scenario)

    # put them together
    p10_upzoning_pba50 = p10_upzoning_pba50.merge(basezoning_allow_dev_type,
                                                  on = 'PARCEL_ID',
                                                  how = 'left').merge(upzoning_allow_dev_type,
                                                                       on = 'PARCEL_ID',
                                                                       how = 'left')
    
    logger.debug("p10_upzoning_pba50 with columns:\n{}".format(p10_upzoning_pba50.dtypes))


    ## calculate raw and net capacity for basezoning and upzoning

    logger.info("Running step ------ Calculating raw development capacity under basezoning")

    raw_capacity_basezoning = dev_capacity_calculation_module.calculate_capacity(p10_upzoning_pba50,
                                                                                 "basezoning",
                                                                                 "basezoning",
                                                                                 pass_thru_cols=["juris_id"])
    logger.debug("raw_capacity_basezoning.head():\n{}".format(raw_capacity_basezoning.head()))

    logger.info("Running step ------ Calculating raw development capacity under {}".format('zoning_mods_'+args.zoningmods_scenario))
    raw_capacity_upzoning = dev_capacity_calculation_module.calculate_capacity(p10_upzoning_pba50,
                                                                               args.zoningmods_scenario,
                                                                               "basezoning",
                                                                               pass_thru_cols=["juris_id"])
    logger.debug("raw_capacity_upzoning.head():\n{}".format(raw_capacity_upzoning.head()))
    
    logger.info("Running step ------ Calculating net development capacity under basezoning")

    net_capacity_basezoning = dev_capacity_calculation_module.calculate_net_capacity(logger, 
                                                                                     p10_upzoning_pba50,
                                                                                     "basezoning",
                                                                                     "basezoning",
                                                                                     building_parcel,
                                                                                     net_pass_thru_cols=["juris_id"])
    logger.debug("net_capacity_basezoning.head():\n{}".format(net_capacity_basezoning.head()))   

    logger.info("Running step ------ Calculating net development capacity under {}".format('zoning_mods_'+args.zoningmods_scenario))
    net_capacity_upzoning = dev_capacity_calculation_module.calculate_net_capacity(logger, 
                                                                                   p10_upzoning_pba50,
                                                                                   args.zoningmods_scenario,
                                                                                   "basezoning",
                                                                                   building_parcel,
                                                                                   net_pass_thru_cols=["juris_id"])
    logger.debug("net_capacity_upzoning.head():\n{}".format(net_capacity_upzoning.head()))

    parcel_capacity_all = raw_capacity_basezoning.merge(net_capacity_basezoning,
                                                        on = 'juris_id').merge(parcel_capacity_upzoning,
                                                                               on = 'juris_id').merge(raw_capacity_upzoning,
                                                                                                      on = 'juris_id').merge(net_capacity_upzoning,
                                                                                                                             on = 'juris_id')
    # export parcel-level capacity
    logger.info('Export development capacity by parcel: \n{}'.format(parcel_capacity_all.dtypes))
    parcel_capacity_all.to_csv(UPZONING_CAPACITY_PARCEL_FILE, index = False)

    
    ## calculate jurisdiction-level capacity
    juris_capacity_basezoning = parcel_capacity_all.groupby(["juris_id"])[[raw_metrics + '_basezoning' for raw_metrics in RAW_CAPACITY_CODES] + 
                                                                          [net_metrics + '_basezoning' for net_metrics in NET_CAPACITY_CODES]].sum().reset_index()

    juris_capacity_upzoning   = parcel_capacity_all.groupby(["juris_id"])[[raw_metrics + '_' + args.zoningmods_scenario for raw_metrics in RAW_CAPACITY_CODES] + 
                                                                          [net_metrics + '_' + args.zoningmods_scenario for net_metrics in NET_CAPACITY_CODES]].sum().reset_index()
                                                                   

    logger.debug("juris_capacity_upzoning.head():\n{}".format(juris_capacity_upzoning.head()))

    ## export jurisdiction-level capacity
    logger.info("Export upzoning development capacity by jurisdiciton: \n{}".format(juris_capacity_upzoning.dtypes))
    juris_capacity_upzoning.to_csv(UPZONING_CAPACITY_FILE, index = False)