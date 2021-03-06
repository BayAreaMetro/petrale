USAGE = """

Summarize deed-restricted units by source, year-built, and locations.

"""

import glob, os, time
import pandas as pd
import numpy as np


# set up file directory and run_id dictionary
# when we have new runs, copy the 'building_data_2050.csv' output to this directory,
# and add the new run_id and BAUS version to runid dictionry 

run_dir = 'M:\\Data\\Urban\\BAUS\\PBA50\\Final_Blueprint\\run_analysis\\DR analysis'
os.chdir(run_dir)

# run_id dictionary
runid = {'run325': 'v2.2.1',
         'run241': 'v2.3',
         'run242': 'v2.3.1',
         'run152': 'v2.4',
         'run327': 'v2.5',
         'run243': 'v2.6',
         'run158': 'v2.7',
         'run335': 'v2.8',
         #'run160': 'v2.9',
         #'run253': 'v2.10',
         #'run161': 'v2.11',
         #'run340': 'v2.12',
         'run254': 'v2.13',
         'run171': 'v2.14',
         'run347': 'v2.15',
         'run261': 'v2.16'}


if __name__ == '__main__':


    ###### step 1: get parcel_id - geographies mapping

    p_geo = pd.read_csv('util\\2020_09_21_parcels_geography.csv',
                        usecols = ['PARCEL_ID', 'juris',
                                   #'fbpzoningm', 'fbp_gg_id', 'pda_id_pba50_fb', 'fbp_tra_id', 
                                   'fbp_sesit_id'])
    juris_county = pd.read_csv('util\\juris_county_id.csv', 
                               usecols = ['juris_name_full', 'baus_output_juris_name', 'county_name'])

    p_taz = pd.read_csv('util\\2020_08_17_parcel_to_taz1454sub.csv',
                        usecols = ['PARCEL_ID', 'ZONE_ID'],
                        dtype = {'PARCEL_ID': int, 'ZONE_ID': int})

    taz_sd = pd.read_csv('util\\taz_geography.csv', usecols = ['zone','superdistrict'])
    taz_sd.columns=['zone','sd_number']

    sd = pd.read_csv('util\\superdistricts.csv', usecols = ['number', 'name', 'subregion'])
    sd.columns = ['sd_number','superdistrict','subregion']

    p_geo = p_geo.merge(juris_county,
                        left_on='juris',
                        right_on='juris_name_full',
                        how='left').merge(p_taz,
                                          on='PARCEL_ID',
                                          how='left').merge(taz_sd,
                                                            left_on='ZONE_ID',
                                                            right_on='zone',
                                                            how='left').merge(sd,
                                                                              on='sd_number',
                                                                              how='left')
    print(p_geo.head())


    ###### step 2: create index variables

    juris = list(p_geo.juris.unique())
    superdistrict = p_geo.superdistrict.unique()
    zone = p_geo.zone.unique()
    hra = ['HRA','non-HRA']
    dis = ['DIS','non-DIS']
    county = juris_county.county_name.unique()
    year = list(range(2015, 2055, 5))
    dr_type = ['deed_restricted_units', 'inclusionary_units', 'preserved_units', 'subsidized_units']


    # set up tables for all DR cross-year comparison
    # note: DR source breakdown table is set up within the loop in step 3

    files = dict()

    all_idx = {'dr_county_all': county,
               'dr_juris_all': juris,
               'dr_sd_all': superdistrict,
               'dr_taz_all': zone,
               'dr_hra_all': hra,
               'dr_dis_all': dis}

    for tablename in all_idx.keys():
        table = pd.Series(np.nan, index = all_idx[tablename], name='temp')
        files[tablename] = table

    # create excel
    today = time.strftime('%Y_%m_%d')
    writer = pd.ExcelWriter('deed_restricted_units_summary_{}.xlsx'.format(today), engine='xlsxwriter')

    dr_breakdonw = pd.DataFrame(columns = ['county_name', 'year', 'deed_restricted_units', 'inclusionary_units', 
                                            'preserved_units', 'subsidized_units', 'dr_units_publicLand', 'version'])

    ###### step 3: loop through all building_data_2050.csv outputs

    for file in list(glob.glob('*.csv')):

        if 'building_data_2050.csv' in file:
            print('{}: {}'.format(file, runid[file.split('_')[0]]))
            
            df = pd.read_csv(file,
                             usecols = ['parcel_id', 'source', 'year_built',
                                        'residential_units','deed_restricted_units',
                                        'inclusionary_units','preserved_units', 'subsidized_units'])
            df = df.merge(p_geo, left_on='parcel_id', right_on='PARCEL_ID', how='left')
            
            # code HRA/non-HRA and DIS/non-DIS
            df['HRA'] = 'HRA'
            df.loc[(df.fbp_sesit_id == 'DIS') | (df.fbp_sesit_id.isnull()), 'HRA'] = 'non-HRA'
            df['DIS'] = 'DIS'
            df.loc[(df.fbp_sesit_id == 'HRA') | (df.fbp_sesit_id.isnull()), 'DIS'] = 'non-DIS'
            
            #### all DR

            # DR counts by county
            dr_county = df.groupby(['county_name'])['deed_restricted_units'].sum()
            dr_county.rename('dr_units_'+runid[file.split('_')[0]], inplace=True)
            dr_county_all = files['dr_county_all']
            dr_county_all = pd.concat([dr_county_all, dr_county], axis=1)
            files['dr_county_all'] = dr_county_all
                   
            # DR counts by jurisdiction
            dr_juris = df.groupby(['juris'])['deed_restricted_units'].sum()
            dr_juris.rename('dr_units_'+runid[file.split('_')[0]], inplace=True)
            dr_juris_all = files['dr_juris_all']
            dr_juris_all = pd.concat([dr_juris_all, dr_juris], axis=1)
            files['dr_juris_all'] = dr_juris_all
     
            # DR counts by superdistrict
            dr_sd = df.groupby(['superdistrict'])['deed_restricted_units'].sum()
            dr_sd.rename('dr_units_'+runid[file.split('_')[0]], inplace=True)
            dr_sd_all = files['dr_sd_all']
            dr_sd_all = pd.concat([dr_sd_all, dr_sd], axis=1)
            files['dr_sd_all'] = dr_sd_all

            # DR counts by taz
            dr_taz = df.groupby(['zone'])['deed_restricted_units'].sum()
            dr_taz.rename('dr_units_'+runid[file.split('_')[0]], inplace=True)
            dr_taz_all = files['dr_taz_all']
            dr_taz_all = pd.concat([dr_taz_all, dr_taz], axis=1)
            files['dr_taz_all'] = dr_taz_all


            dr_hra = df.groupby(['HRA'])['deed_restricted_units'].sum()
            dr_hra.rename('dr_units_'+runid[file.split('_')[0]], inplace=True)
            dr_hra_all = files['dr_hra_all']
            dr_hra_all = pd.concat([dr_hra_all, dr_hra], axis=1)
            files['dr_hra_all'] = dr_hra_all
            
            dr_dis = df.groupby(['DIS'])['deed_restricted_units'].sum()
            dr_dis.rename('dr_units_'+runid[file.split('_')[0]], inplace=True)
            dr_dis_all = files['dr_dis_all']
            dr_dis_all = pd.concat([dr_dis_all, dr_dis], axis=1)
            files['dr_dis_all'] = dr_dis_all

            #### DR breakdown   
            
            # set up tables for single-year DR breakdown
            county_year = pd.DataFrame([[ct, yr] for ct in county for yr in year], 
                                       columns = ['county_name','year'])
           
            # public-land DR
            dr_pub = df.loc[df.source == 'pub'].groupby(['county_name','year_built'])['deed_restricted_units'].sum().reset_index()
            dr_pub.rename(columns={'year_built': 'year',
                                   'deed_restricted_units': 'dr_units_publicLand'}, inplace=True)

            # all DR, preserved_units, inclusionary_units, subsidized_units
            dr_all = pd.DataFrame(columns =['juris','year', 'deed_restricted_units', 'preserved_units',
                                            'inclusionary_units', 'subsidized_units'])

            for filename in list(glob.glob('*.csv')):
                if file.split('_')[0]+'_juris_summaries' in filename:
                    print(filename)
                    df2 = pd.read_csv(filename,
                                      usecols = ['juris','deed_restricted_units', 'preserved_units',
                                                 'inclusionary_units', 'subsidized_units'])
                    df2['year'] = int(filename.split('.')[0].split('_')[-1])
                    dr_all = pd.concat([dr_all, df2])

            dr_all = dr_all.merge(juris_county[['baus_output_juris_name', 'county_name']],
                                  left_on = 'juris',
                                  right_on = 'baus_output_juris_name',
                                  how='left')

            dr_all_county = dr_all.groupby(['county_name', 'year'])['deed_restricted_units', 'preserved_units',
                                                                    'inclusionary_units', 'subsidized_units'].sum().reset_index()

            # merge
            county_year = county_year.merge(dr_all_county,
                                            on=['county_name', 'year'],
                                            how='left').merge(dr_pub,
                                                              on=['county_name', 'year'],
                                                              how='left')

            # write to the excel
            county_year.to_excel(writer, sheet_name='breakdown_'+runid[file.split('_')[0]], index=False)

            county_year['version'] = runid[file.split('_')[0]]
            dr_breakdonw = pd.concat([dr_breakdonw, county_year])

    ###### step 4: write all DR cross-run comparisons to excel

    for tablename in files.keys():
        table = files[tablename]
        table.drop(columns=['temp'], inplace=True)
        table.to_excel(writer, sheet_name=tablename)

    writer.save()

    dr_breakdonw.to_csv('dr_breakdonw_{}.csv'.format(today), index=False)



