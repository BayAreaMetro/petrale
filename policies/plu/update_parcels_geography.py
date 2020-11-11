# Notes:
# Part 1 is to update the 'parcels_geography.csv' file with the new zoningmods and nodev attributes
# Part 2 is to generate geospacial files to use in GIS. The output file dissolves parcels on 'pba50zoningmodcat', 
# and contains "parcel count" and "total acres" for each dissolved geometry. The script enables two approaches for dissolving: 
#     1) Load the 'UrbanSim_input_Zoning\outputs\parcel_zoningmods.shp' into ArcGIS and dissolve.
#     2) Dissolve in geopands and then export. 

import pandas as pd
import numpy as np
import os, glob, logging, sys, time

NOW = time.strftime("%Y_%m%d_%H%M")
today = time.strftime('%Y_%m_%d')


if os.getenv('USERNAME')=='ywang':
    M_WORKING_DIR       = 'M:\\Data\\Urban\\BAUS\\PBA50'
    BOX_DIR             = 'C:\\Users\\{}\\Box\\Modeling and Surveys\\Urban Modeling\\Bay Area UrbanSim'.format(os.getenv('USERNAME'))
    BOX_SMELT_DIR       = 'C:\\Users\\{}\\Box\\baydata\\smelt\\2020 03 12'.format(os.getenv('USERNAME'))
    GITHUB_PETRALE_DIR  = 'C:\\Users\\{}\\Documents\\GitHub\\petrale'.format(os.getenv('USERNAME'))
    M_ID_DIR            = 'M:\\Data\\GIS layers\\Blueprint Land Use Strategies\\ID_idx'

# input file locations
HORIZON_ZONING_BOX_DIR  = os.path.join(M_WORKING_DIR, 'Horizon', 'Large General Input Data')
PBA50_ZONINGMOD_DIR     = os.path.join(M_WORKING_DIR, 'Final_Blueprint', 'Zoning Modifications')
JURIS_CODE_DIR          = os.path.join(GITHUB_PETRALE_DIR, 'zones', 'jurisdictions')
M_ID_DB_DIR             = os.path.join(M_ID_DIR, 'Draft Blueprint')
M_ID_FB_DIR             = os.path.join(M_ID_DIR, 'Final Blueprint')

# outputs locations
PBA50_LARGE_INPUT_DIR   = os.path.join(BOX_DIR, 'PBA50', 'Current PBA50 Large General Input Data')
M_LARGE_INPUT_DIR       = os.path.join(M_WORKING_DIR, 'Final_Blueprint', 'Large General Input Data')
LOG_FILE                = os.path.join(M_LARGE_INPUT_DIR,'{}_update_parcels_geography.log'.format(today))


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

    logger.info("PBA50_LARGE_INPUT_DIR = {}".format(PBA50_LARGE_INPUT_DIR))


    ## Basemap parcels
    basemap_p10_file = os.path.join(BOX_SMELT_DIR, 'p10.csv')
    basemap_p10 = pd.read_csv(basemap_p10_file,
                              usecols =['PARCEL_ID','geom_id_s','ACRES','LAND_VALUE'])

    # Make sure PARCEL_ID and geom_id_s are integer:
    basemap_p10['PARCEL_ID'] = basemap_p10['PARCEL_ID'].apply(lambda x: int(round(x)))
    basemap_p10['geom_id_s'] = basemap_p10['geom_id_s'].apply(lambda x: int(round(x)))

    logger.info('Read {} records from {}, with {} unique Parcel IDs, and header: \n {}'.format(
            len(basemap_p10), 
            basemap_p10_file,
            len(basemap_p10.PARCEL_ID.unique()),
            basemap_p10.head()))
    logger.info(basemap_p10.dtypes)

    ## Read PBA40 parcels_geography file
    pg_pba40_file = os.path.join(HORIZON_ZONING_BOX_DIR, '07_11_2019_parcels_geography.csv')
    pg_pba40_cols = ['geom_id', 'pda_id', 'tpp_id', 'exp_id', 'opp_id', 'zoningmodcat', 'perffoot', 'perfarea', 'urbanized',
                     'hra_id', 'trich_id', 'cat_id', 'zoninghzcat']
    pg_pba40 = pd.read_csv(pg_pba40_file,
                           usecols = pg_pba40_cols)
    pg_pba40.rename(columns = {'pda_id': 'pda_id_pba40'}, inplace = True)

    logger.info('Read {} records from {}, with header: \n {}'.format(
            len(pg_pba40),
            pg_pba40_file,
            pg_pba40.head()))
    logger.info(pg_pba40.dtypes)

    ## Read PBA50 attributes
    pba50_attrs_file = os.path.join(PBA50_ZONINGMOD_DIR, 'p10_pba50_FBP_attr_20201110.csv')
    pba50_attrs_cols = ['geom_id_s', 'juris_id', 'juris', 'gg_id', 'tra_id', 'sesit_id', 'ppa_id', 
                        'exp2020_id', 'pba50chcat', 'exsfd_id', 'chcatwsfd', 'pba50zonin', 'nodev',
                        'fbp_gg_id', 'fbp_tra_id', 'fbp_sesit_', 'fbp_ppa_id', 'fbp_exp202', 
                        'fbpchcat', 'fbp_exsfd_', 'fbpchcatws', 'fbpzoningm']
    pba50_attrs = pd.read_csv(pba50_attrs_file,
                              usecols = pba50_attrs_cols)
    pba50_attrs.geom_id_s = pba50_attrs.geom_id_s.apply(lambda x: int(round(x)))
    pba50_attrs.rename(columns = {'pba50zonin': 'pba50zoningmodcat',

                                  'fbpzoningm': 'fbpzoningmodcat',
                                  'fbp_sesit_': 'fbp_sesit_id',
                                  'fbp_exp202': 'fbp_exp2020_id',
                                  'fbp_exsfd_': 'fbp_exsfd_id',
                                  'fbpchcatws': 'fbpchcatwsfd'}, inplace=True)

    logger.info('Read {} records from {}, with header: \n {}'.format(
            len(pba50_attrs),
            pba50_attrs_file,
            pba50_attrs.head()))
    logger.info(pba50_attrs.dtypes)

    ## Read new PBA50 PDA IDs
    pda_pba50_db_file = os.path.join(M_ID_DB_DIR, 'pda_id_2020.csv')
    pda_pba50_db = pd.read_csv(pda_pba50_db_file)
    pda_pba50_db.rename(columns = {'pda_id': 'pda_id_pba50_db'}, inplace = True)

    logger.info('Read {} records from {}, with {} unique Parcel IDs, header: \n {}'.format(
            len(pda_pba50_db),
            pda_pba50_db_file,
            len(pda_pba50_db.parcel_id.unique()),
            pda_pba50_db.head()))
    logger.info(pda_pba50_db.dtypes)

    pda_pba50_fb_file = os.path.join(M_ID_FB_DIR, 'pda_id_2020.csv')
    pda_pba50_fb = pd.read_csv(pda_pba50_fb_file)
    pda_pba50_fb.rename(columns = {'pda_id': 'pda_id_pba50_fb'}, inplace = True)

    logger.info('Read {} records from {}, with {} unique Parcel IDs, header: \n {}'.format(
            len(pda_pba50_fb),
            pda_pba50_fb_file,
            len(pda_pba50_fb.parcel_id.unique()),
            pda_pba50_fb.head()))
    logger.info(pda_pba50_fb.dtypes)

    ## Read jurisdiction code file
    juris_code_file = os.path.join(JURIS_CODE_DIR, 'juris_county_id.csv')
    juris_code = pd.read_csv(juris_code_file, usecols = ['jurisdiction_id','juris_id','juris_name_full'])


    ## Join pab50 attributes to pba40 parcel set
    pg_pba50_merge = pg_pba40.merge(pba50_attrs, 
                                    left_on = 'geom_id', 
                                    right_on = 'geom_id_s', 
                                    how = 'left').merge(juris_code, 
                                                        on = 'juris_id', 
                                                        how = 'left').merge(basemap_p10, 
                                                                            on = 'geom_id_s',
                                                                            how = 'left').merge(pda_pba50_db,
                                                                                                left_on = 'PARCEL_ID',
                                                                                                right_on = 'parcel_id',
                                                                                                how = 'left').merge(pda_pba50_fb,
                                                                                                                    left_on = 'PARCEL_ID',
                                                                                                                    right_on = 'parcel_id',
                                                                                                                    how = 'left')                    
    ## additional updates on 'nodev'
    nodev_folder = os.path.join(PBA50_ZONINGMOD_DIR,'*.csv')

    for filename in list(glob.glob(nodev_folder)):
        if 'noDev_parcels_' in filename:
            logger.info('Update nodev based on {}'.format(filename))

            nodev_parcel = pd.read_csv(filename)
            nodev_parcel.drop_duplicates(inplace=True)
            nodev_parcel.rename(columns = {'nodev': 'nodev_update'}, inplace=True)          

            if 'PARCEL_ID' in nodev_parcel:
                logger.info('update {} parcels using PARCEL_ID'.format(len(nodev_parcel)))
                nodev_parcel.PARCEL_ID = nodev_parcel.PARCEL_ID.apply(lambda x: int(round(x)))
                pg_pba50_merge = pg_pba50_merge.merge(nodev_parcel[['PARCEL_ID','nodev_update']],
                                                      on='PARCEL_ID',
                                                      how='left')
                pg_pba50_merge.loc[pg_pba50_merge.nodev_update.notnull(), 'nodev'] = \
                    pg_pba50_merge.loc[pg_pba50_merge.nodev_update.notnull(), 'nodev_update']
                pg_pba50_merge.drop(columns=['nodev_update'], inplace=True)

            elif 'geom_id' in nodev_parcel:
                logger.info('update {} parcels using geom_id'.format(len(nodev_parcel)))
                nodev_parcel.geom_id = nodev_parcel.geom_id.apply(lambda x: int(round(x)))
                pg_pba50_merge = pg_pba50_merge.merge(nodev_parcel[['geom_id','nodev_update']],
                                                      on='geom_id',
                                                      how='left')
                pg_pba50_merge.loc[pg_pba50_merge.nodev_update.notnull(), 'nodev'] = \
                    pg_pba50_merge.loc[pg_pba50_merge.nodev_update.notnull(), 'nodev_update']
                pg_pba50_merge.drop(columns=['nodev_update'], inplace=True)

            else:
                logger.info('Missing PARCEL_ID and geom_id, cannot update.')


    ## export needed fields

    # Parcel attribute:
    p_att = ['PARCEL_ID', 'geom_id', 'jurisdiction_id', 'juris_name_full', 'juris_id', 'juris','ACRES']

    # PBA40 fields:
    pba40_att = ['pda_id_pba40', 'tpp_id', 'exp_id', 'opp_id', 
                 'zoningmodcat', 'perffoot', 'perfarea', 'urbanized']

    # Horizon fields:
    hor_att = ['hra_id', 'trich_id', 'cat_id', 'zoninghzcat']

    # PBA50 Draft Blueprint fields:
    pba50_db_att = ['gg_id', 'pda_id_pba50_db', 'tra_id', 'sesit_id', 'ppa_id', 
                    'exp2020_id', 'exsfd_id', 'pba50zoningmodcat', 'pba50chcat']

    # PBA50 Final Blueprint fields:
    pba50_fb_att = ['fbp_gg_id', 'pda_id_pba50_fb', 'fbp_tra_id', 'fbp_sesit_id', 'fbp_ppa_id', 
                    'fbp_exp2020_id', 'fbp_exsfd_id', 'fbpzoningmodcat', 'fbpchcat']

    # PBA50 shared fields:
    pba50_att_both = ['nodev']

    # export:
    pg_all = pg_pba50_merge[p_att + pba40_att + hor_att + pba50_db_att + pba50_fb_att + pba50_att_both]
    pg_pba50_fb_only = pg_pba50_merge[p_att + pba50_fb_att + pba50_att_both]

    logger.info('Export {} records with {} unique PARCEL IDs to {} with the following fields: \n {}'.format(len(pg_all),
                                                                                                            len(pg_all.PARCEL_ID.unique()),
                                                                                                            PBA50_LARGE_INPUT_DIR,
                                                                                                            pg_all.dtypes))
    pg_all.to_csv(os.path.join(PBA50_LARGE_INPUT_DIR, today+'_parcels_geography.csv'), index = False)
    #pg_pba50_fb_only.to_csv(os.path.join(M_LARGE_INPUT_DIR, today+'_parcels_geography_fb_only.csv'), index = False)
    