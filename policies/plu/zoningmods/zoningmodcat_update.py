# Notes:
# Part 1 is to update the 'parcels_geography.csv' file with the new zoningmods and nodev attributes
# Part 2 is to generate geospacial files to use in GIS. The output file dissolves parcels on 'pba50zoningmodcat', and contains "parcel count" and "total acres" for each dissolved geometry. The script enables two approaches for dissolving: 
#     1) Load the 'UrbanSim_input_Zoning\outputs\parcel_zoningmods.shp' into ArcGIS and dissolve.
#     2) Dissolve in geopands and then export. 

import pandas as pd
import geopandas as gpd
import os
import fiona
from datetime import datetime

if os.getenv('USERNAME')=='ywang':
    folder      = 'C:\\Users\\ywang\\Documents\\Files_for_Py\\UrbanSim_input_Zoning'
    input_dir   = os.path.join(folder, 'inputs')
    output_dir  = os.path.join(folder, 'outputs')

## Input
juris_raw = pd.read_csv(input_dir + '\\jurisId.csv')
pg_old = pd.read_csv(input_dir + '\\07_11_2019_parcels_geography.csv')
pba50_att_raw = pd.read_csv(input_dir + '\\p10_pba50_attr_20200416.csv')
p10_geo = gpd.read_file(input_dir + '\\p10_geo_shp.shp')


###############################################
####### Update 'parcels_geography.csv' ########

pba50_att = pba50_att_raw[['geom_id_s','pda_id', 'tpp_id', 'exp_id', 'exp_score', 'opp_id', 'zoningmodcat', 
                           'perffoot', 'perfarea', 'mapshell', 'tpa_id', 'perfarea2', 'alt_zoning', 'zonetype', 'pubopp_id', 
                           'puboppuse', 'juris_id', 'juris','hra_id', 'trich_id', 'cat_id', 'chcat', 'zoninghzcat', 
                           'gg_id', 'tra_id', 'sesit_id', 'ppa_id', 'exp2020_id', 'pba50chcat', 'exsfd_id', 'chcatwsfd', 
                           'pba50zoningmodcat', 'nodev']]
pg_temp = pg_old[['Unnamed: 0','geom_id','urbanized']]
juris = juris_raw[['jurisdiction_id','juris_id']]
p10_geo.PARCEL_ID = p10_geo.PARCEL_ID.apply(lambda x: int(x))
p10_geo.geom_id_s = p10_geo.geom_id_s.apply(lambda x: int(x))

pg = pg_temp.merge(pba50_att, left_on = 'geom_id', right_on = 'geom_id_s', how = 'left').merge(
    juris, on = 'juris_id', how = 'left').merge(p10_geo, on = 'geom_id_s', how = 'left')

## check missing pba50zoningmod
#print(pg.loc[pg.pba50zoningmodcat.isnull()].shape[0] == 0)

## Parcel attribute:
p_att = ['PARCEL_ID','geom_id','jurisdiction_id','juris_id','juris','ACRES']

## PBA40 fields:
pba40_att = ['pda_id', 'tpp_id', 'exp_id', 'opp_id', 'zoningmodcat', 'perffoot', 'perfarea', 'urbanized']

## Horizon fields:
hor_att = ['hra_id', 'trich_id', 'cat_id', 'zoninghzcat']

## PBA50 fields:
pba50_att = ['gg_id', 'tra_id', 'sesit_id', 'ppa_id', 'exp2020_id', 'exsfd_id', 'pba50zoningmodcat', 'nodev','pba50chcat']

## Today's date in output file name:
today = datetime.today().strftime('%Y_%m_%d')

## Export
pg_csv_all = pg[p_att + pba40_att + hor_att + pba50_att]
pg_csv_all.to_csv(output_dir + '\\'+today+'_parcels_geography.csv')

pg_csv = pg[p_att + pba50_att]
pg_csv.to_csv(output_dir + '\\'+today+'_parcels_geography_pba50_only.csv')


####################################################
### Generate 'parcel_zoningmods.shp' for mapping ###

## select required fields
pg_geo = gpd.GeoDataFrame(pg[p_att + pba50_att + ['geometry']], geometry='geometry')
pg_geo[['ACRES']] = pg_geo[['ACRES']].fillna(value=0)
for i in ['gg_id', 'tra_id', 'sesit_id', 'ppa_id', 'exp2020_id', 'exsfd_id']:
    pg_geo[[i]] = pg_geo[[i]].fillna(value= 'NA')
pg_geo = pg_geo.where(pd.notnull(pg_geo), None)
pg_geo.to_file(output_dir + '\\'+today+'_parcel_zoningmods.shp')


## create ['pba50zoningmodcat','pba50chcat'] file as a lookup file
for_join = pg[['pba50zoningmodcat','pba50chcat']].drop_duplicates()
print(for_join.shape)
for_join.to_csv(output_dir + '\\'+today+'zoningmods_for_join.csv')

## statistics around zoningmodcat
stats = pg_geo[['PARCEL_ID','ACRES','pba50zoningmodcat']].groupby(['pba50zoningmodcat']).agg({'PARCEL_ID':'count', 'ACRES': 'sum'}).reset_index()
stats = stats.merge(for_join, on = 'pba50zoningmodcat', how = 'left')
stats.columns = ['pba50zoningmodcat', 'parcel_count','acres','pba50chcat']
stats_nonZero = stats.query('parcel_count > 0 & acres > 0')
print(stats_nonZero.shape)

## create mapping file
"""
pg_geo['modTemp'] = pg_geo[['gg_id', 'tra_id', 'sesit_id', 'ppa_id']].apply(lambda row: '_'.join(row.values.astype(str)), axis=1)

gdf = gpd.GeoDataFrame(pg_geo[['PARCEL_ID','modTemp','geometry']], geometry='geometry')
print(gdf.shape)
gdf2 = gdf.loc[gdf.geometry.notnull(),:]
print(gdf2.shape)
"""

## dissolve by pba50zoningmodca
"""
gdf2['geometry'] = gdf2.buffer(0.01)
try:
    zoningmod_dis = gdf2.dissolve(by='modTemp',as_index=False)
except:
    print('error: ', gdf2.modTemp)

display(zoningmod_dis.head())

df = pd.DataFrame(zoningmod_dis, copy=True)
df_split = pd.concat([df['modTemp'].str.split('_', expand=True), df['geometry'],df['PARCEL_ID']], axis=1)
display(df_split.head())
df_split.columns = ['juris_id', 'gg_id', 'tra_id', 'sesit_id', 'ppa_id', 'exp2020_id', 'exsfd_id', 'chcatwsfd','NA','geometry','PARCEL_ID']
df_split = df_split.merge(juris_name[['jurisdiction','juris']], left_on = 'juris_id', right_on = 'juris',how = 'left')
df_split.drop(columns = ['juris','juris_id'], inplace = True)
dissolved = gpd.GeoDataFrame(df_split, geometry='geometry')
dissolved.to_file(output_dir + '\\pba50_zoningmods_diss.shp')
"""
