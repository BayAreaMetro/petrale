import pandas as pd
import os

# read parcel data with tra_id, hra_id and pda_id
parcel_file = 'C:\\Users\\{}\\Box\\Modeling and Surveys\\Urban Modeling\\Bay Area UrbanSim\\PBA50\\Current PBA50 Large General Input Data\\2021_02_25_parcels_geography.csv'.format(os.getenv('USERNAME'))
df_p = pd.read_csv(parcel_file,
                   usecols = ['PARCEL_ID', 'fbp_tra_id', 'fbp_sesit_id', 'pda_id_pba50_fb', 'juris'])
print('read {} rows of data from {}'.format(df_p.shape[0], parcel_file))


# read parcel data with pda names
pda_name_file = 'M:\\Data\\GIS layers\\Blueprint Land Use Strategies\\ID_idx\\Final Blueprint\\2020_09_17_p10_pda_idx.csv'
df_pda = pd.read_csv(pda_name_file,
                     usecols = ['PARCEL_ID', 'pda_name'])
print('read {} rows of data from {}'.format(df_pda.shape[0], pda_name_file))

# merge
df = df_p.merge(df_pda, on='PARCEL_ID', how='inner')


# benchmark
print(df.fbp_tra_id.value_counts())
print(df.fbp_sesit_id.value_counts())


# configure the tra_id field
df.loc[df.fbp_tra_id.isnull(), 'fbp_tra_id'] = 'non-tra'

# create an tra_cat_id field
df['fbp_tra_cat_id'] = df['fbp_tra_id']
df.loc[df.fbp_tra_id.isin(['tra2a', 'tra2b', 'tra2c']), 'fbp_tra_cat_id'] = 'tra2'

# create an hra_id field
df['fbp_hra_id'] = 'non-HRA'
df.loc[(df.fbp_sesit_id == 'HRADIS') | (df.fbp_sesit_id == 'HRA'), 'fbp_hra_id'] = 'HRA'

# verify
print(df.fbp_tra_id.value_counts())
print(df.fbp_tra_cat_id.value_counts())
print(df.fbp_hra_id.value_counts())

# remove extra field
df.drop('fbp_sesit_id', axis=1, inplace=True)

# add synthetic parcels with job/hh
df = df.append({'PARCEL_ID':       2054505,
                'fbp_tra_id':     'non-tra',
                'fbp_tra_cat_id': 'non-tra',
                'fbp_hra_id':     'non-HRA'}, ignore_index=True)


# save to M
output_file = 'M:\\Data\\GIS layers\\Blueprint Land Use Strategies\\ID_idx\\Final Blueprint\\parcel_tra_hra_pda_fbp_20210816.csv'
print(df.dtypes)
print('export {} rows of data to {}'.format(df.shape[0], output_file))
df.to_csv(output_file, index=False)

