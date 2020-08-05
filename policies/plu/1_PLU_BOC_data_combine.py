import pandas as pd
import numpy as np
import os, glob, logging, sys, time

import dev_capacity_calculation_module

NOW = time.strftime("%Y_%m%d_%H%M")
today = time.strftime('%Y_%m_%d')


## set up the directories

if os.getenv('USERNAME')    =='ywang':
    BOX_DIR                 = 'C:\\Users\\{}\\Box\\Modeling and Surveys\\Urban Modeling\\Bay Area UrbanSim\\PBA50'.format(os.getenv('USERNAME'))
    M_URBANSIM_DIR          = 'M:\\Data\\Urban\\BAUS\\PBA50'
    M_SMELT_DIR             = 'M:\\Data\\GIS layers\\UrbanSim smelt\\2020 03 12'
    GITHUB_PETRALE_DIR      = 'C:\\Users\\{}\\Documents\\GitHub\\petrale'.format(os.getenv('USERNAME'))
    GITHUB_URBANSIM_DIR     = 'C:\\Users\\{}\\Documents\\GitHub\\bayarea_urbansim\\data'.format(os.getenv('USERNAME'))

elif os.getenv('USERNAME')  =='lzorn':
    BOX_DIR                 = 'C:\\Users\\{}\\Box\\Modeling and Surveys\\Urban Modeling\\Bay Area UrbanSim\\PBA50'.format(os.getenv('USERNAME'))
    M_URBANSIM_DIR          = 'M:\\Data\\Urban\\BAUS\\PBA50'
    M_SMELT_DIR             = 'M:\\Data\\GIS layers\\UrbanSim smelt\\2020 03 12'
    GITHUB_PETRALE_DIR      = 'X:\\petrale'
    GITHUB_URBANSIM_DIR     = 'X:\\bayarea_urbansim\\data'

# input file locations
PBA40_ZONING_BOX_DIR        = os.path.join(M_URBANSIM_DIR, 'Horizon', 'Large General Input Data')
PBA50_ZONINGMOD_DIR         = os.path.join(M_URBANSIM_DIR, 'Draft_Blueprint', 'Zoning Modifications')
OTHER_INPUTS_DIR            = os.path.join(M_URBANSIM_DIR, 'Draft_Blueprint', 'Base zoning', 'input')
    
# output file location
DATA_OUTPUT_DIR             = os.path.join(BOX_DIR, 'Policies\\Base zoning\\outputs')
QA_QC_DIR                   = os.path.join(BOX_DIR, 'Policies\\Base zoning\\outputs\\QAQC')
LOG_FILE                    = os.path.join(DATA_OUTPUT_DIR,'{}_plu_boc_combine.log'.format(today))


## Three steps of data clearing - combine PBA40 plu data and BASIS BOC data using p10 parcel geography
                             ## - assign allow residential and/or non-residential development to each parcel;
                             ## - impute max_dua and max_far for parcels missing the info


def impute_max_dua(df_original,boc_source):
    """
    Impute max_dua from max_far or max_height
    Returns dataframe with PARCEL_ID, max_dua, source_dua_[boc_source] 
      source_dua is one of: [boc_source]: if it's already set so no imputation is necessary
                            imputed from max_far
                            imputed from max_height
                            missing: if it can't be imputed because max_far and max_height are missing too
    Note: For parcels that are nodev or residential development isn't allowed, max_dua isn't important
    """

    # don't modify passed df
    df = df_original.copy()

    print("impute_max_dua{}: Before imputation, number of parcels with missing max_dua_{}: {:,}".format(
        boc_source, boc_source, sum(df['max_dua_'+boc_source].isnull())))

    # we can only fill in missing if either max_far or max_height is not null   
    max_dua_from_far    = df['max_far_'    +boc_source] * dev_capacity_calculation_module.SQUARE_FEET_PER_ACRE / dev_capacity_calculation_module.SQUARE_FEET_PER_DU
    max_far_from_height = df['max_height_' +boc_source] / dev_capacity_calculation_module.FEET_PER_STORY * dev_capacity_calculation_module.PARCEL_USE_EFFICIENCY
    max_dua_from_height = max_far_from_height * dev_capacity_calculation_module.SQUARE_FEET_PER_ACRE / dev_capacity_calculation_module.SQUARE_FEET_PER_DU
    
    # default to missing
    df['source_dua_'+boc_source] = 'missing'
    
    # this is set already -- nothing to do
    df.loc[(df['max_dua_'+boc_source].notnull()) & 
           (df['max_dua_'+boc_source] > 0), 'source_dua_'+boc_source] = boc_source

    # decide on imputation source
    # for missing values, fill from max_far or max_height -- if both are available, use the min unless the min is 0
    df.loc[(df['source_dua_'+boc_source]=='missing') & 
            max_dua_from_height.notnull() & 
            max_dua_from_far.notnull() &
           (max_dua_from_height > max_dua_from_far) &
           (max_dua_from_far > 0), "source_dua_"+boc_source] = 'imputed from max_far (as min)'

    df.loc[(df['source_dua_'+boc_source]=='missing') & 
            max_dua_from_height.notnull() & 
            max_dua_from_far.notnull() &
           (max_dua_from_height > max_dua_from_far) &
           (max_dua_from_far == 0), "source_dua_"+boc_source] = 'imputed from max_height'

    df.loc[(df['source_dua_'+boc_source]=='missing') & 
            max_dua_from_height.notnull() & 
            max_dua_from_far.notnull() &
           (max_dua_from_height < max_dua_from_far) & 
           (max_dua_from_height > 0), 'source_dua_'+boc_source] = 'imputed from max_height (as min)'

    df.loc[(df['source_dua_'+boc_source]=='missing') & 
            max_dua_from_height.notnull() & 
            max_dua_from_far.notnull() &
           (max_dua_from_height < max_dua_from_far) & 
           (max_dua_from_height == 0), 'source_dua_'+boc_source] = 'imputed from max_far'


    # if only one available use that
    df.loc[(df['source_dua_'+boc_source]=="missing") & 
           (max_dua_from_height.isnull() | (max_dua_from_height == 0)) & 
            max_dua_from_far.notnull(), 'source_dua_'+boc_source] = 'imputed from max_far'

    df.loc[(df['source_dua_'+boc_source]=='missing') & 
            max_dua_from_height.notnull() & 
            (max_dua_from_far.isnull() | (max_dua_from_far == 0)), 'source_dua_'+boc_source] = 'imputed from max_height'

    # imputation is decided -- set it
    df.loc[df['source_dua_'+boc_source]=='imputed from max_height (as min)', 'max_dua_'+boc_source] = max_dua_from_height
    df.loc[df['source_dua_'+boc_source]=='imputed from max_height',          'max_dua_'+boc_source] = max_dua_from_height
    df.loc[df['source_dua_'+boc_source]=='imputed from max_far (as min)',    'max_dua_'+boc_source] = max_dua_from_far
    df.loc[df['source_dua_'+boc_source]=='imputed from max_far',             'max_dua_'+boc_source] = max_dua_from_far

    logger.info("impute_max_dua(): After imputation: ")
    logger.info(df['source_dua_'+boc_source].value_counts())

    return df[['PARCEL_ID','max_dua_'+boc_source,'source_dua_'+boc_source]]
    


def impute_max_far(df_original,boc_source):
    """
    Impute max_far from max_height
    Returns dataframe with PARCEL_ID, max_far, source_far_[boc_source] 
        source_far is one of: [boc_source]: if it's already set so no imputation is necessary
                              imputed from max_height
                              missing: if it can't be imputed because max_far and max_height are missing too

    Note: For parcels that are nodev or nonresidential development isn't allowed, max_far isn't important
    """

    # don't modify passed df
    df = df_original.copy()

    logger.info("impute_max_far{}: Before imputation, number of parcels with missing max_far_{}: {:,}".format(
        boc_source, boc_source, sum(df['max_far_'+boc_source].isnull())))
    
    # we can only fill in missing if max_height is not null
    max_far_from_height = df['max_height_' +boc_source] / dev_capacity_calculation_module.FEET_PER_STORY * dev_capacity_calculation_module.PARCEL_USE_EFFICIENCY
    
    # default to missing
    df['source_far_'+boc_source] = 'missing'
    
    # this is set already -- nothing to do
    df.loc[(df['max_far_'+boc_source].notnull()) & 
           (df['max_far_'+boc_source] > 0), 'source_far_'+boc_source] = boc_source

    # decide on imputation source
    # for missing values, fill from max_height
    df.loc[(df['source_far_'+boc_source]=='missing') & max_far_from_height.notnull(),
           'source_far_'+boc_source] = 'imputed from max_height'

    # imputation is decided -- set it
    df.loc[df['source_far_'+boc_source]=='imputed from max_height', 'max_far_'+boc_source] = max_far_from_height

    logger.info("impute_max_far_{}: After imputation: ".format(boc_source))
    logger.info(df['source_far_'+boc_source].value_counts())

    return df[['PARCEL_ID','max_far_'+boc_source,'source_far_'+boc_source]]


def impute_basis_devtypes_from_pba40(df):
    """
    Where basis allowed development type is missing AND nodev_zmod == 0,
    impute value from pba40.  Note this in source_[btype]_basis, which will be set to one of 
        ['basis', 'missing', 'imputed from pba40']

    Returns df with [btype]_basis and source_[btype]_basis columns updated
    """
    logger.info("impute_basis_devtypes_from_pba40():")

    for btype in dev_capacity_calculation_module.ALLOWED_BUILDING_TYPE_CODES:
        df['source_'+btype+'_basis'] = 'basis' # default
        df.loc[ df[btype+'_basis'].isnull(), 'source_'+btype+'_basis'] = 'missing' # or missing if null

        logger.info("Before imputation of {}_basis:\n{}".format(btype, df['source_'+btype+'_basis'].value_counts()))
        # if basis value is missing
        #    and we care about it (nodev_zod == 0)
        #    and the pba40 value is present
        # => impute
        impute_idx = ((df[btype+'_basis'].isnull()) & \
                      (df['nodev_zmod'] == 0) & \
                      (df[btype+'_pba40'].notnull()))
        # impute and note source
        df.loc[ impute_idx,           btype+'_basis' ] = df[btype + '_pba40']
        df.loc[ impute_idx, 'source_'+btype+'_basis' ] = 'imputed from pba40'

        logger.info("After imputation of {}_basis:\n{}".format(btype, df['source_'+btype+'_basis'].value_counts()))

    logger.info("")
    return df

def impute_basis_max_height_from_pba40(df):
    """
    Where max_height_basis is missing AND nodev_zmod == 0,
    impute value from pba40.  Note this in source_height_basis, which will be set to one of 
        ['basis', 'missing', 'imputed from pba40']

    Returns df with max_height_basis and source_height_basis columns updated
    """
    logger.info("impute_basis_max_height_from_pba40():")

    df['source_height_basis'] = 'basis' # default
    df.loc[ df['max_height_basis'].isnull(), 'source_height_basis'] = 'missing' # or missing if null

    logger.info("Before imputation of max_height_basis:\n{}".format(df['source_height_basis'].value_counts()))
    # if basis value is missing
    #    and we care about it (nodev_zod == 0)
    #    and the pba40 value is present
    # => impute
    impute_idx = ((df['max_height_basis'].isnull()) & \
                  (df['nodev_zmod'] == 0) & \
                  (df['max_height_pba40'].notnull()))
    # impute and note source
    df.loc[ impute_idx,    'max_height_basis' ] = df['max_height_pba40']
    df.loc[ impute_idx, 'source_height_basis' ] = 'imputed from pba40'

    logger.info("After imputation of max_height_basis:\n{}".format(df['source_height_basis'].value_counts()))
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


    ## Basemap parcels
    basemap_p10_file = os.path.join(BOX_SMELT_DIR, 'p10.csv')
    basemap_p10 = pd.read_csv(basemap_p10_file,
                              usecols =['PARCEL_ID','geom_id_s','ACRES','LAND_VALUE'],
                              dtype   ={'PARCEL_ID':np.float64, 'geom_id_s':str, 'ACRES':np.float64, 'LAND_VALUE':np.float64})
    # conver PARCEL_ID to integer:
    basemap_p10['PARCEL_ID'] = basemap_p10['PARCEL_ID'].apply(lambda x: int(round(x)))
    logger.info("Read {:,} rows from {}".format(len(basemap_p10), basemap_p10_file))
    logger.info("\n{}".format(basemap_p10.head()))
    logger.info('Number of unique PARCEL_ID: {}'.format(len(basemap_p10.PARCEL_ID.unique())))


    ## p10 pacel to pba40 zoning code mapping
    pba40_pz_file = os.path.join(PBA40_ZONING_BOX_DIR, '2015_12_21_zoning_parcels.csv')
    pba40_pz = pd.read_csv(
        pba40_pz_file,
        usecols = ['geom_id','zoning_id','nodev'],
        dtype = {'geom_id':str, 'zoning_id':np.float64, 'nodev_pba40':np.int})

    logger.info("Read {:,} rows from {}".format(len(pba40_pz), pba40_pz_file))
    logger.info("\n{}".format(pba40_pz.head()))

    ## add zoning_id, nodev_pba40 columns to p10
    p10_pba40_pz = pd.merge(left=basemap_p10, right=pba40_pz, left_on='geom_id_s', right_on = 'geom_id', how='left')
    p10_pba40_pz.rename(columns={'nodev'    :'nodev_pba40',
                                 'zoning_id':'zoning_id_pba40'}, inplace=True)
    #display(p10_pba40_pz.head())

    ## Check Number of parcels missing zoning designation
    p10_pba40_pz_missing = p10_pba40_pz.loc[p10_pba40_pz['zoning_id_pba40'].isnull()]
    logger.info("Out of {0:,} p10 parcels, {1:,} or {2:.1f}% are missing 'zoning_id' values".format(
                len(p10_pba40_pz), len(p10_pba40_pz_missing), 100.0*len(p10_pba40_pz_missing)/len(p10_pba40_pz)))


    ## P10 parcels with PBA40 zoning code PLU

    pba40_plu_file = os.path.join(GITHUB_URBANSIM_DIR, 'zoning_lookup.csv')
    pba40_plu = pd.read_csv(pba40_plu_file, dtype={'id':float})
    logger.info("Read {:,} rows from {}".format(len(pba40_plu), pba40_plu_file))
    # coerce this column to float -- it's a string for some reason
    pba40_plu['SC'] = pd.to_numeric(pba40_plu['SC'], errors='coerce')

    # append _pba40 to column names
    rename_cols = dict((col,col+"_pba40") for col in pba40_plu.columns.values)
    pba40_plu.rename(columns=rename_cols, inplace=True)
    logger.info("\n{}".format(pba40_plu.head()))

    # check duplicates in zoning id
    pba40_plu['jz_o'] = pba40_plu['city_pba40'].str.cat(pba40_plu['name_pba40'],sep=" ")
    logger.info("Out of {:,} rows in pba40_plu, {:,} have unique values of 'id', {:,} have unique values of 'jz_o'".format(
                len(pba40_plu), len(pba40_plu.id_pba40.unique()), len(pba40_plu.jz_o.unique())))

    # using the zoning_id, get the pba40 zoning data (intensities, allowed building types)
    p10_pba40_plu = pd.merge(left=p10_pba40_pz, 
                             right=pba40_plu, 
                             left_on='zoning_id_pba40', 
                             right_on='id_pba40', 
                             how='left')

    # Check number of p10 records failed to find a matching PLU
    p10_pba40_plu_missing = p10_pba40_plu.loc[p10_pba40_plu['jz_o'].isnull()]
    logger.info("Out of {0:,} rows in p10_pba40_plu, {1:,} or {2:.1f}% are missing 'jz_o' values".format(
                 len(p10_pba40_plu), len(p10_pba40_plu_missing), 100.0*len(p10_pba40_plu_missing)/len(p10_pba40_plu)))

    logger.info("\n{}".format(p10_pba40_plu.head()))


    ## P10 with BASIS BOC

    ## Read BASIS BOC
    basis_boc_file = os.path.join(OTHER_INPUTS_DIR,'p10_urbansim_boc_opt_b_v2.csv')
    basis_boc_columns = [
        'parcel_id','max_height','max_dua','max_far',
        'plu_code','plu_id','plu_jurisdiction','plu_description',
        'building_types_source','source'] + [btype.lower() for btype in dev_capacity_calculation_module.ALLOWED_BUILDING_TYPE_CODES]
    # most are float
    basis_boc_dtypes = dict((x, float) for x in basis_boc_columns)
    # except these
    basis_boc_dtypes['plu_code'             ] = str
    basis_boc_dtypes['plu_id'               ] = str
    basis_boc_dtypes['plu_jurisdiction'     ] = str
    basis_boc_dtypes['plu_description'      ] = str
    basis_boc_dtypes['building_types_source'] = str
    basis_boc_dtypes['source'               ] = str

    basis_boc = pd.read_csv(basis_boc_file, usecols = basis_boc_columns, dtype = basis_boc_dtypes)
    logger.info("Read {:,} rows from {}".format(len(basis_boc), basis_boc_file))

    # drop records with no parcel_id
    basis_boc = basis_boc.loc[basis_boc.parcel_id.notnull()]

    # convert parcel_id to integer
    basis_boc['parcel_id'] = basis_boc['parcel_id'].apply(lambda x: int(round(x)))

    logger.info('After dropping nan parcel_id, BASIS BOC has {} parcels, {} unique parcel_id'.format(len(basis_boc),len(basis_boc.parcel_id.unique())))

    # append _basis to column names to differentiate between basis PLU and pba40 PLU between 
    rename_cols = {}
    for col in basis_boc.columns.values:
        # rename the ht, hm, etc to HT_basis, HM_basis, ...
        if len(col)==2:
            rename_cols[col] = col.upper() + "_basis"
        else:
            rename_cols[col] = col + "_basis"
    basis_boc.rename(columns=rename_cols, inplace=True)

    # drop duplicates of parcel_id; this should be unique
    logger.info("\n{}".format(basis_boc.head()))
    basis_boc_rows = len(basis_boc)
    basis_boc.drop_duplicates(subset='parcel_id_basis', inplace=True)
    if len(basis_boc) == basis_boc_rows:
        logger.info("No duplicate parcel_ids found in {}".format(basis_boc_file))
    else:
        logger.warning("Dropped duplicate parcel_id rows from {}".format(basis_boc_file))
        logger.warning("Went from {:,} to {:,} rows; dropped {:,} duplicates".format(basis_boc_rows, len(basis_boc), basis_boc_rows-len(basis_boc)))

    # report on missing allowed building types
    for btype in dev_capacity_calculation_module.ALLOWED_BUILDING_TYPE_CODES:
        null_btype_count = len(basis_boc.loc[basis_boc["{}_basis".format(btype)].isnull()])
        logger.info('Number of parcels missing allowable type for {}: {:,} or {:.1f}%'.format(btype,
                     null_btype_count, 100.0*null_btype_count/len(basis_boc)))

    # merge basis plu to p10 + pba40 plu
    p10_basis_pba40_boc = pd.merge(left=p10_pba40_plu, right=basis_boc, left_on='PARCEL_ID', right_on='parcel_id_basis', how='left')

    p10_basis_pba40_boc.drop(columns = ['id_pba40','plandate_pba40','jz_o'],inplace = True)
    logger.info('Create p10_basis_pba40_boc:')
    logger.info(p10_basis_pba40_boc.dtypes)


    ## Bring in zoning scenarios data

    zmod_file = os.path.join(PBA50_ZONINGMOD_DIR,'p10_pba50_attr_20200416.csv')
    zmod = pd.read_csv(zmod_file,
                       usecols = ['PARCEL_ID','juris','pba50zoningmodcat','nodev'])
    zmod['PARCEL_ID'] = zmod['PARCEL_ID'].apply(lambda x: int(round(x)))
    logger.info("Read {:,} rows from {}".format(len(zmod), zmod_file))
    logger.info("\n{}".format(zmod.head()))
    logger.info('Number of unique parcel_id: {}'.format(len(zmod.PARCEL_ID.unique())))

    # append _zmod to column names to clarify source of these columns
    rename_cols = dict((col, col+"_zmod") for col in zmod.columns.values)
    zmod.rename(columns=rename_cols, inplace=True)

    # merge parcel data with zoning mods
    p10_basis_pba40_boc_zmod       = pd.merge(left=p10_basis_pba40_boc, right=zmod, 
                                                  left_on='PARCEL_ID', right_on='PARCEL_ID_zmod', how = 'left')
    logger.info("Created p10_b10_basis_pba40_boc_zmod:")
    logger.info(p10_basis_pba40_boc_zmod.dtypes)


    ## Bring in jurisdiction_county lookup data
    juris_county_lookup_file = os.path.join(GITHUB_PETRALE_DIR,'zones\\jurisdictions\\juris_county_id.csv')
    juris_county_lookup = pd.read_csv(
        juris_county_lookup_file,
        usecols = ['juris_name_full','juris_id','county_name', 'county_id','jurisdiction_id'])

    p10_basis_pba40_boc_zmod_withJuris = p10_basis_pba40_boc_zmod.merge(juris_county_lookup,
                                                                       left_on = 'juris_zmod',right_on='juris_name_full',how='left')

    p10_basis_pba40_boc_zmod_withJuris.drop(columns = ['juris_name_full'],inplace = True)

    logger.info('Add jurisdiction names and IDs: ')
    logger.info("\n{}".format(p10_basis_pba40_boc_zmod_withJuris.head()))


    ## Add basis and pba40 allowed_res_ and allowed_nonres_
    allowed_basis = dev_capacity_calculation_module.set_allow_dev_type(p10_basis_pba40_boc_zmod_withJuris, "basis")
    allowed_pba40 = dev_capacity_calculation_module.set_allow_dev_type(p10_basis_pba40_boc_zmod_withJuris, "pba40")

    p10_basis_pba40_boc_zmod_withJuris = pd.merge(left=p10_basis_pba40_boc_zmod_withJuris,
                                                  right=allowed_basis,
                                                  how="left", on="PARCEL_ID")
    p10_basis_pba40_boc_zmod_withJuris = pd.merge(left=p10_basis_pba40_boc_zmod_withJuris,
                                                  right=allowed_pba40,
                                                  how="left", on="PARCEL_ID")
    #p10_basis_pba40_boc_zmod_withJuris

    logger.info('Add basis and pba40 allowed_res_ and allowed_nonres_:')
    logger.info(p10_basis_pba40_boc_zmod_withJuris.head())

    # as the function suggests -- impute basis allowed development types from pba40
    p10_basis_pba40_boc_zmod_withJuris = impute_basis_devtypes_from_pba40(p10_basis_pba40_boc_zmod_withJuris)
    # and impute basis max height from pba40 - do this before max_dua/max_far since it's used for that
    p10_basis_pba40_boc_zmod_withJuris = impute_basis_max_height_from_pba40(p10_basis_pba40_boc_zmod_withJuris)

    ## Impute max_dua and max_far
    dua_basis = impute_max_dua(p10_basis_pba40_boc_zmod_withJuris, "basis")
    dua_pba40 = impute_max_dua(p10_basis_pba40_boc_zmod_withJuris, "pba40")

    far_basis = impute_max_far(p10_basis_pba40_boc_zmod_withJuris, "basis")
    far_pba40 = impute_max_far(p10_basis_pba40_boc_zmod_withJuris, "pba40")

    ## replace the columns with those with imputations
    logger.info('Parcels count: {:,}'.format(len(p10_basis_pba40_boc_zmod_withJuris)))
    p10_basis_pba40_boc_zmod_withJuris.drop(columns=['max_dua_basis','max_dua_pba40','max_far_basis','max_far_pba40'], inplace=True)

    p10_basis_pba40_boc_zmod_withJuris = pd.merge(left=p10_basis_pba40_boc_zmod_withJuris,
                                                  right=dua_basis,
                                                  how="left", on="PARCEL_ID")
    p10_basis_pba40_boc_zmod_withJuris = pd.merge(left=p10_basis_pba40_boc_zmod_withJuris,
                                                  right=dua_pba40,
                                                  how="left", on="PARCEL_ID")
    p10_basis_pba40_boc_zmod_withJuris = pd.merge(left=p10_basis_pba40_boc_zmod_withJuris,
                                                  right=far_basis,
                                                  how="left", on="PARCEL_ID")
    p10_basis_pba40_boc_zmod_withJuris = pd.merge(left=p10_basis_pba40_boc_zmod_withJuris,
                                                  right=far_pba40,
                                                  how="left", on="PARCEL_ID")

    ## Export PLU BOC data to csv

    output_columns = [
        'PARCEL_ID', 'geom_id','county_id', 'county_name', 'juris_zmod', 'jurisdiction_id',

        'ACRES', 'zoning_id_pba40', 'name_pba40','plu_code_basis','pba50zoningmodcat_zmod',
        
        # intensity
        'max_far_basis',        'max_far_pba40',
        'source_far_basis',     'source_far_pba40',
        'max_dua_basis',        'max_dua_pba40',
        'source_dua_basis',     'source_dua_pba40',
        'max_height_basis',     'max_height_pba40',
        'source_height_basis',

        'nodev_zmod',           'nodev_pba40',

        # allow building types sum
        'allow_res_basis',      'allow_res_pba40',
        'allow_nonres_basis',   'allow_nonres_pba40',

        # BASIS metadata
        'building_types_source_basis','source_basis',
        'plu_id_basis','plu_jurisdiction_basis','plu_description_basis'
    ]
    # allowed building types
    for btype in dev_capacity_calculation_module.ALLOWED_BUILDING_TYPE_CODES:
        output_columns.append(btype + "_basis")
        output_columns.append(btype + "_pba40")
        # basis btypes may be imputed, recorded here
        output_columns.append("source_" + btype + "_basis")

    plu_boc_output = p10_basis_pba40_boc_zmod_withJuris[output_columns]

    for devType in dev_capacity_calculation_module.ALLOWED_BUILDING_TYPE_CODES:
        logger.info('Missing BASIS {} parcel count: {}'.format(devType,len(plu_boc_output.loc[plu_boc_output[devType+'_basis'].isnull()])))

    logger.info('Export pba40/BASIS combined base zoning data: {} records of the following fields: {}'.format(len(plu_boc_output), plu_boc_output.dtypes))

    plu_boc_output.to_csv(os.path.join(DATA_OUTPUT_DIR, today+'_p10_plu_boc_allAttrs.csv'), index = False)

    
    ## Evaluate development type for QA/QC
    plu_boc = plu_boc_output.copy()

    for devType in dev_capacity_calculation_module.ALLOWED_BUILDING_TYPE_CODES:
        plu_boc[devType+'_comp'] = np.nan

        plu_boc.loc[(plu_boc[devType + '_pba40'] == 1) & 
                    (plu_boc[devType + '_basis'] == 0),devType+'_comp'] = 'only PBA40 allow'
        plu_boc.loc[(plu_boc[devType + '_pba40'] == 0) & 
                    (plu_boc[devType + '_basis'] == 1),devType+'_comp'] = 'only BASIS allow'
        plu_boc.loc[(plu_boc[devType + '_pba40'] == 1) & 
                    (plu_boc[devType + '_basis'] == 1),devType+'_comp'] = 'both allow'
        plu_boc.loc[(plu_boc[devType + '_pba40'] == 0) & 
                    (plu_boc[devType + '_basis'] == 0),devType+'_comp'] = 'both not allow'
        plu_boc.loc[(plu_boc[devType + '_basis'].isnull()) & 
                    (plu_boc[devType + '_pba40'].notnull()),devType+'_comp'] = 'missing BASIS data' 
        plu_boc.loc[plu_boc[devType + '_pba40' ].isnull(),devType+'_comp'] = 'missing PBA40 data'    
        plu_boc.loc[plu_boc['nodev_zmod'       ] == 1,devType+'_comp'] = 'not developable'
                
    devType_comp = plu_boc[['PARCEL_ID','county_id','county_name','juris_zmod', 'ACRES',
                            'nodev_zmod','nodev_pba40'] + 
                           [devType+'_comp' for devType in dev_capacity_calculation_module.ALLOWED_BUILDING_TYPE_CODES]]

    devType_comp.to_csv(os.path.join(QA_QC_DIR, today+'_devType_comparison.csv'),index = False)


    ## Check PBA40 zoning_id / BASIS plu_id completeness  
    logger.info('Export parcels that have a zoning_id_pba40 but no plu_id_basis')
    missing_plu_id_basis = plu_boc_output.loc[(plu_boc_output['plu_id_basis'].isnull()) & 
                                              (plu_boc_output['zoning_id_pba40'].notnull())][['PARCEL_ID','juris_zmod','zoning_id_pba40',
                                                                                              'plu_id_basis', 'plu_description_basis']]
    missing_plu_id_basis.to_csv(os.path.join(QA_QC_DIR, today+'_missing_plu_id_basis.csv'),index = False)                                                                                         


    logger.info('Export parcels that have a plu_id_basis but no zoning_id_pba40')
    missing_zoning_id_pba40 = plu_boc_output.loc[(plu_boc_output['zoning_id_pba40'].isnull()) & 
                                                 (plu_boc_output['plu_id_basis'].notnull())][['PARCEL_ID','juris_zmod','zoning_id_pba40',
                                                                                              'plu_id_basis', 'plu_description_basis']]
    missing_zoning_id_pba40.to_csv(os.path.join(QA_QC_DIR, today+'_missing_zoning_id_pba40.csv'),index = False)
