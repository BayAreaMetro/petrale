# Notes:
# Part 1 is to update the 'parcels_geography.csv' file with the new zoningmods and nodev attributes
# Part 2 is to generate geospacial files to use in GIS. The output file dissolves parcels on 'pba50zoningmodcat', and contains "parcel count" and "total acres" for each dissolved geometry. The script enables two approaches for dissolving: 
#     1) Load the 'UrbanSim_input_Zoning\outputs\parcel_zoningmods.shp' into ArcGIS and dissolve.
#     2) Dissolve in geopands and then export. 

import pandas as pd
import numpy as np
#import geopandas as gpd
#import fiona
import os, glob
import time

NOW = time.strftime("%Y_%m%d_%H%M")
today = time.strftime('%Y_%m_%d')


if os.getenv('USERNAME')=='ywang':
    BOX_DIR             = 'C:\\Users\\{}\\Box\\Modeling and Surveys\\Urban Modeling\\Bay Area UrbanSim 1.5'.format(os.getenv('USERNAME'))
    BOX_SMELT_DIR       = 'C:\\Users\\{}\\Box\\baydata\\smelt\\2020 03 12'.format(os.getenv('USERNAME'))
    GITHUB_PETRALE_DIR  = 'C:\\Users\\{}\\Documents\\GitHub\\petrale'.format(os.getenv('USERNAME'))

# input file locations
PBA40_ZONING_BOX_DIR    = os.path.join(BOX_DIR, 'Horizon\\Current Horizon Large General Input Data')
PBA50_ZONINGMOD_DIR     = os.path.join(BOX_DIR, 'PBA50\\Policies\\Zoning Modifications')
JURIS_CODE_DIR          = os.path.join(GITHUB_PETRALE_DIR, 'zones\\jurisdictions')
P10_GEO_INOUT_DIR       = os.path.join(BOX_DIR, 'PBA50\\Policies\\Base zoning\\inputs')

# outputs locations
CSV_OUTPUTS_DIR         = os.path.join(BOX_DIR, 'PBA50\\Current PBA50 Large General Input Data')
GIS_OUTPUTS_DIR         = os.path.join(BOX_DIR, 'PBA50\\Policies\\Zoning Modifications\\GIS_data')



if __name__ == '__main__':


    ## Basemap parcels
    basemap_p10_file = os.path.join(BOX_SMELT_DIR, 'p10.csv')
    basemap_p10 = pd.read_csv(basemap_p10_file,
                              usecols =['PARCEL_ID','geom_id_s','ACRES','LAND_VALUE'],
                              dtype   ={'PARCEL_ID':np.float64, 'geom_id_s':str, 'ACRES':np.float64, 'LAND_VALUE':np.float64})
    # conver PARCEL_ID to integer:
    basemap_p10['PARCEL_ID'] = basemap_p10['PARCEL_ID'].apply(lambda x: int(round(x)))
    basemap_p10['geom_id_s'] = basemap_p10['geom_id_s'].apply(lambda x: int(x))
    print(basemap_p10.dtypes)

    ## Read PBA40 parcels_geography file
    pg_pba40_file = os.path.join(PBA40_ZONING_BOX_DIR, '07_11_2019_parcels_geography.csv')
    pg_pba40 = pd.read_csv(pg_pba40_file,
                           usecols = ['Unnamed: 0','geom_id','urbanized'])
    print(pg_pba40.head())
    print(pg_pba40.dtypes)

    ## Read PBA50 attributes
    pba50_attrs_file = os.path.join(PBA50_ZONINGMOD_DIR, 'p10_pba50_attr_20200416.csv')
    pba50_attrs_cols = ['geom_id_s','pda_id', 'tpp_id', 'exp_id', 'exp_score', 'opp_id', 'zoningmodcat', 
                        'perffoot', 'perfarea', 'mapshell', 'tpa_id', 'perfarea2', 'alt_zoning', 'zonetype', 'pubopp_id', 
                        'puboppuse', 'juris_id', 'juris','hra_id', 'trich_id', 'cat_id', 'chcat', 'zoninghzcat', 
                        'gg_id', 'tra_id', 'sesit_id', 'ppa_id', 'exp2020_id', 'pba50chcat', 'exsfd_id', 'chcatwsfd', 
                        'pba50zoningmodcat', 'nodev']
    pba50_attrs = pd.read_csv(pba50_attrs_file,
                              usecols = pba50_attrs_cols)
    print(pba50_attrs.head())
    print(pba50_attrs.dtypes)

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
                                                                            how = 'left')
    print(pg_pba50_merge.head())                            

    ## export needed fields

    # Parcel attribute:
    p_att = ['PARCEL_ID','geom_id','jurisdiction_id','juris_name_full','juris','ACRES']

    # PBA40 fields:
    pba40_att = ['pda_id', 'tpp_id', 'exp_id', 'opp_id', 'zoningmodcat', 'perffoot', 'perfarea', 'urbanized']

    # Horizon fields:
    hor_att = ['hra_id', 'trich_id', 'cat_id', 'zoninghzcat']

    # PBA50 fields:
    pba50_att = ['gg_id', 'tra_id', 'sesit_id', 'ppa_id', 'exp2020_id', 'exsfd_id', 'pba50zoningmodcat', 'nodev','pba50chcat']

    # export:
    pg_pba50_all = pg_pba50_merge[p_att + pba40_att + hor_att + pba50_att]
    pg_pba50_all.to_csv(os.path.join(CSV_OUTPUTS_DIR, today+'_parcels_geography.csv'))

    pg_pba50_only = pg_pba50_merge[p_att + pba50_att]
    pg_pba50_only.to_csv(os.path.join(CSV_OUTPUTS_DIR, today+'_parcels_geography_pba50_only.csv'))



    # ################ Generate 'parcel_zoningmods.shp' for mapping ###

    # ## Read p10 geographic data
    # p10_geo_file = os.path.join(P10_GEO_INOUT_DIR, 'p10_geo_shp.shp')
    # p10_geo      = gpd.read_file(p10_geo_file)
    # logger.info('Read {} rows from {}, with header:'.format(len(p10_geo),p10_geo_file,p10_geo.head()))

    # p10_geo.PARCEL_ID = p10_geo.PARCEL_ID.apply(lambda x: int(x))
    # p10_geo.geom_id_s = p10_geo.geom_id_s.apply(lambda x: int(x))

    # ## merge with pba50 parcels_geography
    # pg_pba50_geo = pg_pba50_only.merge(p10_geo, 
    #                                    on = 'geom_id_s', 
    #                                    how = 'left')

    # ## export select required fields
    # pg_pba50_geo[['ACRES']] = pg_pba50_geo[['ACRES']].fillna(value=0)
    # for i in ['gg_id', 'tra_id', 'sesit_id', 'ppa_id', 'exp2020_id', 'exsfd_id']:
    #     pg_pba50_geo[[i]] = pg_pba50_geo[[i]].fillna(value= 'NA')

    # pg_pba50_geo_shape = gpd.GeoDataFrame(pg_pba50_geo, geometry='geometry')


    # pg_pba50_geo_shape = pg_pba50_geo_shape.where(pd.notnull(pg_pba50_geo_shape), None)
    # pg_pba50_geo_shape.to_file(os.path.join(GIS_OUTPUTS_DIR, today+'_parcel_zoningmods.shp'))


    # ## create ['pba50zoningmodcat','pba50chcat'] file as a lookup file
    # for_join = pg_pba50_only[['pba50zoningmodcat','pba50chcat']].drop_duplicates()
    # print(for_join.shape)
    # for_join.to_csv(os.path.join(GIS_OUTPUTS_DIR, today+'zoningmods_for_join.csv'))

    # ## statistics around zoningmodcat
    # stats = pg_pba50_geo_shape[['PARCEL_ID','ACRES','pba50zoningmodcat']].groupby(['pba50zoningmodcat']).agg({'PARCEL_ID':'count', 'ACRES': 'sum'}).reset_index()
    # stats = stats.merge(for_join, on = 'pba50zoningmodcat', how = 'left')
    # stats.columns = ['pba50zoningmodcat', 'parcel_count','acres','pba50chcat']
    # stats_nonZero = stats.query('parcel_count > 0 & acres > 0')
    # print(stats_nonZero.shape)

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
