USAGE="""

  Calculates share households in different TAZ subzones for each TM1454 TAZ
  See asana task: https://app.asana.com/0/403262763383022/1161734609745564/f

"""

import numpy,pandas
import argparse, os, sys, time

BLUEPRINT_DIR           = "M:\Data\Urban\BAUS\PBA50\Draft_Blueprint"
LARGE_DATASET_INPUT_DIR = os.path.join(BLUEPRINT_DIR, "Large General Input Data")
PARCEL_TO_SUBZONE_FILE  = os.path.join(LARGE_DATASET_INPUT_DIR, '2018_10_17_parcel_to_taz1454sub.csv')

URBANSIM_RUN_DIR        = os.path.join(BLUEPRINT_DIR, 'runs')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=USAGE, formatter_class=argparse.RawDescriptionHelpFormatter,)
    parser.add_argument("parcel_data_file", help='Parcel data file relative to "{}". e.g. "Blueprint Plus Crossing (s23)\\v1.5.5\\run998_parcel_data_2050.csv"'.format(URBANSIM_RUN_DIR))
    parser.add_argument("output_file",      help='Output file')
    args = parser.parse_args()

    pandas.set_option('max_columns',   200)
    pandas.set_option('display.width', 200)

    parcel_data_file     = os.path.join(URBANSIM_RUN_DIR, args.parcel_data_file)
    print(" {:20}: {}".format("parcel_data_file", parcel_data_file))
    print(" {:20}: {}".format("output_file",      args.output_file))

    parcel_to_subzone_df = pandas.read_csv(PARCEL_TO_SUBZONE_FILE)
    print('Read {} rows from {}; head:\n{}'.format(len(parcel_to_subzone_df), PARCEL_TO_SUBZONE_FILE, parcel_to_subzone_df.head()))
    # make PARCEL_ID and ZONE_ID an int rather than a float
    parcel_to_subzone_df['PARCEL_ID'] = parcel_to_subzone_df['PARCEL_ID'].round(0).astype(numpy.int64)
    parcel_to_subzone_df['ZONE_ID'  ] = parcel_to_subzone_df['ZONE_ID'  ].round(0).astype(numpy.int64)
    print(parcel_to_subzone_df.dtypes)

    parcel_data_df       = pandas.read_csv(parcel_data_file)
    parcel_data_df = parcel_data_df[['parcel_id','tothh']]

    print('Read {} rows from {}; head:\n{}'.format(len(parcel_data_df), parcel_data_file, parcel_data_df.head()))
    # filter to parcels with notnull(tothh) and tothh > 0
    parcel_data_df = parcel_data_df.loc[pandas.notnull(parcel_data_df['tothh'])&(parcel_data_df['tothh']>0), ]
    print("Filtered to {} rows with tothh>0".format(len(parcel_data_df)))
    print(parcel_data_df.head())

    # join
    parcel_data_df = pandas.merge(left=parcel_data_df, right=parcel_to_subzone_df, how="left", left_on="parcel_id", right_on="PARCEL_ID")
    print("After merge, parcel_data_df.head():\n{}".format(parcel_data_df.head()))

    # summarize to taz and subzone
    taz_subzone_hh = parcel_data_df.groupby(['ZONE_ID','subzone']).agg({'tothh':'sum'}).reset_index()
    # pivot subzone to column
    taz_subzone_hh = taz_subzone_hh.pivot(index='ZONE_ID', columns='subzone', values='tothh').reset_index()
    taz_subzone_hh.fillna(0, inplace=True)
    # subzone  ZONE_ID      a    b    c
    # 0            1.0   55.0  0.0  0.0
    # 1            2.0  364.0  0.0  0.0
    # 2            3.0  358.0  0.0  0.0
    # 3            4.0  398.0  0.0  0.0
    # 4            5.0  702.0  0.0  0.0
    taz_subzone_hh['tothh'] = taz_subzone_hh['a'] + taz_subzone_hh['b'] + taz_subzone_hh['c']

    # see mapping here: https://github.com/BayAreaMetro/bayarea_urbansim/blob/9f40b58b731a2cb956543948b7bcba74ba1532e9/baus/datasources.py#L511
    # a = short walk
    # b = long walk
    # c = no walk
    taz_subzone_hh['SHRT'] = taz_subzone_hh['a']/taz_subzone_hh['tothh']
    taz_subzone_hh['LONG'] = taz_subzone_hh['b']/taz_subzone_hh['tothh']
    taz_subzone_hh['NONE'] = taz_subzone_hh['c']/taz_subzone_hh['tothh']
    taz_subzone_hh['TAZ']  = taz_subzone_hh['ZONE_ID'].astype(int)
    print(taz_subzone_hh.head()) 

    taz_subzone_hh[['TAZ','SHRT','LONG']].to_csv(args.output_file, index=False, float_format='%.2f')
    print("Wrote {} rows to {}".format(len(taz_subzone_hh), args.output_file))

    # save unpivoted for tableau
    taz_subzone_hh_unpivot = pandas.melt(taz_subzone_hh, id_vars=['TAZ'], value_vars=['SHRT','LONG','NONE'], value_name="share")
    print("taz_subzone_hh_unpivot.head():\n{}".format(taz_subzone_hh_unpivot.head()))
 
    unpivot_file = args.output_file.replace(".csv","_unpivot.csv")
    taz_subzone_hh_unpivot.to_csv(unpivot_file, index=False, float_format='%.2f')
    print("Wrote {} rows to {}".format(len(taz_subzone_hh_unpivot), unpivot_file))
