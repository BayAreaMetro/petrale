
import pandas as pd
import numpy as np
import os, glob, logging, sys, time

#p10_PDA.csv is created in ArcGIS through spatial join of p10 polygons and Draft Blueprint growth geography polygons.

#p10                : M:\Data\GIS layers\UrbanSim smelt\2020 03 12\smelt.gdb
#PDA                : http://opendata.mtc.ca.gov/datasets/priority-development-areas-current?geometry=-129.633%2C36.372%2C-114.945%2C39.406
#Spatial join rule  : Centers of p10 polygons fall into PDA polygons
#Spatial join output: M:\Data\GIS layers\Blueprint Land Use Strategies\Blueprint Land Use Strategies.gdb\p10_PDA

#Then run script 'https://github.com/BayAreaMetro/petrale/blob/master/basemap/import_filegdb_layers.py' 
#to export the 'p10_PDA' layer to .csv format: p10_PDA_06112020.csv

NOW = time.strftime("%Y_%m%d_%H%M")
today = time.strftime('%Y_%m_%d')


if os.getenv('USERNAME')=='ywang':
    WORK_DIR            = 'M:\\Data\\GIS layers\\Blueprint Land Use Strategies\\ID_idx'
    URBANSIM_DIR        = 'C:\\Users\\{}\\Documents\\GitHub\\bayarea_urbansim'.format(os.getenv('USERNAME'))
    BOX_DIR             = 'C:\\Users\\{}\\Box\\Modeling and Surveys\\Urban Modeling\\Bay Area UrbanSim'.format(os.getenv('USERNAME'))
    
# output folders
PBA50_PARCEL_GEO_DIR    = os.path.join(BOX_DIR, 'PBA50\\Current PBA50 Large General Input Data')
URBANSIM_INPUT_DIR      = os.path.join(URBANSIM_DIR, 'data')
LOG_FILE                = os.path.join(PBA50_PARCEL_GEO_DIR,'{}_parcel_BlueprintGeos_idx.log'.format(today))



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

    logger.info("PBA50_PARCEL_GEO_DIR = {}".format(PBA50_PARCEL_GEO_DIR))


	# Read input
	p10_pda_file = os.path.join(WORK_DIR, 'p10_PDA_06112020.csv')
	p10_pda_raw = pd.read_csv(p10_pda_file)
	logger.info('Read {:,} rows from p10_PDA_file'.format(len(p10_pda_raw)))
	logger.info('{:,} unique PARCEL_IDs'.format(len(p10_pda_raw.PARCEL_ID.unique())))

	# Keep needed fields and name them as needed
	p10_pda = p10_pda_raw[['PARCEL_ID','geom_id_s','manual_county',
						   'county','ACRES','pda_name','jurisdicti']]
	p10_pda.rename(columns = {'jurisdicti': 'jurisdiction',
	                          'manual_county': 'county_ID'}, inplace = True)

	# Get unique PDAs
	pdas = p10_pda[['jurisdiction','pda_name']].drop_duplicates()
	pdas = pdas.loc[(pdas.pda_name.notnull()) & (pdas.pda_name != ' ')]
	pdas.sort_values(by = ['jurisdiction','pda_name'], inplace = True)
	logger.info('There are {:,} unique PDAs in {} jurisdictions'.format(len(pdas), \
		len(pdas.jurisdiction.unique())))
	logger.info(pdas.head())

	# Assign index to PDAs by jurisdiction
	pdas['idx'] = pdas.groupby(['jurisdiction']).cumcount()+1
	logger.info(pdas.head())

	# Join the index back to p10 parcels
	p10_pda_idx = p10_pda.merge(pdas, 
	                            on = ['pda_name','jurisdiction'],
	                            how = 'left')

	p10_pda_idx['PARCEL_ID'] = p10_pda_idx['PARCEL_ID'].apply(lambda x: int(round(x)))

	# create pda_id by concatenating jurisdiction name and pda idx
	in_pda_idx = p10_pda_idx.pda_name.notnull()
	p10_pda_idx.loc[in_pda_idx,'idx'] = p10_pda_idx.loc[in_pda_idx,'idx'].apply(lambda x: str(int(x)))
	p10_pda_idx.loc[in_pda_idx,'pda_id_pba50'] = \
		p10_pda_idx.loc[in_pda_idx,'jurisdiction'] + p10_pda_idx.loc[in_pda_idx,'idx']

	logger.info(p10_pda_idx.head())
	logger.info('Export {:,} rows to p10_pda_idx'.format(len(p10_pda_idx)))
	logger.info('{:,} unique PARCEL_IDs'.format(len(p10_pda_idx.PARCEL_ID.unique())))
	p10_pda_idx.to_csv(os.path.join(WORK_DIR, today+'_p10_pda_idx.csv'),index = False) 

	# Simple stats
	logger.info('Number of PDAs by Jurisdiction:')
	pda_count_juris = pdas.groupby(['jurisdiction'])['pda_name'].count().reset_index()
	pda_count_juris.rename(columns = {'pda_name':'pda_count'}, inplace = True)
	logger.info(pda_count_juris)
	pda_count_juris.to_csv(os.path.join(WORK_DIR, today+'_pda_count_juris.csv'),index = False)

	logger.info('Parcels Acreage by PDAs:')
	p10_acr_pda = p10_pda_idx.groupby(['county','jurisdiction','pda_name'])['ACRES'].sum().reset_index()
	logger.info(p10_acr_pda)
	p10_acr_pda.to_csv(os.path.join(WORK_DIR, today+'_p10_acr_pda.csv'),index = False)

	# double check data quality before export
	logger.info('Double check total number of PDAs:')
	logger.info(pda_count_juris['pda_count'].sum())

	# export to Urbansim input
	pda_id_2020 = p10_pda_idx[['PARCEL_ID','pda_id_pba50']]
	pda_id_2020.rename(columns = {'pda_id_pba50':'pda_id',
	                              'PARCEL_ID':   'parcel_id'}, inplace = True)
	logger.info(pda_id_2020.head())
	pda_id_2020.to_csv(os.path.join(WORK_DIR, 'pda_id_2020.csv'), index = False)



	## p10 PARCEL_ID - TRA_ID index
	pba50_attr_file = os.path.join(PBA50_PARCEL_GEO_DIR, '2020_04_17_parcels_geography.csv')

	pba50_tra_cols = ['PARCEL_ID','tra_id','juris']
	pba50_tra = pd.read_csv(pba50_attr_file,
	                        usecols = pba50_tra_cols)
	pba50_tra.rename(columns = {'PARCEL_ID': 'parcel_id'}, inplace = True)

	tra_id = pd.DataFrame({'tra_id':['tra3', 'tra2', 'tra1', 'tra3c2', 'tra2c1', 'tra3c1'], 
	                       '20_22' :['tra3', 'tra2', 'tra1', 'tra3',   'tra2',   'tra3'  ], 
	                       '23'    :['tra3', 'tra2', 'tra1', 'tra2',   'tra1',   'tra1'  ]})

	pba50_tra = pba50_tra.merge(tra_id, on = 'tra_id', how = 'left')
	in_tra_idx = pba50_tra.tra_id.notnull()

	pba50_tra_noCrossing = pba50_tra[['parcel_id','juris','20_22']]
	pba50_tra_noCrossing.rename(columns = {'20_22': 'tra_id'}, inplace = True)
	pba50_tra_noCrossing.loc[in_tra_idx,'juris_tra'] = \
		pba50_tra_noCrossing.loc[in_tra_idx,'juris'] + '_' + pba50_tra_noCrossing.loc[in_tra_idx,'tra_id']
	pba50_tra_noCrossing.drop(columns = ['juris'], inplace = True)
	logger.info(pba50_tra_noCrossing.head())

	pba50_tra_crossing = pba50_tra[['parcel_id','juris','23']]
	pba50_tra_crossing.rename(columns = {'23': 'tra_id'}, inplace = True)
	pba50_tra_crossing.loc[in_tra_idx,'juris_tra'] = \
		pba50_tra_crossing.loc[in_tra_idx,'juris'] + '_' + pba50_tra_crossing.loc[in_tra_idx,'tra_id']
	pba50_tra_crossing.drop(columns = ['juris'], inplace = True)
	logger.info(pba50_tra_crossing.head())

	pba50_tra_noCrossing.to_csv(os.path.join(WORK_DIR, 'tra_id_2020_s202122.csv'), index = False)
	pba50_tra_crossing.to_csv(os.path.join(WORK_DIR, 'tra_id_2020_s23.csv'), index = False)



	## p10 PARCEL_ID - HRA_ID index
	pba50_hra_cols = ['PARCEL_ID','sesit_id','juris']
	pba50_hra = pd.read_csv(pba50_attr_file,
	                        usecols = pba50_hra_cols)
	pba50_hra.rename(columns = {'PARCEL_ID': 'parcel_id'}, inplace = True)
	in_hra_idx = pba50_hra.sesit_id.notnull()
	pba50_hra.loc[in_hra_idx, 'juris_sesit'] = \
		pba50_hra.loc[in_hra_idx, 'juris'] + '_' + pba50_hra.loc[in_hra_idx, 'sesit_id']
	pba50_hra.drop(columns = ['juris'], inplace = True)
	logger.info(pba50_hra.head())
	pba50_hra.to_csv(os.path.join(WORK_DIR, 'hra_id_2020.csv'), index = False)