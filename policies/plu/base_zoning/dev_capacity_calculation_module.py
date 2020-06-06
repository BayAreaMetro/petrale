USAGE = """

Calculates the development capacity (residential units, non-residential sqft) under certain version of hybrid base zoning.

"""
# Run the script by passing along the following inputs:
    # 1. folder dir of the hybrid base zoning, eg. "C:\Users\ywang\Box\Modeling and Surveys\Urban Modeling\Bay Area UrbanSim 1.5\
    #                                              PBA50\Policies\Base zoning\outputs\hybrid_base_zoning\2020_05_22_p10_plu_boc_urbansim_heuristic_10.csv"
    # 2. hybrid verion, eg. "idx_urbansim_heuristic.csv"
    # 3. folder dir for the ouput parcel-level development capacity, eg. "C:\Users\ywang\Box\Modeling and Surveys\Urban Modeling\
    #                                                                     Bay Area UrbanSim 1.5\PBA50\Policies\Base zoning\outputs\capacity"

import pandas as pd
import numpy as np
import os, argparse, time, logging


if os.getenv('USERNAME')=='ywang':
    GITHUB_PETRALE_DIR  = 'C:\\Users\\{}\\Documents\\GitHub\\petrale\\'.format(os.getenv('USERNAME'))
elif os.getenv('USERNAME')=='lzorn':
    GITHUB_PETRALE_DIR  = 'X:\\petrale'

JURIS_COUNTY_FILE = os.path.join(GITHUB_PETRALE_DIR, 'zones', 'jurisdictions', 'juris_county_id.csv')

# See Dataset_Field_Definitions_Phase1.xlsx, Build Out Capacity worksheet
# https://mtcdrive.box.com/s/efbpxbz8553e90eljvlnnq20465whyiv
ALLOWED_BUILDING_TYPE_CODES = ["HS","HT","HM","OF","HO","SC","IL","IW","IH","RS","RB","MR","MT","ME"]
RES_BUILDING_TYPE_CODES     = ["HS","HT","HM",                                        "MR"          ]
NONRES_BUILDING_TYPE_CODES  = [               "OF","HO","SC","IL","IW","IH","RS","RB","MR","MT","ME"]

INTENSITY_CODES             = ["far", "dua", "height"]

# human-readable idx values for hybrid indexing
USE_PBA40 = 0
USE_BASIS = 1

# used in calculate_capacity()
SQUARE_FEET_PER_ACRE                = 43560.0
SQUARE_FEET_PER_DU                  = 1200.0
FEET_PER_STORY                      = 11.0
PARCEL_USE_EFFICIENCY               = 0.5
SQUARE_FEET_PER_EMPLOYEE            = 350.0
SQUARE_FEET_PER_EMPLOYEE_OFFICE     = 175.0
SQUARE_FEET_PER_EMPLOYEE_INDUSTRIAL = 500.0


def get_jurisdiction_county_df():
    """
    Returns dataframe with two columns: juris_name, county_name
    juris_name is lower case, no spaces, with underscores (e.g. "unincorporated_contra_costa")
    county_name includes spaces with first letters capitalized (e.g. "Contra Costa")
    """

    # obtain jurisdiction list
    juris_df = pd.read_csv(JURIS_COUNTY_FILE, usecols = ['juris_name_full', 'county_name'])
    juris_df.rename(columns = {'juris_name_full': 'juris_name'}, inplace = True)
    return juris_df

def set_allow_dev_type(df_original,boc_source):
    """
    Assign allow residential and/or non-residential by summing the columns
    for the residential/nonresidential allowed building type codes
    Returns dataframe with 3 columns: PARCEL_ID, allow_res_[boc_source], allow_nonres_[boc_source]
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

def create_hybrid_parcel_data_from_juris_idx(logger, df_original,hybrid_idx):
    """
    Apply hybrid jurisdiction index to plu_boc parcel data
    * df_original is a parcel dataframe with pba40 and basis attributes
    * hybrid_idx is a dataframe with juris_name and _idx columns for each allowed building type or intensity attribute
      e.g. HS_idx, HT_idx, HM_idx, OF_idx, etc.... max_far_idx, max_dua_idx, etc
      Note: XX_idx is one of [ USE_PBA40, USE_BASIS ]

    Returns a dataframe with columns PARCEL_ID, juris_zmod, plus for each allowed building type or intensity attribute,
    * XX_idx: one of [ USE_PBA40, USE_BASIS ]
    * XX_urbansim: the value of XX_basis if XX_idx==USE_BASIS otherwise the value of XX_pba40

    """
    logger.info("Applying hybrid index; hybrid_idx:\n{}".format(hybrid_idx.head()))
    # logger.info("df_original.dtypes: \n{}".format(df_original.dtypes))

    # don't modify passed df
    df = df_original.copy()
    keep_cols = ['PARCEL_ID', 'juris_zmod']

    # join parcel dataframe with jurisdiction hybrid_idx on juris_zmod == juris_name
    # this brings in XX_idx
    urbansim_df = pd.merge(left    =df_original.copy(),
                           right   =hybrid_idx,
                           left_on ='juris_zmod',
                           right_on='juris_name',
                           how     = 'left')

    # bring in the allowed development type values
    for dev_type in ALLOWED_BUILDING_TYPE_CODES:
        # default to BASIS
        urbansim_df["{}_urbansim".format(dev_type)] = urbansim_df["{}_basis".format(dev_type)]
        # but set to PBA40 if the idx says to use PBA40
        urbansim_df.loc[ urbansim_df["{}_idx".format(dev_type)]==USE_PBA40, 
                         "{}_urbansim".format(dev_type) ]                   = urbansim_df["{}_pba40".format(dev_type)]
        # keep the idx and the new column
        keep_cols.append("{}_idx".format(dev_type))
        keep_cols.append("{}_urbansim".format(dev_type))

    # bring in the intensity type values
    for intensity in INTENSITY_CODES:
        # default to BASIS
        urbansim_df["max_{}_urbansim".format(intensity)] = urbansim_df["max_{}_basis".format(intensity)]
        # but set to PBA40 if the idx says to use PBA40
        urbansim_df.loc[ urbansim_df["max_{}_idx".format(intensity)]==USE_PBA40, 
                         "max_{}_urbansim".format(intensity) ]              = urbansim_df["max_{}_pba40".format(intensity)]

        # keep the idx and the new column
        keep_cols.append("max_{}_idx".format(intensity))
        keep_cols.append("max_{}_urbansim".format(intensity))

    return urbansim_df[keep_cols]


def calculate_capacity(df_original,boc_source,nodev_source,pass_thru_cols=[]):
    """
    Calculate the development capacity in res units, non-res sqft, and employee estimates

    Returns dataframe with columns:
     * PARCEL_ID
     * columns in pass_thru_cols
     * units_[boc_source]: residential units, calculated from ACRES x max_dua_[boc_source]
                           (set to zero if allow_res_[boc_source]==0 or nodev_[nodev_source]==1)
     * sqft_[boc_source] : building sqft, calculated from ACRES x max_far_[boc_source]
                           (set to zero if allow_nonres_[boc_source]==0 or nodev_[nodev_source]==1)
     * Ksqft_[boc_source]: sqft_[boc_source]/1,000
     * emp_[boc_source]  : estimate of employees from sqft_[boc_source]
    """
    
    df = df_original.copy()
    
    # DUA calculations apply to parcels 'allowRes'
    df['units_'+boc_source] = df['ACRES'] * df['max_dua_'+boc_source]   
    
    # zero out units for 'nodev' parcels or parcels that don't allow residential
    zero_unit_idx = (df['allow_res_'+boc_source] == 0) | (df['nodev_'+nodev_source] == 1)
    df.loc[zero_unit_idx,'units_'   +boc_source] = 0
        
    # FAR calculations apply to parcels 'allowNonRes'
    df['sqft_' +boc_source] = df['ACRES'] * df['max_far_'+boc_source] * SQUARE_FEET_PER_ACRE 
    
    # zero out sqft for 'nodev' parcels or parcels that don't allow non-residential
    zero_sqft_idx = (df['allow_nonres_'+boc_source] == 0) | (df['nodev_'+nodev_source] == 1)
    df.loc[zero_sqft_idx,'sqft_'       +boc_source] = 0
    
    df['Ksqft_'+boc_source] = df['sqft_'+boc_source]*0.001

    # of nonresidential uses, only office allowed
    office_idx   = (df['OF_'+boc_source] == 1) & (df['allow_nonres_'+boc_source]== 1)
    # of nonresidential uses, only industrial allowed
    allow_indust = df[['IL_'+boc_source,'IW_'+boc_source,'IH_'+boc_source]].sum(axis = 1)
    indust_idx   = (allow_indust > 0) & (df['allow_nonres_'+boc_source] == allow_indust)
    # calculate non-residential capacity in employment
    df[               'emp_'+boc_source] = df['sqft_'+boc_source] / SQUARE_FEET_PER_EMPLOYEE
    df.loc[office_idx,'emp_'+boc_source] = df['sqft_'+boc_source] / SQUARE_FEET_PER_EMPLOYEE_OFFICE
    df.loc[indust_idx,'emp_'+boc_source] = df['sqft_'+boc_source] / SQUARE_FEET_PER_EMPLOYEE_INDUSTRIAL
    
    keep_cols = ['PARCEL_ID'] + pass_thru_cols + \
    [
        "units_"        +boc_source,
        "sqft_"         +boc_source,
        "Ksqft_"        +boc_source,
        "emp_"          +boc_source
    ]
    return df[keep_cols]

def zoning_to_capacity(hybrid_zoning, hybrid_version, capacity_output_dir):

    if not os.path.exists(capacity_output_dir):
        os.makedirs(capacity_output_dir)
    output_file_name = os.path.join(capacity_output_dir, 'capacity_'+hybrid_version+'.csv')

    # Read hybrid base zoning data
    p10_plu_boc = pd.read_csv(hybrid_zoning)
    print('Read {:,} lines from {}. Head:\n{}Dtypes:\n{}'.format(len(p10_plu_boc), hybrid_zoning, p10_plu_boc.head(), p10_plu_boc.dtypes))

    print('Parcel count by county:\n{}'.format(p10_plu_boc.county_name.value_counts()))

    # convert all 

    # Calculate capacity
    capacity_pba40_allAtts    = calculate_capacity(p10_plu_boc,'pba40','zmod')
    capacity_urbansim_allAtts = calculate_capacity(p10_plu_boc,'urbansim','zmod')

    print("capacity_pba40_allAtts has {:,} rows; head:\n{}".format(len(capacity_pba40_allAtts),capacity_pba40_allAtts.head()))
    print("capacity_urbansim_allAtts has {:,} rows; head:\n{}".format(len(capacity_urbansim_allAtts),capacity_urbansim_allAtts.head()))

    # output all attributes
    capacity_allAtts = pd.merge(left=capacity_pba40_allAtts, 
                                right=capacity_urbansim_allAtts, 
                                how="inner", 
                                on=['PARCEL_ID'])

    p10_plu_boc_simply = p10_plu_boc[['PARCEL_ID','ACRES','county_id', 'county_name','juris_zmod', 'nodev_zmod'] + [
                         dev_type+'_pba40'    for dev_type in ALLOWED_BUILDING_TYPE_CODES] + [
                         dev_type+'_urbansim' for dev_type in ALLOWED_BUILDING_TYPE_CODES]]

    capacity_allAtts = capacity_allAtts.merge(p10_plu_boc_simply,
                                              on = 'PARCEL_ID', 
                                              how = 'inner')
    print("capacity has {:,} rows; head:".format(len(capacity_allAtts)))
    print(capacity_allAtts.head())

    for i in ['PARCEL_ID', 'nodev_zmod',
              'allow_res_pba40', 'allow_res_urbansim','allow_nonres_pba40','allow_nonres_urbansim'] + [
              dev_type+'_pba40'    for dev_type in ALLOWED_BUILDING_TYPE_CODES] + [
              dev_type+'_urbansim' for dev_type in ALLOWED_BUILDING_TYPE_CODES]:
        capacity_allAtts[i] = capacity_allAtts[i].fillna(-1).astype(np.int64)

    print('Export parcel-level capacity results for {:,} parcels. Head:\n{}Dtypes:\n{}'.format(len(capacity_allAtts),capacity_allAtts.head(),capacity_allAtts.dtypes))

    capacity_allAtts.to_csv(output_file_name, index = False)

    return capacity_allAtts

if __name__ == '__main__':

    """    
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

    logger.info("BOX_dir         = {}".format(BOX_dir))
    logger.info("data_output_dir = {}".format(data_output_dir))
    """


    parser = argparse.ArgumentParser(description=USAGE, formatter_class=argparse.RawDescriptionHelpFormatter,)
    parser.add_argument('hybrid_zoning', metavar="hybrid_zoning.csv",  help="Input hybrid zoning")
    parser.add_argument('hybrid_version', metavar="hybrid_version",    help="Version of input hybrid zoning")
    parser.add_argument('capacity_output', metavar="capacity_output",  help="Capacity output folder")

    args = parser.parse_args()
    print(" {:15}: {}".format('hybrid_zoning',  args.hybrid_zoning))
    print(" {:15}: {}".format('hybrid_version', args.hybrid_version))
    print(" {:15}: {}".format('capacity_output', args.capacity_output))

    zoning_to_capacity(args.hybrid_zoning, args.hybrid_version, args.capacity_output)

