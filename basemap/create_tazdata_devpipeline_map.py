#
# Create 2015 tazdata map from UrbanSim input layer(s) using building data and pipeline data
# 
# Notes:
#  - zone_id and county/county_id aren't always consistent with the TM mapping between zones/county
#    (https://github.com/BayAreaMetro/travel-model-one/blob/master/utilities/geographies/taz-superdistrict-county.csv)
#    This script assumes the zone_id is accurate and pull the county from the TM correspondence file
#    TODO: report on these?

import logging,os,sys,time
import pandas

NOW = time.strftime("%Y%b%d.%H%M")

# reference for creation: 
# Create and share 2015 tazdata from basemap plus development pipeline with MTC planners @
#   https://app.asana.com/0/385259290425521/1165636787387665/f
if os.getenv("USERNAME")=="lzorn":
    URBANSIM_LOCAL_DIR    = "C:\\Users\\lzorn\\Documents\\UrbanSim smelt"
    # from https://mtcdrive.box.com/s/w0fmrz85l9cti2byd6rjqu9hv0m2edlq
    URBANSIM_BASEMAP_FILE = "2020_03_20_bayarea_v6.h5"
    # from https://mtcdrive.box.com/s/wcxlgwov5l6s6p0p0vh2xj1ekdynxxw5
    URBANSIM_PIPELINE_FILE= "pipeline_2020Mar20.1512.csv"
    # taz-county file
    TAZ_COUNTY_FILE       = "X:\\travel-model-one-master\\utilities\\geographies\\taz-superdistrict-county.csv"
    OUTPUT_DIR            = os.path.join(URBANSIM_LOCAL_DIR, URBANSIM_BASEMAP_FILE[:-3])
    LOG_FILE              = os.path.join(OUTPUT_DIR, "create_tazdata_devpipelie_map_{}.log".format(NOW))

# year buit categories we care about
#          name,  min, max
YEAR_BUILT_CATEGORIES = [
    ("0000-2000",   0,2000),
    ("2001-2010",2001,2010),
    ("2011-2015",2011,2015),
    ("2016-2020",2016,2020),
    ("2021-2030",2021,2030),
    ("2030-2050",2031,2050)
 ]

COUNTY_ID_NAME = [
    ("Alameda"      , 1),
    ("Contra Costa" ,13),
    ("Marin"        ,41),
    ("Napa"         ,55),
    ("San Francisco",75),
    ("San Mateo"    ,81),
    ("Santa Clara"  ,85),
    ("Solano"       ,95),
    ("Sonoma"       ,97),
]
COUNTY_ID_NAME_DF = pandas.DataFrame(COUNTY_ID_NAME, columns=["county","county_id"])

def set_year_built_category(df):
    # set year_built_category column based on YEAR_BUILT_CATEGORIES and year_built column
    df["year_built_category"] = "????-????"
    for category in YEAR_BUILT_CATEGORIES:
        CAT_NAME = category[0]
        YEAR_MIN = category[1]
        YEAR_MAX = category[2]

        df.loc[(df.year_built >= YEAR_MIN)&(df.year_built <= YEAR_MAX), "year_built_category"] = CAT_NAME
    return df

def warn_zone_county_disagreement(df):
    # check if zone/county mapping disagree with the TM mapping and log issues
    # TODO
    pass

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

    logger.info("Output dir: {}".format(OUTPUT_DIR))
    if not os.path.exists(OUTPUT_DIR): os.mkdir(OUTPUT_DIR)

    ####################################
    taz_sd_county_df = pandas.read_csv(TAZ_COUNTY_FILE)
    logger.info("Read {}; head:\n{}".format(TAZ_COUNTY_FILE, taz_sd_county_df.head()))
    # let's just keep taz/county
    taz_sd_county_df = taz_sd_county_df[["ZONE","COUNTY_NAME", "SD_NAME", "SD_NUM_NAME"]]
    taz_sd_county_df.rename(columns={"ZONE":"zone_id", "COUNTY_NAME":"county"},inplace=True)
    # and county_id
    taz_sd_county_df = pandas.merge(left=taz_sd_county_df, right=COUNTY_ID_NAME_DF)
    logger.debug("taz_sd_county_df head:\n{}".format(taz_sd_county_df.head()))

    ####################################
    logger.info("Reading parcels and buildings from {}".format(os.path.join(URBANSIM_LOCAL_DIR, URBANSIM_BASEMAP_FILE)))

    # use this for parcel_id (index), county_id, zone_id, acres
    parcels_df   = pandas.read_hdf(os.path.join(URBANSIM_LOCAL_DIR, URBANSIM_BASEMAP_FILE), key='parcels')
    # logger.info(parcels_df.dtypes)
    parcels_df = parcels_df[["zone_id","acres"]].reset_index().rename(columns={"acres":"parcel_acres"})
    logger.info("parcels_df.head():\n{}".format(parcels_df.head()))

    # sum parcel acres to zone
    parcels_zone_df = parcels_df.groupby(["zone_id"]).agg({"parcel_acres":"sum"}).reset_index()
    logger.info("parcels_zone_df:\n{}".format(parcels_zone_df.head()))

    buildings_df = pandas.read_hdf(os.path.join(URBANSIM_LOCAL_DIR, URBANSIM_BASEMAP_FILE), key='buildings')
    logger.info("buildings_df.dtypes:\n{}".format(buildings_df.dtypes))
    #logger.info(buildings_df.head())

    # segment year buit to 0000-2000, 2001-2010, 2011-2015
    buildings_df = set_year_built_category(buildings_df)
    logger.info("buildings_df by year_built_category:\n{}".format(buildings_df["year_built_category"].value_counts()))

    # join buildings to parcel to get the zone
    buildings_df = pandas.merge(left=buildings_df, right=parcels_df[["parcel_id","zone_id"]], 
                                how="left", left_on=["parcel_id"], right_on=["parcel_id"])

    #### sum to zone by year_built_category and building_type: residential_units, residential_sqft, non_residential_sqft
    buildings_zone_btype_df = buildings_df.groupby(["zone_id","year_built_category","building_type"]).agg(
                                {"residential_units"   :"sum",
                                 "building_sqft"       :"sum",
                                 "residential_sqft"    :"sum",
                                 "non_residential_sqft":"sum"})
    buildings_zone_btype_df.reset_index(inplace=True)
    buildings_zone_btype_df["source"] = "buildings"
    # reorder
    buildings_zone_btype_df = buildings_zone_btype_df[["zone_id","source",
        "year_built_category","building_type",
        "residential_units","building_sqft","residential_sqft","non_residential_sqft"]]

    logger.info("buildings_zone_btype_df.head():\n{}".format(buildings_zone_btype_df.head()))
    logger.info("buildings_zone_btype_df.dtypes:\n{}".format(buildings_zone_btype_df.dtypes))

    #### sum to zone by year_built_category and NOT building_type: residential_units, residential_sqft, non_residential_sqft
    buildings_zone_df = buildings_df.groupby(["zone_id","year_built_category"]).agg(
                                {"residential_units"   :"sum",
                                 "building_sqft"       :"sum",
                                 "residential_sqft"    :"sum",
                                 "non_residential_sqft":"sum"})
    buildings_zone_df.reset_index(inplace=True)
    buildings_zone_df["source"] = "buildings"
    buildings_zone_df["building_type"] = "all"

    # reorder
    buildings_zone_df = buildings_zone_df[list(buildings_zone_btype_df.columns.values)]

    logger.info("buildings_zone_df.head():\n{}".format(buildings_zone_df.head()))
    logger.info("buildings_zone_df.dtypes:\n{}".format(buildings_zone_df.dtypes))

    ####################################
    # read pipeline file
    logger.info("Reading pipeline from {}".format(os.path.join(URBANSIM_LOCAL_DIR, URBANSIM_PIPELINE_FILE)))
    pipeline_df = pandas.read_csv(os.path.join(URBANSIM_LOCAL_DIR, URBANSIM_PIPELINE_FILE))
    logger.info("pipeline_df.head():\n{}".format(pipeline_df.head()))
    logger.info("pipeline_df.dtypes:\n{}".format(pipeline_df.dtypes))
    # logger.info("pipeline_df by year_built:\n{}".format(pipeline_df["year_built"].value_counts()))
    pipeline_df = set_year_built_category(pipeline_df)
    logger.info("pipeline_df by year_built_category:\n{}".format(pipeline_df["year_built_category"].value_counts()))
    #logger.info("pipeline_df with unknown year_built_category:\n{}".format(
    #      pipeline_df.loc[pipeline_df.year_built_category=="unknown"]))

    # sum to zone by year_built_category and building_type
    # assume residential_sqft = building_sqft - non_residential_sqft
    pipeline_df["residential_sqft"] = pipeline_df["building_sqft"] - pipeline_df["non_residential_sqft"]

    #### sum to zone by year_built_category and building_type: residential_units, residential_sqft, non_residential_sqft
    pipeline_zone_btype_df = pipeline_df.groupby(["ZONE_ID","year_built_category","building_type"]).agg(
                                {"residential_units"   :"sum",
                                 "building_sqft"       :"sum",
                                 "residential_sqft"    :"sum",
                                 "non_residential_sqft":"sum"})
    pipeline_zone_btype_df.reset_index(inplace=True)
    pipeline_zone_btype_df.rename(columns={"ZONE_ID":"zone_id"}, inplace=True)
    pipeline_zone_btype_df.loc[ pandas.isnull(pipeline_zone_btype_df.zone_id), "zone_id"] = 0 # null => 0
    pipeline_zone_btype_df.zone_id = pipeline_zone_btype_df.zone_id.astype(int)

    pipeline_zone_btype_df["source"] = "pipeline"
    pipeline_zone_btype_df = pipeline_zone_btype_df[list(buildings_zone_btype_df.columns)]
    logger.info("pipeline_zone_btype_df.head():\n{}".format(pipeline_zone_btype_df.head()))
    logger.info("pipeline_zone_btype_df.dtypes:\n{}".format(pipeline_zone_btype_df.dtypes))

    #### sum to zone by year_built_category and NOT building_type: residential_units, residential_sqft, non_residential_sqft
    pipeline_zone_df = pipeline_df.groupby(["ZONE_ID","year_built_category"]).agg(
                                {"residential_units"   :"sum",
                                 "building_sqft"       :"sum",
                                 "residential_sqft"    :"sum",
                                 "non_residential_sqft":"sum"})
    pipeline_zone_df.reset_index(inplace=True)
    pipeline_zone_df.rename(columns={"ZONE_ID":"zone_id"}, inplace=True)
    pipeline_zone_df.loc[ pandas.isnull(pipeline_zone_df.zone_id), "zone_id"] = 0 # null => 0
    pipeline_zone_df.zone_id = pipeline_zone_df.zone_id.astype(int)

    pipeline_zone_df["source"] = "pipeline"
    pipeline_zone_df["building_type"] = "all"
    pipeline_zone_df = pipeline_zone_df[list(buildings_zone_btype_df.columns)]
    logger.info("pipeline_zone_df.head():\n{}".format(pipeline_zone_df.head()))
    logger.info("pipeline_zone_df.dtypes:\n{}".format(pipeline_zone_df.dtypes))


    ####################################
    # take buildings & pipeline by zone
    zone_df = pandas.concat([buildings_zone_btype_df, 
                             buildings_zone_df,
                             pipeline_zone_btype_df,
                             pipeline_zone_df], axis="index")
    logger.info("zone_df.head():\n{}".format(zone_df.head()))

    # pivot on buildings/pipeline including ALL building types
    zone_piv_df = zone_df.pivot_table(index  ="zone_id",
                                      columns=["source","year_built_category","building_type"],
                                      values =["residential_units", "building_sqft", "residential_sqft", "non_residential_sqft"])
    logger.info("zone_piv_df.head():\n{}".format(zone_piv_df.head()))
    zone_piv_df.reset_index(inplace=True)

    # convert column names from tuples
    new_cols = []
    for col in zone_piv_df.columns.values:
        if col[1] == '':  # ('zone_id', '', '', '')
            new_cols.append(col[0])
        else: # ('building_sqft', 'buildings', '0000-2000', 'HM')
            new_cols.append(col[1]+" "+col[2]+" "+col[3]+" "+col[0])
    zone_piv_df.columns = new_cols
    logger.debug("zone_piv_df.head():\n{}".format(zone_piv_df.head()))
    logger.debug("zone_piv_df.dtypes:\n{}".format(zone_piv_df.dtypes))
    logger.debug("zone_piv_df.sum():\n{}".format(zone_piv_df.sum()))

    # drop columns with zero sums
    # drop_cols = []
    # for col in zone_piv_df.columns.values:
    #     if zone_piv_df[col].sum() == 0: drop_cols.append(col)
    # logger.info("Dropping {} columns with zero sums".format(len(drop_cols)))
    # logger.debug("{}".format(drop_cols))
    # zone_piv_df.drop(columns=drop_cols, inplace=True)

    # keep only these
    keep_columns = ["zone_id","source",
        # residential untils built from 2016 on
        "pipeline 2016-2020 HS residential_units",
        "pipeline 2016-2020 HT residential_units",
        "pipeline 2016-2020 HM residential_units",
        "pipeline 2016-2020 MR residential_units",
        "pipeline 2016-2020 all residential_units",

        "pipeline 2021-2030 HS residential_units",
        "pipeline 2021-2030 HT residential_units",
        "pipeline 2021-2030 HM residential_units",
        "pipeline 2021-2030 MR residential_units",
        "pipeline 2021-2030 all residential_units",

        "pipeline 2031-2050 HS residential_units",
        "pipeline 2031-2050 HT residential_units",
        "pipeline 2031-2050 HM residential_units",
        "pipeline 2031-2050 MR residential_units",
        "pipeline 2031-2050 all residential_units",

        # commercial Square Feet Built From 2016
        "pipeline 2016-2020 all non_residential_sqft",
        "pipeline 2021-2030 all non_residential_sqft",
        "pipeline 2031-2050 all non_residential_sqft",        
    ]
    # but only if they exist
    keep_columns_present = []
    for col in keep_columns: 
        if col in list(zone_piv_df.columns.values): keep_columns_present.append(col)
    zone_piv_df = zone_piv_df[keep_columns_present]
    # fill na with zero
    zone_piv_df.fillna(value=0, inplace=True)

    logger.info("zone_piv_df.dtypes:\n{}".format(zone_piv_df.dtypes))

    # add parcel acres
    zone_piv_df = pandas.merge(left=zone_piv_df, right=parcels_zone_df, how="outer")

    # zone pivot: add county/superdistrict
    zone_piv_df = pandas.merge(left=zone_piv_df, right=taz_sd_county_df, how="outer")
    logger.info("zone_piv_df.head():\n{}".format(zone_piv_df.head()))

    # write zone_piv_df
    zone_file = os.path.join(OUTPUT_DIR, "urbansim_input_zonedata_pivot.csv")
    zone_piv_df.to_csv(zone_file, index=False)
    logger.info("Wrote {}".format(zone_file))

    # for tableau, let's not pivot, and let's not keep the all btypes
    zone_df = pandas.concat([buildings_zone_btype_df, pipeline_zone_btype_df], axis="index")

    # zone: add county/superdistrict
    zone_df = pandas.merge(left=zone_df, right=taz_sd_county_df, how="outer")
    logger.info("zone_piv_df.head():\n{}".format(zone_piv_df.head()))

    # write zone_df
    zone_file = os.path.join(OUTPUT_DIR, "urbansim_input_zonedata.csv")
    zone_df.to_csv(zone_file, index=False)
    logger.info("Wrote {}".format(zone_file))