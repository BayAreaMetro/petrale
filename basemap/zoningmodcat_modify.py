#!/usr/bin/env python
# coding: utf-8

import pandas as pd

# load files
pcl19 = pd.read_csv('07_11_2019_parcels_geography.csv')
p10_pba50_att = pd.read_csv('p10_pba50_attr_20200221.csv')

#pcl19.head()
#p10_pba50_att.head()

# check unique ID in both tables
print(len(pcl19.geom_id.unique()) == pcl19.shape[0])
print(len(p10_pba50_att.GEOM_ID.unique()) == p10_pba50_att.shape[0])

print(pcl19.shape[0])
print(p10_pba50_att.shape[0])

# outer join two tables
pcl19['geom_id'] = pcl19['geom_id'].apply(lambda x: int(x))
p10_pba50_att['geom_id_s'] = p10_pba50_att['geom_id_s'].apply(lambda x: int(x))
merg_outer = pd.merge(pcl19,p10_pba50_att, how='outer', left_on='geom_id', right_on='geom_id_s')
display(merg_outer.head())
merg_outer.shape[0]

# check if missing pba50zoningmodcat
missing50cat = merg_outer.loc[merg_outer.pba50zoningmodcat.isnull()]
display(missing50cat)
print(missing50cat.shape[0] / pcl19.shape[0])

# append only the new zoningmodcat to the parcel table
pcl_new = pd.merge(pcl19, p10_pba50_att[['geom_id_s','pba50zoningmodcat']],how='outer', left_on='geom_id', right_on='geom_id_s')
pcl_new.drop(columns=['geom_id_s'],inplace = True)
display(pcl_new)

# export
merg_outer.to_csv('02_21_2020_parcels_geography_allFields.csv', index = False)
pcl_new.to_csv('02_21_2020_parcels_geography.csv', index = False)

