#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy as np
import os
import glob
import time
import logging

NOW = time.strftime("%Y_%m%d_%H%M")
today = time.strftime('%Y_%m_%d')

if os.getenv('USERNAME')    =='ywang':
    BOX_dir                 = 'C:\\Users\\{}\\Box\\Modeling and Surveys\\Urban Modeling\\Bay Area UrbanSim 1.5\\PBA50'.format(os.getenv('USERNAME'))
    
# input file locations
hybrid_plu_boc_dir      = os.path.join(BOX_dir, 'Policies\\Base zoning\\outputs\\hybrid_base_zoning')
other_inputs_dir        = os.path.join(BOX_dir, 'Policies\\Base zoning\\inputs')

# output file location
data_output_dir         = os.path.join(BOX_dir, 'Policies\\Base zoning\\outputs\\capacity')
LOG_FILE                = os.path.join(data_output_dir,'capacity_cal_{}.log'.format(NOW))

    
ALLOWED_BUILDING_TYPE_CODES = ["HS","HT","HM","OF","HO","SC","IL","IW","IH","RS","RB","MR","MT","ME"]
RES_BUILDING_TYPE_CODES     = ["HS","HT","HM",                                        "MR"          ]
NONRES_BUILDING_TYPE_CODES  = [               "OF","HO","SC","IL","IW","IH","RS","RB","MR","MT","ME"]

# used in calculate_capacity()
SQUARE_FEET_PER_ACRE                = 43560.0
SQUARE_FEET_PER_DU                  = 1200.0
FEET_PER_STORY                      = 11.0
PARCEL_USE_EFFICIENCY               = 0.5
SQUARE_FEET_PER_EMPLOYEE            = 350.0
SQUARE_FEET_PER_EMPLOYEE_OFFICE     = 175.0
SQUARE_FEET_PER_EMPLOYEE_INDUSTRIAL = 500.0


# Precessed PLU BOC data
# four versions of hybrid zoning for BASIS; refers to different versions of the hybrid plu data

"""
versions = ['_fill_naType','_BASIS_intensity_all','_BASIS_intensity_partial','_BASIS_devType_intensity_partial','_urbansim'] 
""" 
version = '_hybrid_devTypes'


## set up a process to first determine parcel 'allow_res' and 'allow_nonres' status, and then
## calculate the development capacity in res units, non-res sqft, and employee counts 


def set_allow_dev_type(df_original,boc_source):

    """
    Assign allow residential and/or non-residential by summing the columns
    for the residential/nonresidential allowed building type codes
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


def calculate_capacity(df_original,boc_source,nodev_source):
    """
    Calculate capacity
    """
    
    df = df_original.copy()
    
    # DUA calculations apply to parcels 'allowRes' and not marked as "nodev"
    df['units_'+boc_source] = df['ACRES'] * df['max_dua_'+boc_source]   
    
    # zero out units for 'nodev' parcels or parcels that don't allow residential
    zero_unit_idx = (df['allow_res_'+boc_source] == 0) | (df['nodev_'+nodev_source] == 1)
    df.loc[zero_unit_idx,'units_'   +boc_source] = 0
        
    # FAR calculations apply to parcels 'allowNonRes' and not marked as "nodev"
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
    
    if ('source_dua_' +boc_source in df.columns) & ('source_far_'+boc_source in df.columns):
        return df[['PARCEL_ID',
                   "source_dua_"   +boc_source,
                   "allow_res_"    +boc_source,
                   "units_"        +boc_source,
                   "allow_nonres_" +boc_source,
                   "source_far_"   +boc_source,
                   "sqft_"         +boc_source,
                   "Ksqft_"        +boc_source,
                   "emp_"          +boc_source]]
    else:
        return df[['PARCEL_ID', 
                   "allow_res_"    +boc_source,
                   "units_"        +boc_source,
                   "allow_nonres_" +boc_source,
                   "sqft_"         +boc_source,
                   "Ksqft_"        +boc_source,
                   "emp_"          +boc_source]]



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

    logger.info("BOX_dir         = {}".format(BOX_dir))
    logger.info("data_output_dir = {}".format(data_output_dir))


    # Hybrid base zoning data

    p10_plu_boc = pd.read_csv(os.path.join(hybrid_plu_boc_dir, today+'_p10_plu_boc' + version + '.csv'))

    logger.info("p10_plu_boc.county_id.value_counts()") 
    logger.info(p10_plu_boc.county_id.value_counts())

    # nodev_zmod value counts
    logger.info("p10_plu_boc.nodev_zmod.value_counts()")
    logger.info(p10_plu_boc.nodev_zmod.value_counts())

    logger.info('p10_plu_boc.csv data types:')
    logger.info(p10_plu_boc.dtypes)


    # Add basis and pba40 allowed_res_ and allowed_nonres_
    # allowed_basis = set_allow_dev_type(p10_plu_boc, "basis")
    # allowed_pba40 = set_allow_dev_type(p10_plu_boc, "pba40")

    # p10_plu_boc.drop(columns = [
    #     'allow_res_basis','allow_res_pba40','allow_nonres_basis','allow_nonres_pba40'], inplace = True)


    # p10_plu_boc = pd.merge(left=p10_plu_boc,
    #                        right=allowed_basis,
    #                        how="left", on="PARCEL_ID")
    # p10_plu_boc = pd.merge(left=p10_plu_boc,
    #                        right=allowed_pba40,
    #                        how="left", on="PARCEL_ID")

    ## Calculate development capacity

    capacity_basis_allAtts    = calculate_capacity(p10_plu_boc,'basis','zmod')
    capacity_pba40_allAtts    = calculate_capacity(p10_plu_boc,'pba40','zmod')
    capacity_urbansim_allAtts = calculate_capacity(p10_plu_boc,'urbansim','zmod')

    logger.info("capacity_pba40_allAtts has {:,} rows; head:".format(len(capacity_pba40_allAtts)))
    logger.info(capacity_pba40_allAtts.head())

    logger.info("capacity_basis_allAtts has {:,} rows; head:".format(len(capacity_basis_allAtts)))
    logger.info(capacity_basis_allAtts.head())

    logger.info("capacity_urbansim_allAtts has {:,} rows; head:".format(len(capacity_basis_allAtts)))
    logger.info(capacity_urbansim_allAtts.head())

    # output all attributes

    capacity_allAtts = pd.merge(left=capacity_pba40_allAtts, 
                                right=capacity_basis_allAtts, 
                                how="inner", 
                                on=['PARCEL_ID']).merge(capacity_urbansim_allAtts,
                                                        how = 'inner',
                                                        on = ['PARCEL_ID'])

    p10_plu_boc_simply = p10_plu_boc[['PARCEL_ID','ACRES','county_id', 'county_name','juris_zmod', 'nodev_zmod'] + [
                         dev_type+'_pba40'    for dev_type in ALLOWED_BUILDING_TYPE_CODES] + [
                         dev_type+'_basis'    for dev_type in ALLOWED_BUILDING_TYPE_CODES] + [
                         dev_type+'_urbansim' for dev_type in ALLOWED_BUILDING_TYPE_CODES] + [
                         'building_types_source_basis','source_basis','plu_id_basis', 
                         'plu_jurisdiction_basis', 'plu_description_basis']]

    capacity_allAtts = capacity_allAtts.merge(p10_plu_boc_simply,
                                              on = 'PARCEL_ID', 
                                              how = 'inner')
    logger.info("capacity has {:,} rows; head:".format(len(capacity_allAtts)))
    logger.info(capacity_allAtts.head())

    for i in ['PARCEL_ID', 'nodev_zmod',
              'allow_res_pba40', 'allow_res_basis','allow_nonres_pba40','allow_nonres_basis'] + [
              dev_type+'_pba40'    for dev_type in ALLOWED_BUILDING_TYPE_CODES] + [
              dev_type+'_basis'    for dev_type in ALLOWED_BUILDING_TYPE_CODES] + [
              dev_type+'_urbansim' for dev_type in ALLOWED_BUILDING_TYPE_CODES]:
        capacity_allAtts[i] = capacity_allAtts[i].fillna(-1).astype(np.int64)

    logger.info(capacity_allAtts.dtypes)

    capacity_allAtts.to_csv(os.path.join(data_output_dir, today+'_devCapacity_allAttrs'+ version + '.csv'), index = False)

