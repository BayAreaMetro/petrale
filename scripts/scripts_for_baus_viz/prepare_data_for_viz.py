USAGE = """
Prepares UrbanSim model run data (output, key input, interim) for (Tableau) dashboard visualization.

Example call: 

Args: 
    run_dir: directory of model run data
    run_scenario: e.g. 's24' for Final Blueprint, 's28' for EIR Alt2
    scenario_group: e.g. Final Blueprint, EIR Alt2, DevRun
    description: description of the scenario and/or run group
    run_id: model run_id from the output, e.g. 'run182' for the official Final Blueprint run

Returns:
    [RUN_ID]_taz_summary.csv: TAZ-level key model output metrics; created from model taz output
    [RUN_ID]_juris_summary.csv: jurisdiction-level key model output metrics; created from model jurisdiction output
    [RUN_ID]_growth_geos_summary.csv: key model output metrics by Plan growth geographies; created from model geos output
    [RUN_ID]_parcel_output.csv: key metrics on individual development projects (buildings); created from model parcel_output output
    [RUN_ID]_dr_units_growth.csv: growth of deed-restricted residential units by source/Plan Strategy; created from model jurisdiction output
    model_run_inventory.csv: not newly created by running this script, but updated to include the new run's info.
  
"""

import pandas as pd
import numpy as np
import geopandas as gpd
import argparse, sys, logging, time, os, glob
import yaml


today = time.strftime("%Y_%m_%d")

if __name__ == '__main__':

    # process one run at a time
    parser = argparse.ArgumentParser(description=USAGE)
    parser.add_argument('run_dir', help='Provide the full directory of the model run')
    parser.add_argument('run_scenario', help='Provide the run scenario, e.g. s24')
    parser.add_argument('scenario_group', help='Provide the run scenario group name, e.g. Final Blueprint')
    parser.add_argument('run_description', help='Provide the run description, e.g. Model development test runs using s24 assumptions')
    parser.add_argument('run_id', help='Provide the run id, e.g. run182')
    parser.add_argument('--last_run', required=False, help='yes or no, indicating if it is the most recent run of a scenario. Default to yes')
    
    args = parser.parse_args()

    ############ I/O
    # INPUT - model run data
    MOEDL_RUN_DIR = args.run_dir
    RAW_INPUT_DIR = os.path.join(MOEDL_RUN_DIR, 'inputs')
    RAW_OUTPUT_DIR = os.path.join(MOEDL_RUN_DIR, 'outputs')
    # RAW_OUTPUT_DIR = MOEDL_RUN_DIR
    RUN_ID = args.run_id

    RUN_SCENARIO = args.run_scenario
    SCENARIO_GROUP = args.scenario_group
    RUN_DESCRIPTION = args.run_description

    if args.last_run:
        LAST_RUN = args.last_run
    else:
        LAST_RUN = 'yes'

    # INPUT - other helper data
    JURIS_NAME_CROSSWALK_FILE = 'M:\\Data\\Urban\\BAUS\\visualization_design\\data\\data_viz_ready\\crosswalks\\juris_county_id.csv'
    MODEL_RUN_INVENTORY_FILE = 'M:\\Data\\Urban\\BAUS\\visualization_design\\data\\model_run_inventory.csv'

    # OUTPUT - data for visualization
    VIZ_DIR = 'M:\\Data\\Urban\\BAUS\\visualization_design'
    VIA_DATA_DIR = os.path.join(VIZ_DIR, 'data')
    VIZ_READY_DATA_DIR = os.path.join(VIA_DATA_DIR, 'data_viz_ready', 'csv_v2')
    LOG_FILE = os.path.join(VIZ_READY_DATA_DIR, "prepare_data_for_viz_{}_{}.log".format(RUN_ID, today))

    TAZ_SUMMARY_FILE = os.path.join(VIZ_READY_DATA_DIR, '{}_taz_summary.csv'.format(RUN_ID))
    JURIS_SUMMARY_FILE = os.path.join(VIZ_READY_DATA_DIR, '{}_juris_summary.csv'.format(RUN_ID))
    GROWTH_GEOS_SUMMARY_FILE = os.path.join(VIZ_READY_DATA_DIR, '{}_growth_geos_summary.csv'.format(RUN_ID))
    PARCEL_OUTPUT_SUMMARY_FILE = os.path.join(VIZ_READY_DATA_DIR, '{}_parcel_output.csv'.format(RUN_ID))
    DR_UNITS_GROWTH_FILE = os.path.join(VIZ_READY_DATA_DIR, '{}_dr_units_growth.csv'.format(RUN_ID))
    UPDATED_MODEL_RUN_INVENTORY_FILE = 'M:\\Data\\Urban\\BAUS\\visualization_design\\data\\model_run_inventory.csv'

    ############ set up logging
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

    logger.info("running prepare_data_for_viz.py for: {}, {}, {}, {}".format(RUN_ID, RUN_SCENARIO, SCENARIO_GROUP, RUN_DESCRIPTION))
    logger.info("model data dir: {}".format(MOEDL_RUN_DIR))
    logger.info("write out files for dashboard viz at: {}".format(VIZ_READY_DATA_DIR))
    logger.info("update model run inventory {}".format(MODEL_RUN_INVENTORY_FILE))

    ############ process model output data
    
    ## TAZ output, from '[RUN_ID]_taz_summaries_[year].csv' to '[RUN_ID]_taz_summary.csv'

    # specify which TAZ attributes to include 
    # growth summaries 
    taz_summary_attr_cols = ['TOTHH', 'TOTEMP', 'EMPRES', 'RES_UNITS']
    # household / employment groups
    taz_hh_attr_cols = ['HHINCQ1', 'HHINCQ2', 'HHINCQ3', 'HHINCQ4']
    taz_emp_attr_cols = ['AGREMPN', 'FPSEMPN', 'HEREMPN', 'RETEMPN', 'MWTEMPN', 'OTHEMPN']

    # collect all TAZ summaries outputs
    all_taz_files = glob.glob(RAW_OUTPUT_DIR + "\{}_taz_summaries*.csv".format(RUN_ID))
    # NOTE: remove 2010 data since 2015 is the base year for PBA50
    all_taz_files = [file_dir for file_dir in all_taz_files if '2010' not in file_dir]
    logger.info(
        'processing {} taz_summaries files for key summaries: {}'.format(len(all_taz_files), all_taz_files))

    # loop through the list to process the files
    all_taz_df = pd.DataFrame()

    for file_dir in all_taz_files:
        year = file_dir.split("\\")[-1].split(".")[0].split("summaries_")[1][:4]
        logger.info('year: {}'.format(year))

        # load the data
        taz_df = pd.read_csv(
            file_dir,
            usecols = ['TAZ'] + taz_summary_attr_cols + taz_hh_attr_cols)
        # fill na with 0
        taz_df.fillna(0, inplace=True)
        # add year
        taz_df['year'] = year
        # append to the master table
        all_taz_df = pd.concat([all_taz_df, taz_df])
    
    # double check all years are here
    logger.debug('aggregated TAZ output has years: {}'.format(all_taz_df['year'].unique()))
    
    # TODO: modify field types, esp. integer fields
    logger.debug('aggregated TAZ output fields: \n{}'.format(all_taz_df.dtypes))
    logger.debug('header: \n{}'.format(all_taz_df.head()))

    # write out
    logger.info(
        'writing out {} rows of TAZ summary data to {}'.format(
            all_taz_df.shape[0], TAZ_SUMMARY_FILE))   
    all_taz_df.to_csv(TAZ_SUMMARY_FILE, index=False)

    ## Jurisdiction output, from '[RUN_ID]_juris_summaries_[year].csv' to '[RUN_ID]_juris_summary.csv'
    
    # specify which TAZ attributes to include
    # JURIS attributes for growth summaries
    juris_summary_attr_cols = ['tothh', 'totemp', 'res_units']
    # JURIS attributes for household / employment groups
    juris_hh_attr_cols = ['hhincq1', 'hhincq2', 'hhincq3', 'hhincq4']
    juris_emp_attr_cols = ['agrempn', 'mwtempn', 'retempn', 'fpsempn', 'herempn', 'othempn']
    # deed-restricted housing attributes
    juris_dr_units_atrr_cols = ['deed_restricted_units', 'preserved_units', 'inclusionary_units', 'subsidized_units']
    
    # collect all juris summaries outputs
    all_juris_files = glob.glob(RAW_OUTPUT_DIR + "\{}_juris_summaries*.csv".format(RUN_ID))
    # NOTE: remove 2010 data since 2015 is the base year for PBA50
    all_juris_files = [file_dir for file_dir in all_juris_files if '2010' not in file_dir]
    logger.info(
        'processing {} juris_summaries files for key summaries: {}'.format(len(all_juris_files), all_juris_files))
    
    # loop through the list of outputs
    all_juris_df = pd.DataFrame()

    for file_dir in all_juris_files:
        year = file_dir.split("\\")[-1].split(".")[0].split("summaries_")[1][:4]
        logger.info('year: {}'.format(year))
        
        # load the summary data
        juris_summary_df = pd.read_csv(
            file_dir,
            usecols = ['juris'] + juris_summary_attr_cols + juris_hh_attr_cols)       
        # fill na with 0
        juris_summary_df.fillna(0, inplace=True)
        # add year
        juris_summary_df['year'] = year    
        # append to the master table
        all_juris_df = pd.concat([all_juris_df, juris_summary_df])

    # double check all years are here
    logger.debug('aggregated Juris output has years: {}'.format(all_juris_df['year'].unique()))

    # make field names consistent with TAZ table
    all_juris_df_cols = [x.upper() for x in list(all_juris_df)]
    all_juris_df.columns = all_juris_df_cols

    # use jurisdiction name crosswalk to make naming convention consistent with in shapefile
    juris_name_crosswalk = pd.read_csv(
        JURIS_NAME_CROSSWALK_FILE, 
        usecols = ['baus_output_juris_name', 'shapefile_juris_name'])
    juris_name_crosswalk.rename(columns={'baus_output_juris_name': 'JURIS'}, inplace=True)

    all_juris_df = all_juris_df.merge(juris_name_crosswalk, on='JURIS', how='left')
    print(all_juris_df.head())

    # TODO: modify field types, esp. integer fields
    logger.debug('aggregated Juris output fields: \n{}'.format(all_juris_df.dtypes))
    logger.debug('header: \n{}'.format(all_juris_df.head()))

    # write out
    logger.info(
        'writing out {} rows of Juris summary data to {}'.format(
            all_juris_df.shape[0], JURIS_SUMMARY_FILE))  
    all_juris_df.to_csv(JURIS_SUMMARY_FILE, index=False)

    ## Deed-restrcited housing output, from '[RUN_ID]_juris_summaries_[year].csv' to  and '[RUN_ID]_dr_units_growth.csv'
    logger.info('processing juris_summaries files to calculate deed-restricted housing growth')

    # get base year 2015 data
    logger.info('year: 2015')
    juris_dr_2015_file = os.path.join(RAW_OUTPUT_DIR, "{}_juris_summaries_2015.csv".format(RUN_ID))
    juris_dr_2015_df = pd.read_csv(
        juris_dr_2015_file,
        usecols=['juris'] + juris_dr_units_atrr_cols).set_index('juris')

    # calculate units from project list
    juris_dr_2015_df['projs_list_units'] = \
            juris_dr_2015_df['deed_restricted_units'] - juris_dr_2015_df[['preserved_units', 'inclusionary_units', 'subsidized_units']].sum(axis=1)
    # add year to colnames
    juris_dr_2015_df.columns = [x+'_2015' for x in list(juris_dr_2015_df)]

    # loop through juris output of other years and calculate growth from 2015
    all_juris_dr_growth_df = pd.DataFrame()

    for file_dir in all_juris_files:
        if '2015' not in file_dir:
            # logger.debug(file_dir)
            juris_dr_forecast_df = pd.read_csv(
                file_dir,
                usecols = ['juris'] + juris_dr_units_atrr_cols).set_index('juris')
            juris_dr_forecast_df['projs_list_units'] = \
                juris_dr_forecast_df['deed_restricted_units'] - juris_dr_forecast_df[['preserved_units', 'inclusionary_units', 'subsidized_units']].sum(axis=1)
  
            year = file_dir.split("\\")[-1].split(".")[0].split("summaries_")[1][:4]
            logger.info('year: {}'.format(year))
            juris_dr_forecast_df.columns = [x+'_{}'.format(year) for x in list(juris_dr_forecast_df)]
            logger.debug('raw juris DR data: \n{}'.format(juris_dr_forecast_df.head()))
            
            # merge the forecast data with 2015 base year data, and calculate growth of each DR housing source 
            dr_units_growth = pd.concat([juris_dr_2015_df, juris_dr_forecast_df], axis=1)
            for colname in list(dr_units_growth):
                dr_units_growth[colname].fillna(0, inplace=True)
            logger.debug('after merging with base year data: \n{}'.format(dr_units_growth.head()))
            for attr in juris_dr_units_atrr_cols + ['projs_list_units']:
                dr_units_growth[attr+'_growth'] = dr_units_growth[attr+'_{}'.format(year)] - dr_units_growth[attr+'_2015']
            logger.debug('after calculating growth: \n{}'.format(dr_units_growth.head()))
            
            # add year tag to the table
            dr_units_growth['year'] = year

            # keep only needed fields
            dr_units_growth_export = dr_units_growth[[x for x in list(dr_units_growth) if 'growth' in x] + ['year']]
            logger.debug('after dropping raw fields: \n{}'.format(dr_units_growth_export.head()))
            
            # append to the master data
            all_juris_dr_growth_df = pd.concat([all_juris_dr_growth_df, dr_units_growth_export])
    
    # double check all years are here
    logger.debug(
        'aggregated DR units growth summary all_juris_dr_growth_df has years: {}'.format(all_juris_dr_growth_df['year'].unique()))

    # use crosswalk to get standard jurisdiction name
    all_juris_dr_growth_df.reset_index(inplace=True)
    all_juris_dr_growth_df.rename(columns = {'juris': 'JURIS'}, inplace=True)
    all_juris_dr_growth_df = all_juris_dr_growth_df.merge(juris_name_crosswalk, on='JURIS', how='left')

    # convert to integer
    all_juris_dr_growth_df = all_juris_dr_growth_df.astype({
        'deed_restricted_units_growth' :np.int32,
        'preserved_units_growth'   :np.int32,
        'inclusionary_units_growth'  :np.int32,
        'subsidized_units_growth'  :np.int32,
        'projs_list_units_growth'  :np.int32
        })
    
    logger.debug('final aggregated DR units growth table fields: \n{}'.format(all_juris_dr_growth_df.dtypes))

    # write out
    logger.info(
        'writing out {} rows of Juris summary data to {}'.format(
            all_juris_dr_growth_df.shape[0], DR_UNITS_GROWTH_FILE))
    all_juris_dr_growth_df.to_csv(DR_UNITS_GROWTH_FILE, index=False)

    ## growth summary by Plan growth geographies, from '[RUN_ID]_[geos]_growth_summaries.csv' to '[RUN_ID]_growth_geos_summary.csv'

    # dictionaries to recode growth geography types, and categories in each type
    geos_tag_recode = {
        'yes_DIS': 'in_DIS',
        'no_DIS': 'outside_DIS',
        'yes_GG': 'in_GG',
        'no_GG': 'outside_GG',
        'yes_HRA': 'in_HRA',
        'no_HRA': 'outside_HRA',
        'yes_tra': 'in_TRA',
        'no_tra': 'outside_TRA'}
    geo_category_recode = {
        'DIS': 'Displacement-risk',
        'GG':  'GG',
        'HRA': 'High-resource',
        'TRA': 'Transit-rich'}

    # collect needed geos summary outputs
    # all_growth_GGs_files = glob.glob(RAW_OUTPUT_DIR + "\*growth_summaries.csv")
    all_growth_GGs_files = [
        '{}_GG_growth_summaries.csv'.format(RUN_ID),
        '{}_tra_growth_summaries.csv'.format(RUN_ID),
        '{}_HRA_growth_summaries.csv'.format(RUN_ID),
        '{}_DIS_growth_summaries.csv'.format(RUN_ID)
    ]
    logger.info(
        'processing GEOs growth summary files: {}'.format(
            [os.path.join(RAW_OUTPUT_DIR, x) for x in all_growth_GGs_files]))

    # create a df to aggregate all outputs
    all_growth_GGs_df = pd.DataFrame()

    # loop through the tables, recode geos tag, and append to the master
    for file_name in all_growth_GGs_files:
        geo_tag = file_name.split('_')[1]

        logger.info('load {} for growth summary by {}'.format(file_name, geo_tag))

        growth_GGs_df = pd.read_csv(
            os.path.join(RAW_OUTPUT_DIR, file_name),
            usecols = ['county', 'juris', 'geo_category', 'tothh growth', 'totemp growth'])
        
        # add tag for type of growth geography
        growth_GGs_df['geography_type'] = geo_category_recode[geo_tag.upper()]

        # recode geography categories into more straight-forward descriptions
        growth_GGs_df['geo_category'] = growth_GGs_df['geo_category'].map(geos_tag_recode)
        logger.debug('geo categories contained: {}'.format(growth_GGs_df['geo_category'].unique()))
        # logger.debug(growth_GGs_df.head())

        # append to master table
        all_growth_GGs_df = pd.concat([all_growth_GGs_df, growth_GGs_df])

    # double check all geos are included
    logger.debug(
        'aggregated geo-growth summary contain the following growth geographies: {}'.format(
            all_growth_GGs_df['geography_type'].unique()))

    logger.debug('aggregated geo-growth summary table fields: \n{}'.format(all_growth_GGs_df.dtypes))
    logger.debug('header: \n{}'.format(all_growth_GGs_df.head()))

    # write out
    logger.info(
        'writing out {} rows of geo-growth summary data to {}'.format(
            all_growth_GGs_df.shape[0], GROWTH_GEOS_SUMMARY_FILE))
    all_growth_GGs_df.to_csv(GROWTH_GEOS_SUMMARY_FILE, index=False)

    ## simplify parcel_output data '[RUN_ID]_parcel_output.csv'

    file_dir = os.path.join(RAW_OUTPUT_DIR, '{}_parcel_output.csv'.format(RUN_ID))
    logger.info('processing parcel_output data: {}'.format(file_dir))

    # define which fields to include
    keep_cols = [
        'development_id', 'SDEM', 'building_sqft', 'building_type',
        'job_spaces', 'non_residential_sqft', 'residential', 'residential_sqft', 'residential_units', 
        'source', 'total_residential_units', 'total_sqft', 
        'x', 'y', 'year_built']
    
    try:
        parcel_output_df = pd.read_csv(
            file_dir,
            usecols = keep_cols)
        logger.info('parcel_output has {} rows'.format(parcel_output_df.shape[0]))

        # TODO: modify field types - e.g. year_built integer
        logger.debug('field types: \n{}'.format(parcel_output_df.dtypes))
        logger.debug('header: \n{}'.format(parcel_output_df.head()))

        # write out
        logger.info(
            'writing out {} rows of geo-growth summary data to {}'.format(
                parcel_output_df.shape[0], PARCEL_OUTPUT_SUMMARY_FILE))
        parcel_output_df.to_csv(PARCEL_OUTPUT_SUMMARY_FILE, index=False)

    except:
        logger.warning('parcel_output not exist for {}'.format(RUN_ID))


    ############ TODO: process model input and interim data


    ############ update run inventory log

    logger.info('adding the new run to model run inventory')
    model_run_inventory = pd.read_csv(MODEL_RUN_INVENTORY_FILE)
    logger.info('previous runs: {}'.format(model_run_inventory))

    # append the info of the new run
    NEW_RUN_INFO = [int(RUN_ID.split('run')[1]), RUN_SCENARIO, SCENARIO_GROUP, RUN_DESCRIPTION, LAST_RUN, MOEDL_RUN_DIR]
    logger.info('adding info of the new run: {}'.format(NEW_RUN_INFO))
    model_run_inventory.loc[len(model_run_inventory.index)] = NEW_RUN_INFO

    # TODO: if a new run of the same scenario was added, update previous runs of the same scenario to 'last_run' = 'no'

    # write out the updated inventory table
    model_run_inventory.to_csv(UPDATED_MODEL_RUN_INVENTORY_FILE, index=False)
