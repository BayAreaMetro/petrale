#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy as np

# raw data: 'p10_pba50_attr_20200416.csv' at https://mtcdrive.app.box.com/file/654543170007
zoningmod = pd.read_csv(r'C:\Users\ywang\Documents\Files_for_Py\UrbanSim_input_Zoning\inputs\p10_pba50_attr_20200416.csv',usecols = ['pba50chcat','gg_id','tra_id','sesit_id', 'ppa_id'])
zoningmod.drop_duplicates(inplace = True)

# set default as 0.1 which is the minumum requirement
zoningmod['inclusionary'] = 0.10

zoningmod_noCrossing = zoningmod.copy()
zoningmod_crossing = zoningmod.copy()

min_20_idx = (zoningmod['gg_id'] == 'GG') & (
                (zoningmod['tra_id'] == 'tra1')   | (
                 zoningmod['tra_id'] == 'tra2')   | (
                 zoningmod['tra_id'] == 'tra3')   | (
                 zoningmod['tra_id'] == 'tra2c1') | (
                 zoningmod['tra_id'] == 'tra3c1') | (
                 zoningmod['tra_id'] == 'tra3c2')) & (
               zoningmod['sesit_id'] == 'HRA') & (
               zoningmod['ppa_id'].isnull())

min_15_idx_1_noCrossing = (zoningmod['gg_id'] == 'GG') & (
                            (zoningmod['tra_id'] == 'tra1') | (
                             zoningmod['tra_id'] == 'tra2') | (
                             zoningmod['tra_id'] == 'tra2c1')) & (
                           zoningmod['sesit_id'].isnull()) & (
                           zoningmod['ppa_id'].isnull())

min_15_idx_1_crossing = (zoningmod['gg_id'] == 'GG') & (
                          (zoningmod['tra_id'] == 'tra1')   | (
                           zoningmod['tra_id'] == 'tra2')   | (
                           zoningmod['tra_id'] == 'tra2c1') | (
                           zoningmod['tra_id'] == 'tra3c1') | (
                           zoningmod['tra_id'] == 'tra3c2')) & (
                         zoningmod['sesit_id'].isnull()) & (
                         zoningmod['ppa_id'].isnull())

min_15_idx_2 = (zoningmod_noCrossing['gg_id'] == 'GG') & (
                zoningmod_noCrossing['tra_id'].isnull()
                ) & (zoningmod_noCrossing['sesit_id'] == 'HRA'
                ) & (zoningmod_noCrossing['ppa_id'].isnull())

zoningmod_noCrossing.loc[min_20_idx,'inclusionary'] = 0.20
zoningmod_noCrossing.loc[min_15_idx_1_noCrossing,'inclusionary'] = 0.15
zoningmod_noCrossing.loc[min_15_idx_2,'inclusionary'] = 0.15

zoningmod_crossing.loc[min_20_idx,'inclusionary'] = 0.20
zoningmod_crossing.loc[min_15_idx_1_crossing,'inclusionary'] = 0.15
zoningmod_crossing.loc[min_15_idx_2,'inclusionary'] = 0.15

## sort to view pba50chcat by inclusionary level
zoningmod_noCrossing.sort_values(by=['inclusionary','pba50chcat'], inplace = True)
zoningmod_crossing.sort_values(by=['inclusionary','pba50chcat'], inplace = True)


## export
zoningmod_noCrossing.to_csv('pab50_inclusionary_noCrossing.csv')
zoningmod_crossing.to_csv('pab50_inclusionary_crossing.csv')
