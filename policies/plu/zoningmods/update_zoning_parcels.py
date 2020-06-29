USAGE = """

  python update_zoning_parcels.py

  Update the 'nodev' and 'juris_id' fields of Horizon 'zoning_parcels.csv'
  input with Draft Blueprint value while keeping other 
  Horizon zoning information (e.g. development types, development intensities)

"""
import pandas as pd
import os
import numpy as np


if os.getenv('USERNAME')=='ywang':
    BOX_DIR             = 'C:\\Users\\{}\\Box\\Modeling and Surveys\\Urban Modeling\\Bay Area UrbanSim 1.5\\PBA50'.format(os.getenv('USERNAME'))
    HORIZON_DIR         = os.path.join(BOX_DIR, 'OLD Horizon Large General Input Data')  
    DRAFTBLUEPRINT_DIR  = os.path.join(BOX_DIR, 'Current PBA50 Large General Input Data')
    PBA50_ZONING_DIR    = os.path.join(BOX_DIR, 'Policies', 'Zoning Modifications')


if __name__ == '__main__':

    # Horizon zoning_parcels.csv
    pz_horizon_file = os.path.join(HORIZON_DIR, '2015_12_21_zoning_parcels.csv')
    pz_horizon_cols = ['geom_id','zoning_id','zoning','juris',
                       'prop','tablename','nodev_pba40']
    pz_horizon      = pd.read_csv(pz_horizon_file,
                                  usecols = pz_horizon_cols)

    print('Read {} rows from {}'.format(len(pz_horizon), pz_horizon_file))
    print('Header: {}'.format(pz_horizon.head()))
    print('Number of unique zoning_id is {}'.format(len(pz_horizon.zoning_id.unique())))
    
    pz_horizon.rename(columns={'nodev':'nodev_pba40'},inplace = True)


    # PBA50 zoning input
    pz_pba50_file   = os.path.join(PBA50_ZONING_DIR, 'p10_pba50_attr_20200416.csv')
    pz_pba50_cols   = ['PARCEL_ID','geom_id_s','nodev','juris_id']
    pz_pba50        = pd.read_csv(pz_pba50_file, 
                                  usecols=pz_pba50_cols)

    print('Read {} rows from {}'.format(len(pz_pba50), pz_pba50_file))
    print('Header: {}'.format(pz_pba50.head()))

    pz_pba50['geom_id_s'] = pd.to_numeric(pz_pba50['geom_id_s'])
    pz_pba50.rename(columns = {'geom_id_s':'geom_id'},inplace = True)

    # Merge 
    merg = pz_horizon.merge(pz_pba50, 
                            on = 'geom_id', 
                            how = 'left')

    for i in ['zoning_id','PARCEL_ID','nodev']:
        try:
            merg[i] = merg[i].fillna(-1).astype(np.int64)
            merg[i].replace(-1, None, inplace = True)
        except:
            print(i)
            pass
    print('Merge pz_pba50 value with pz_horizon zoning_parcels')
    display(merg.dtypes)

    merg.to_csv(os.path.join(DRAFTBLUEPRINT_DIR, 'zoning_parcels.csv'))


    # For QA/QC of the nodev field

    # Parcels whose 'nodev' value is 1 in Horizon but 0 in Draft Blueprint
    nodev_pba40_1_pba50_0 = merg.loc[(merg['nodev_pba40'] == 1) & (merg['nodev'] == 0)]
    nodev_pba40_1_pba50_0.drop(columns = 'geom_id',inplace = True)
    nodev_pba40_1_pba50_0.to_csv(os.path.join(PBA50_ZONING_DIR, 'nodev_pba40_1_pba50_0.csv'))

    # Parcels whose 'nodev' value is 0 in Horizon but 1 in Draft Blueprint
    nodev_pba40_0_pba50_1 = merg.loc[(merg['nodev_pba40'] == 0) & (merg['nodev'] == 1)]
    #nodev_pba40_0_pba50_1
    nodev_pba40_0_pba50_1.drop(columns = 'geom_id',inplace = True)
    nodev_pba40_0_pba50_1.to_csv(os.path.join(PBA50_ZONING_DIR, 'nodev_pba40_0_pba50_1.csv'))