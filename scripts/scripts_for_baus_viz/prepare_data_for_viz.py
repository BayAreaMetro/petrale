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

    # INPUT - growth geometries
    # FBP growth geographies
    FBPZONINGMODCAT_SYSTEM_FILE = 'M:\\Data\\Urban\\BAUS\\visualization_design\\data\\data_viz_ready\\crosswalks\\fbpzoningmodcat_attrs.csv'
    EIRZONINGMODCAT_SYSTEM_FILE = 'M:\\Data\\Urban\\BAUS\\visualization_design\\data\\data_viz_ready\\crosswalks\\eirzoningmodcat_attrs.csv'

    # INPUT - other helper data
    JURIS_NAME_CROSSWALK_FILE = 'M:\\Data\\Urban\\BAUS\\visualization_design\\data\\data_viz_ready\\crosswalks\\juris_county_id.csv'
    MODEL_RUN_INVENTORY_FILE = 'M:\\Data\\Urban\\BAUS\\visualization_design\\data\\model_run_inventory.csv'

    # OUTPUT - folder for visualization data
    VIZ_DIR = 'M:\\Data\\Urban\\BAUS\\visualization_design'
    VIA_DATA_DIR = os.path.join(VIZ_DIR, 'data')
    VIZ_READY_DATA_DIR = os.path.join(VIA_DATA_DIR, 'data_viz_ready', 'csv_v2')
    LOG_FILE = os.path.join(VIZ_READY_DATA_DIR, "prepare_data_for_viz_{}_{}.log".format(RUN_ID, today))

    # OUTPUT - model inputs
    REGIONAL_CONTROLS_FILE = os.path.join(VIZ_READY_DATA_DIR, '{}_regional_controls.csv'.format(RUN_ID))
    PIPELINE_FILE = os.path.join(VIZ_READY_DATA_DIR, '{}_pipeline.csv'.format(RUN_ID))
    STRATEGY_PROJECT_FILE = os.path.join(VIZ_READY_DATA_DIR, '{}_strategy_projects.csv'.format(RUN_ID))
    STRATEGY_UPZONING_FILE = os.path.join(VIZ_READY_DATA_DIR, '{}_strategy_upzoning.csv'.format(RUN_ID))
    BASELINE_INCLUSIONARY_FILE = os.path.join(VIZ_READY_DATA_DIR, '{}_baseline_upzoning.csv'.format(RUN_ID))
    STRATEGY_INCLUSIONARY_FILE = os.path.join(VIZ_READY_DATA_DIR, '{}_strategy_IZ.csv'.format(RUN_ID))
    STRATEGY_HOUSING_BOND_FILE = os.path.join(VIZ_READY_DATA_DIR, '{}_strategy_housingBond.csv'.format(RUN_ID))
    STRATEGY_DEV_COST_FILE = os.path.join(VIZ_READY_DATA_DIR, '{}_strategy_devCost.csv'.format(RUN_ID))
    STRATEGY_PRESERVE_TARGET_FILE = os.path.join(VIZ_READY_DATA_DIR, '{}_strategy_unitPreserve_target.csv'.format(RUN_ID))
    STRATEGY_PRESERVE_QUALIFY_FILE = os.path.join(VIZ_READY_DATA_DIR, '{}_strategy_unitPreserve.csv'.format(RUN_ID))

    # OUTPUT - model interim data

    # OUTPUT - model outputs
    TAZ_SUMMARY_FILE = os.path.join(VIZ_READY_DATA_DIR, '{}_taz_summary.csv'.format(RUN_ID))
    JURIS_SUMMARY_FILE = os.path.join(VIZ_READY_DATA_DIR, '{}_juris_summary.csv'.format(RUN_ID))
    GROWTH_GEOS_SUMMARY_FILE = os.path.join(VIZ_READY_DATA_DIR, '{}_growth_geos_summary.csv'.format(RUN_ID))
    PARCEL_OUTPUT_SUMMARY_FILE = os.path.join(VIZ_READY_DATA_DIR, '{}_parcel_output.csv'.format(RUN_ID))
    DR_UNITS_GROWTH_FILE = os.path.join(VIZ_READY_DATA_DIR, '{}_dr_units_growth.csv'.format(RUN_ID))
    UPDATED_MODEL_RUN_INVENTORY_FILE = 'M:\\Data\\Urban\\BAUS\\visualization_design\\data\\model_run_inventory.csv'


    ############ helpers

    # dictionary to recode building 'source' - appear both in 'parcel_output' and 'development_projects_list'
    building_source_recode = {
        'manual'            : 'Pipeline',
        'cs'                : 'Pipeline',
        'basis'             : 'Pipeline',
        'bas_bp_new'        : 'Pipeline', 
        'rf'                : 'Pipeline',
        'opp'               : 'Pipeline',

        'developer_model'   : 'Developer Model',
        
        'h5_inputs'         : 'H5 Inputs',
        
        'pub'               : 'Public Land',
        'mall_office'       : 'Mall & Office Park',
        'incubator'         : 'Incubator',
        'ppa'               : 'PPA'
    }

    # dictionary to map strategy/policy geographies into the 'geo_type' tag, e.g. 
    geo_type_dict = {}

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

        # recode 'source' to be consistent with 
        parcel_output_df['source_cat'] = parcel_output_df['source'].map(building_source_recode)

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


    ############ process model input and interim data
    logger.info('start processing model inputs')

    ## pipeline projects and strategy-based asserted projects
    # NOTE: the two datasets now are in one table; they will be in separately tables per the BASIS process
    dev_project_file = os.path.join(RAW_INPUT_DIR, 'basis_inputs', 'parcels_buildings_agents', '2021_0309_1939_development_projects.csv')
    dev_project_df = pd.read_csv(dev_project_file)  
    logger.info(
        'loaded {} rows of development projects, containing the following source: \n{}'.format(
            dev_project_df.shape[0],
            dev_project_df['source'].unique()))

    # split the data by two categories of "source"
    pipeline_df = dev_project_df.loc[dev_project_df.source.isin(['manual', 'cs', 'basis', 'bas_bp_new', 'rf', 'opp'])][[
                    'development_projects_id', 'site_name', 'action',
                    'x', 'y', 'year_built', 'building_type', 'source',
                    'building_sqft', 'non_residential_sqft', 'residential_units',
                    'tenure', 'deed_restricted_units']]
    pipeline_df['source_cat'] = pipeline_df['source'].map(building_source_recode)

    strategy_projects_df = dev_project_df.loc[dev_project_df.source.isin(['pub', 'mall_office', 'incubator', 'ppa'])][[
                    'development_projects_id', 'site_name', 'action',
                    'x', 'y', 'year_built', 'building_type', 'source',
                    'building_sqft', 'non_residential_sqft', 'residential_units',
                    'tenure', 'deed_restricted_units']]
    strategy_projects_df['source_cat'] = strategy_projects_df['source'].map(building_source_recode)

    # export
    pipeline_df.to_csv(PIPELINE_FILE, index=False)
    logger.info('wrote out {} rows of pipeline data to {}'.format(pipeline_df.shape[0], PIPELINE_FILE))
    strategy_projects_df.to_csv(STRATEGY_PROJECT_FILE, index=False)
    logger.info('wrote out {} rows of strategy-based projects data to {}'.format(strategy_projects_df.shape[0], STRATEGY_PROJECT_FILE))

    ## regional controls
    hh_control_df = os.path.join(RAW_INPUT_DIR, 'regional_controls', 'household_controls.csv')
    emp_control_df = os.path.join(RAW_INPUT_DIR, 'regional_controls', 'employment_controls.csv')

    def consolidate_regional_control(hh_control_df_raw, emp_control_df_raw):
        """
        stack and consolidate regional household controls and employment controls for Tableau viz
        """
        hh_control_df_raw.set_index('year', inplace=True)
        hh_control_df = hh_control_df_raw.stack().reset_index()
        hh_control_df.columns = ['year', 'breakdown', 'hh_control']

        emp_control_df_raw.set_index('year', inplace=True)
        emp_control_df = emp_control_df_raw.stack().reset_index()
        emp_control_df.columns = ['year', 'breakdown', 'emp_control']

        control_df = pd.concat([hh_control_df, emp_control_df])
        control_df.fillna(0, inplace=True)

        return control_df

    regional_controls_df = consolidate_regional_control(hh_control_df, emp_control_df)
    # write out
    regional_controls_df.to_csv(REGIONAL_CONTROLS_FILE, index=False)
    logger.info('wrote out {} rows of regional controls data to {}'.format(regional_controls_df.shape[0], REGIONAL_CONTROLS_FILE))

    ## strategy - upzoning
    logger.info('process strategy zoming_mods')

    # load the data
    zmod_df = pd.read_csv(os.path.join(RAW_INPUT_DIR, 'plan_strategies', 'zoning_mods.csv'))

    # only keep needed fields
    zmod_df = zmod_df[['fbpzoningmodcat', 'dua_up', 'far_up', 'dua_down', 'far_down']]

    # make column names Plan-/scenario-agnostic
    if 'fbpzoningmodcat' in list(zmod_df):
        zmod_df.rename(columns = {'fbpzoningmodcat': 'zoningmodcat'}, inplace=True)
        zmod_df['geo_type'] = 'zoningmodcat_fbp'
    elif 'eirzoningmodcat' in list(zmod_df):
        zmod_df.rename(columns = {'fbpzoningmodcat': 'zoningmodcat'}, inplace=True)
        zmod_df['geo_type'] = 'zoningmodcat_eir'
    elif 'zoningmodcat' in list(zmod_df):
        zmod_df['geo_type'] = 'zoningmodcat_generic'

    # write out
    zmod_df.to_csv(STRATEGY_UPZONING_FILE, index=False)

    ## strategies in the yaml file
    policy_input = os.path.join(RAW_INPUT_DIR, 'plan_strategies', 'policy.yaml')
    logger.info('process inclusionary zoning existing policy and strategy from {}'.format(policy_input))
    # policy_input = os.path.join(r'C:\Users\ywang\Box\Modeling and Surveys\Urban Modeling\Bay Area UrbanSim\PBA50Plus_Development\Clean Code PR #3\inputs', 'plan_strategies', 'policy.yaml')

    with open(policy_input, 'r') as stream:
        try:
            policy_yaml = yaml.safe_load(stream)
            # print(policy_yaml)
        except yaml.YAMLError as exc:
            print(exc)

    # a helper function to reformat the IZ data, called by 'inclusionary_yaml_to_df()'
    def explode_df_list_col_to_rows(df, list_col):
        """
        Explode dataframe where one column contains list values.
        
        list_col: name of the column whose values are lists

        Example:
        - input df : pd.DataFrame({'non_list_col': [1, 2], 'list_col': [['a', 'b'], 'c']})
        - output df: pd.DataFrame({'non_list_col': [1, 1, 2], 'list_col': ['a', 'b', 'c']})

        """
        # get columns whose values will be repeated for each item in the list of the list column
        repeating_cols = list(df)
        # print(list_col)
        repeating_cols.remove(list_col)
        # print(repeating_cols)

        tmp_dict = {}
        # iterate through rows and each item of each list; add the values to a temp dictionary
        for i in range(df.shape[0]):
            # print(i)
            # print(df.iloc[i, :][list_col])
            for list_item in df.iloc[i, :][list_col]:
                # print(list_item)
                # print(df.iloc[i, :][repeating_cols])
                tmp_dict[list_item] = df.iloc[i, :][repeating_cols]
        
        exploded_df = pd.DataFrame.from_dict(tmp_dict, orient='index').reset_index()

        return exploded_df

    # a helper function to extract IZ data from policy.yaml
    def inclusionary_yaml_to_df(yaml_f):
        """
        Extract inclusionary settings in yaml based on scenario and convert to dataframe.
        
        Args:
        - yaml_f: yaml file
        - scen: scenarions in string, including 'default' for NoProject
        - geo_type: 'jurisdiction' or 'fbpchcat' in string
        
        Return:
        - inclusionary_df: a dataframe of two columns: 
            geo_type: type of inclusionary-zoning policy geography, to be joined to policy-geographies
            'geography': inclusionary-zoning policy geography,
            scenario: scenario,
            'value': the inclusionary zoning value in percentage.
        """
        
        # get the inclusionary setting of the target scenario
        IZ_raw = yaml_f['inclusionary_housing_settings']
        print('inclusionary data contains the following scenarios: {}'.format(IZ_raw.keys()))
    #     print(inclusionary_raw)
        
        # convert default and strategy into dataframes
        try:
            print('process default IZ data')
            IZ_default_raw_df = pd.DataFrame(IZ_raw['default'])
            IZ_default_df = explode_df_list_col_to_rows(IZ_default_raw_df, 'values')
            IZ_default_df.rename(columns = {'type': 'geo_type',
                                            'index': 'geo_category'}, inplace=True)

        except:
            print('no default IZ data')

        try:
            print('process strategy IZ data')
            IZ_strategy_raw_df = pd.DataFrame(IZ_raw['inclusionary_strategy'])
            IZ_strategy_df = explode_df_list_col_to_rows(IZ_strategy_raw_df, 'values')
            IZ_strategy_df.rename(columns = {'type': 'geo_type',
                                            'index': 'geo_category'}, inplace=True)
        except:
            print('no strategy IZ data')

        return (IZ_default_df, IZ_strategy_df)

    # get default IZ and IZ strategy tables
    IZ_default_df, IZ_strategy_df = inclusionary_yaml_to_df(policy_yaml)
    IZ_default_df.to_csv(BASELINE_INCLUSIONARY_FILE, index=False)
    IZ_strategy_df.to_csv(STRATEGY_INCLUSIONARY_FILE, index=False)

    # strategy - housing bond subsidies
    # first load the strategy geometry categories and attach strategy info as new columns
    if RUN_SCENARIO in ['s24', 's25']:
        zoningmodcat_df = pd.read_csv(FBPZONINGMODCAT_SYSTEM_FILE)
    if RUN_SCENARIO in ['s28']:
        zoningmodcat_df = pd.read_csv(EIRZONINGMODCAT_SYSTEM_FILE)
    
    # add column 'housing_bonds' to tag geography categories based on eligibility to receive bond subsidies
    strategy_housing_bonds = zoningmodcat_df[['zoningmodcat', 'geo_type', 'shapefile_juris_name']].copy()

    # baseline scenario with no strategy
    strategy_housing_bonds['housing_bonds'] = 'Not qualify'

    # scenarios with strategies
    if RUN_SCENARIO in ['s24']:
        qualify_idx = "gg_id == 'GG'"
    elif RUN_SCENARIO in ['s28']:
        qualify_idx = "gg_id == 'GG' and tra_id == 'NA' and sesit_id in ('HRA', 'HRADIS')"
    strategy_housing_bonds.loc[strategy_housing_bonds.eval(qualify_idx), 'housing_bonds'] = 'Qualify'
    logger.debug('housing_bond value counts: \n{}'.format(strategy_housing_bonds['housing_bonds'].value_counts(dropna=False)))

    # write out
    strategy_housing_bonds.to_csv(STRATEGY_HOUSING_BOND_FILE, index=False)

    # strategy - development cost reduction, represented by columns 'housing_devCost_reduction_cat' and 'housing_devCost_reduction_amt'
    strategy_devcost = zoningmodcat_df[['zoningmodcat', 'geo_type', 'shapefile_juris_name']].copy()

    # baseline scenario with no strategy
    strategy_devcost['housing_devCost_reduction_cat'] = 'None'
    strategy_devcost['housing_devCost_reduction_amt'] = 0

    # scenarios with strategies - 3 cost reduction tiers
    if RUN_SCENARIO in ['s24', 's28']:
        # tier 1: reduce dev cost by 0.025
        cost_tier1_idx  = "gg_id == 'GG' and tra_id in ('tra1', 'tra2a', 'tra2b', 'tra2c') and sesit_id in ('HRA', 'HRADIS')"

        # tier 2: reduce dev cost by 0.019
        cost_tier2_idx_part1 = "gg_id == 'GG' and tra_id in ('tra1') and sesit_id in ('DIS', 'NA')"      # GG and tra1 and non-HRA
        cost_tier2_idx_part2 = "gg_id == 'GG' and tra_id in ('tra3') and sesit_id in ('HRA', 'HRADIS')"  # GG and tra3 and HRA

        # tier 3: reduce dev cost by 0.013
        cost_tier3_idx_part1 = "gg_id == 'GG' and tra_id in ('tra3') and sesit_id in ('DIS', 'NA')"      # GG and tra3 and non-HRA
        cost_tier3_idx_part2 = "gg_id == 'GG' and tra_id == 'NA' and sesit_id in ('HRA', 'HRADIS')"      # GG and non-TRA and HRA

        # tag the columns base on cost reduction tier
        strategy_devcost.loc[strategy_devcost.eval(cost_tier1_idx), 'housing_devCost_reduction_cat'] = 'Tier 1'
        strategy_devcost.loc[strategy_devcost.eval(cost_tier1_idx), 'housing_devCost_reduction_amt'] = 0.025

        strategy_devcost.loc[strategy_devcost.eval(cost_tier2_idx_part1), 'housing_devCost_reduction_cat'] = 'Tier 2'
        strategy_devcost.loc[strategy_devcost.eval(cost_tier2_idx_part1), 'housing_devCost_reduction_amt'] = 0.019
        strategy_devcost.loc[strategy_devcost.eval(cost_tier2_idx_part2), 'housing_devCost_reduction_cat'] = 'Tier 2'
        strategy_devcost.loc[strategy_devcost.eval(cost_tier2_idx_part2), 'housing_devCost_reduction_amt'] = 0.019

        strategy_devcost.loc[strategy_devcost.eval(cost_tier3_idx_part1), 'housing_devCost_reduction_cat'] = 'Tier 3'
        strategy_devcost.loc[strategy_devcost.eval(cost_tier3_idx_part1), 'housing_devCost_reduction_amt'] = 0.013
        strategy_devcost.loc[strategy_devcost.eval(cost_tier3_idx_part2), 'housing_devCost_reduction_cat'] = 'Tier 3'
        strategy_devcost.loc[strategy_devcost.eval(cost_tier3_idx_part2), 'housing_devCost_reduction_amt'] = 0.013

    logger.debug(
        'devCost reduction amt value counts: \n{}'.format(
            strategy_devcost['housing_devCost_reduction_amt'].value_counts(dropna=False)))

    # strategy - naturally-occuring  affordable housing preservation

    # get preservation target amount from policy.yaml
    strategy_preserveTarget = pd.DataFrame(columns = ['geo_category', 'geo_type', 'batch1', 'batch2', 'batch3', 'batch4'])
    # also, tag geographies based on whether housing in a geography would be candicates for housing preservation
    strategy_preserveQualify = zoningmodcat_df[['zoningmodcat', 'geo_type', 'shapefile_juris_name']].copy()

    # baseline scenario with no strategy
    strategy_preserveQualify['preserve_candidate'] = ''

    # if strategy scenario, policy.yaml should contain the strategy
    try:
        # extract preservation target
        strategy_geo_type = policy_yaml['housing_preservation']['geography']

        for geo_category in policy_yaml['housing_preservation']['settings']:
        #     print(county)
            config = policy_yaml['housing_preservation']['settings'][geo_category]
            first_batch_target = config['first_unit_target']
            second_unit_target = config['second_unit_target']
            third_unit_target = config['third_unit_target']
            fourth_unit_target = config['fourth_unit_target']
            
            strategy_preserveTarget.loc[len(strategy_preserveTarget.index)] = \
                [geo_category, strategy_geo_type, first_batch_target, second_unit_target, third_unit_target, fourth_unit_target]
        
        # tag geographies
        batch1_idx = "sesit_id in ('DIS', 'HRADIS') and tra_id != 'NA'"
        batch2_idx = "sesit_id in ('DIS', 'HRADIS') and tra_id == 'NA'"
        batch3_idx = "tra_id != 'NA' and sesit_id in ('HRA', 'NA')"
        batch4_idx = "gg_id == 'GG'"

        strategy_preserveQualify.loc[strategy_preserveQualify.eval(batch1_idx), 'preserve_candidate'] = 'batch 1'
        strategy_preserveQualify.loc[strategy_preserveQualify.eval(batch2_idx) & strategy_preserveQualify['preserve_candidate'].isnull(), 'preserve_candidate'] = 'batch 2'
        strategy_preserveQualify.loc[strategy_preserveQualify.eval(batch3_idx) & strategy_preserveQualify['preserve_candidate'].isnull(), 'preserve_candidate'] = 'batch 3'
        strategy_preserveQualify.loc[strategy_preserveQualify.eval(batch4_idx) & strategy_preserveQualify['preserve_candidate'].isnull(), 'preserve_candidate'] = 'batch 4'
        

    except:
        logger.info('no housing_preservation strategy in policy.yaml for this model run')
    
    # fillna with 0 or '' (when no target for a county in a batch)
    strategy_preserveTarget.fillna(0, inplace=True)
    strategy_preserveQualify['preserve_candidate'].fillna('', inplace=True)

    logger.debug(
        'housing preserve_candidate value counts: \n{}'.format(
            strategy_preserveQualify['preserve_candidate'].value_counts(dropna=False)))

    # write out
    strategy_preserveTarget.to_csv(STRATEGY_PRESERVE_TARGET_FILE, index=False)
    strategy_preserveQualify.to_csv(STRATEGY_PRESERVE_QUALIFY_FILE, index=False)
    

    ############ update run inventory log

    logger.info('adding the new run to model run inventory')
    model_run_inventory = pd.read_csv(
        MODEL_RUN_INVENTORY_FILE,
        dtype = {'runid': int})
    logger.info('previous runs: {}'.format(model_run_inventory))

    # append the info of the new run
    if int(RUN_ID.split('run')[1]) not in model_run_inventory['runid']:
        NEW_RUN_INFO = [int(RUN_ID.split('run')[1]), RUN_SCENARIO, SCENARIO_GROUP, RUN_DESCRIPTION, LAST_RUN, MOEDL_RUN_DIR]
        logger.info('adding info of the new run: {}'.format(NEW_RUN_INFO))
        model_run_inventory.loc[len(model_run_inventory.index)] = NEW_RUN_INFO
    else:
        logger.info('run already in the inventory')

    # TODO: if a new run of the same scenario was added, update previous runs of the same scenario to 'last_run' = 'no'

    # write out the updated inventory table
    model_run_inventory.to_csv(UPDATED_MODEL_RUN_INVENTORY_FILE, index=False)
