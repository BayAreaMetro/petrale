#
# Create 2015 tazdata map from UrbanSim input layer(s) using building data and pipeline data
# 
# Notes:
#  - zone_id and county/county_id aren't always consistent with the TM mapping between zones/county
#    (https://github.com/BayAreaMetro/travel-model-one/blob/master/utilities/geographies/taz-superdistrict-county.csv)
#    This script assumes the zone_id is accurate and pull the county from the TM correspondence file
#    TODO: report on these?
#
# for arcpy:
# set PATH=C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3

import logging,os,sys,time
import numpy, pandas

NOW = time.strftime("%Y%b%d.%H%M")

# taz-county file
TAZ_COUNTY_FILE       = "X:\\travel-model-one-master\\utilities\\geographies\\taz-superdistrict-county.csv"

# taz shapefile
TAZ_SHPFILE = "M:\\Data\\GIS layers\\TM1_taz\\bayarea_rtaz1454_rev1_WGS84.shp"


# reference for creation: 
# Create and share 2015 tazdata from basemap plus development pipeline with MTC planners @
#   https://app.asana.com/0/385259290425521/1165636787387665/f
if os.getenv("USERNAME")=="lzorn":
    # use local dir to make things faster
    URBANSIM_LOCAL_DIR    = "C:\\Users\\lzorn\\Documents\\UrbanSim_InputMapping"
    # from https://mtcdrive.box.com/s/w0fmrz85l9cti2byd6rjqu9hv0m2edlq
    URBANSIM_BASEMAP_FILE = "2020_03_20_bayarea_v6.h5"
    # from https://mtcdrive.box.com/s/wcxlgwov5l6s6p0p0vh2xj1ekdynxxw5
    URBANSIM_PIPELINE_FILE= "pipeline_2020Mar20.1512.csv"
    # employment data
    EMPLOYMENT_FILE       = "X:\\petrale\\applications\\travel_model_lu_inputs\\2015\\TAZ1454 2015 Land Use.csv"
    OUTPUT_DIR            = os.path.join(URBANSIM_LOCAL_DIR, "map_data")
    LOG_FILE              = os.path.join(OUTPUT_DIR, "create_tazdata_devpipeline_map_{}.log".format(NOW))

    # geodatabase for arcpy and map
    WORKSPACE_GDB         = "C:\\Users\\lzorn\\Documents\\UrbanSim_InputMapping\\UrbanSim_InputMapping.gdb"
    ARCGIS_PROJECT        = "C:\\Users\\lzorn\\Documents\\UrbanSim_InputMapping\\UrbanSim_InputMapping.aprx"

# year buit categories we care about
#          name,  min, max
YEAR_BUILT_CATEGORIES = [
    ("0000-2000",   0,2000),
    ("2001-2010",2001,2010),
    ("2011-2015",2011,2015),
    ("2016-2020",2016,2020),
    ("2021-2030",2021,2030),
    ("2031-2050",2031,2050),
]
# aggregate
YEAR_BUILD_CATEGORIES_AGG = [
    ("0000-2015",   0,2015),
    ("2016-2050",2016,2050),
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
    # set year_built_category, year_built_category_agg columns based on YEAR_BUILT_CATEGORIES and year_built column
    df["year_built_category"] = "????-????"
    for category in YEAR_BUILT_CATEGORIES:
        CAT_NAME = category[0]
        YEAR_MIN = category[1]
        YEAR_MAX = category[2]

        df.loc[(df.year_built >= YEAR_MIN)&(df.year_built <= YEAR_MAX), "year_built_category"] = CAT_NAME

    df["year_built_category_agg"] = "????-????"
    for category in YEAR_BUILD_CATEGORIES_AGG:
        CAT_NAME = category[0]
        YEAR_MIN = category[1]
        YEAR_MAX = category[2]

        df.loc[(df.year_built >= YEAR_MIN)&(df.year_built <= YEAR_MAX), "year_built_category_agg"] = CAT_NAME

    return df

def warn_zone_county_disagreement(df):
    # check if zone/county mapping disagree with the TM mapping and log issues
    # TODO
    pass

if __name__ == '__main__':
    # pandas options
    pandas.options.display.max_rows = 999

    if not os.path.exists(OUTPUT_DIR): os.mkdir(OUTPUT_DIR)

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
    tm_lu_df = pandas.read_csv(EMPLOYMENT_FILE)
    logger.info("Read {}; head:\n{}".format(EMPLOYMENT_FILE, tm_lu_df.head()))
    tm_lu_df.rename(columns={"ZONE":"zone_id"}, inplace=True)
    # keep only employment, tothh, totpop, hhpop
    tm_lu_df = tm_lu_df[["zone_id","TOTHH","TOTPOP","HHPOP","TOTEMP","RETEMPN","FPSEMPN","HEREMPN","AGREMPN","MWTEMPN","OTHEMPN"]]

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
    buildings_zone_btype_df = buildings_df.groupby(["zone_id","year_built_category_agg","year_built_category","building_type"]).agg(
                                {"residential_units"   :"sum",
                                 "building_sqft"       :"sum",
                                 "residential_sqft"    :"sum",
                                 "non_residential_sqft":"sum"})
    buildings_zone_btype_df.reset_index(inplace=True)
    buildings_zone_btype_df["source"] = "buildings"
    # reorder
    buildings_zone_btype_df = buildings_zone_btype_df[["zone_id","source",
        "year_built_category_agg","year_built_category","building_type",
        "residential_units","building_sqft","residential_sqft","non_residential_sqft"]]

    logger.info("buildings_zone_btype_df.head():\n{}".format(buildings_zone_btype_df.head()))
    logger.info("buildings_zone_btype_df.dtypes:\n{}".format(buildings_zone_btype_df.dtypes))

    #### sum to zone by year_built_category and NOT building_type: residential_units, residential_sqft, non_residential_sqft
    buildings_zone_df = buildings_df.groupby(["zone_id","year_built_category_agg","year_built_category"]).agg(
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
    logger.info("pipeline_df by year_built_category_agg:\n{}".format(pipeline_df["year_built_category_agg"].value_counts()))
    #logger.info("pipeline_df with unknown year_built_category:\n{}".format(
    #      pipeline_df.loc[pipeline_df.year_built_category=="unknown"]))

    # sum to zone by year_built_category and building_type
    # assume residential_sqft = building_sqft - non_residential_sqft
    pipeline_df["residential_sqft"] = pipeline_df["building_sqft"] - pipeline_df["non_residential_sqft"]

    #### sum to zone by year_built_category and building_type: residential_units, residential_sqft, non_residential_sqft
    pipeline_zone_btype_df = pipeline_df.groupby(["ZONE_ID","year_built_category_agg","year_built_category","building_type"]).agg(
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
    pipeline_zone_df = pipeline_df.groupby(["ZONE_ID","year_built_category_agg","year_built_category"]).agg(
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

    # pivot on buildings/pipeline including ALL building types
    zone_piv_agg_df = zone_df.pivot_table(index  ="zone_id",
                                          columns=["source","year_built_category_agg","building_type"],
                                          values =["residential_units", "building_sqft", "residential_sqft", "non_residential_sqft"])
    logger.info("zone_piv_agg_df.head():\n{}".format(zone_piv_agg_df.head()))
    zone_piv_agg_df.reset_index(inplace=True)

    # convert column names from tuples
    new_cols = []
    for col in zone_piv_agg_df.columns.values:
        if col[1] == '':  # ('zone_id', '', '', '')
            new_cols.append(col[0])
        else: # ('building_sqft', 'buildings', '0000-2000', 'HM')
            new_cols.append(col[1]+" "+col[2]+" "+col[3]+" "+col[0])
    zone_piv_agg_df.columns = new_cols
    logger.debug("zone_piv_agg_df.head():\n{}".format(zone_piv_agg_df.head()))
    logger.debug("zone_piv_agg_df.dtypes:\n{}".format(zone_piv_agg_df.dtypes))
    logger.debug("zone_piv_agg_df.sum():\n{}".format(zone_piv_agg_df.sum()))

    # merge zone_piv_df and zone_piv_agg_df
    zone_piv_df = pandas.merge(left=zone_piv_df, right=zone_piv_agg_df, left_on="zone_id", right_on="zone_id", how="outer")

    # drop columns with zero sums
    # drop_cols = []
    # for col in zone_piv_df.columns.values:
    #     if zone_piv_df[col].sum() == 0: drop_cols.append(col)
    # logger.info("Dropping {} columns with zero sums".format(len(drop_cols)))
    # logger.debug("{}".format(drop_cols))
    # zone_piv_df.drop(columns=drop_cols, inplace=True)

    # keep only these
    keep_columns = ["zone_id","source",
        # 2015 HU count
        "buildings 0000-2015 all residential_units",
        # 2015 Commercial Square Feet
        "buildings 0000-2015 all non_residential_sqft",

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

        "pipeline 2016-2050 HS residential_units",
        "pipeline 2016-2050 HT residential_units",
        "pipeline 2016-2050 HM residential_units",
        "pipeline 2016-2050 MR residential_units",
        "pipeline 2016-2050 all residential_units",

        # commercial Square Feet Built From 2016
        "pipeline 2016-2020 all non_residential_sqft",
        "pipeline 2021-2030 all non_residential_sqft",
        "pipeline 2031-2050 all non_residential_sqft",
        "pipeline 2016-2050 all non_residential_sqft",      
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
    # and employment
    zone_piv_df = pandas.merge(left=zone_piv_df, right=tm_lu_df, how="outer")

    # and 2015 HU Density
    zone_piv_df["HU Density 2015"] = zone_piv_df["buildings 0000-2015 all residential_units"]/zone_piv_df["parcel_acres"]
    zone_piv_df.loc[ zone_piv_df["parcel_acres"] == 0, "HU Density 2015" ] = 0.0

    # and 2015 Employee Density
    zone_piv_df["Employee Density 2015"] = zone_piv_df["TOTEMP"]/zone_piv_df["parcel_acres"]
    zone_piv_df.loc[ zone_piv_df["parcel_acres"] == 0, "Employee Density 2015" ] = 0.0

    # 2015 Commercial Square Feet per Employee
    zone_piv_df["Commercial Square Feet per Employee 2015"] = zone_piv_df["buildings 0000-2015 all non_residential_sqft"]/zone_piv_df["TOTEMP"]
    zone_piv_df.loc[ zone_piv_df["TOTEMP"] == 0, "Commercial Square Feet per Employee 2015"] = 0.0

    # zone pivot: add county/superdistrict
    zone_piv_df = pandas.merge(left=zone_piv_df, right=taz_sd_county_df, how="outer")
    logger.info("zone_piv_df.head():\n{}".format(zone_piv_df.head()))

    # write zone_piv_df
    zone_piv_file = os.path.join(OUTPUT_DIR, "urbansim_input_zonedata_pivot.csv")
    zone_piv_df.to_csv(zone_piv_file, index=False)
    logger.info("Wrote {}".format(zone_piv_file))

    # for tableau, let's not pivot, and let's not keep the all btypes
    zone_df = pandas.concat([buildings_zone_btype_df, pipeline_zone_btype_df], axis="index")

    # zone: add county/superdistrict
    zone_df = pandas.merge(left=zone_df, right=taz_sd_county_df, how="outer")
    logger.info("zone_piv_df.head():\n{}".format(zone_piv_df.head()))

    # write zone_df
    zone_file = os.path.join(OUTPUT_DIR, "urbansim_input_zonedata.csv")
    zone_df.to_csv(zone_file, index=False)
    logger.info("Wrote {}".format(zone_file))

    logger.info("importing arcpy....")
    import arcpy
    arcpy.env.workspace = WORKSPACE_GDB

    # bring in binary of zone_piv_df since arcpy mangles csv datatypes
    zone_piv_table = "urbansim_input_zonedata_pivot"
    try:     arcpy.Delete_management(zone_piv_table)
    except:  pass

    logger.info("Converting zone_piv_df to arcpy table {}".format(zone_piv_table))
    zone_piv_nparr = numpy.array(numpy.rec.fromrecords(zone_piv_df.values))
    zone_piv_nparr.dtype.names = tuple(zone_piv_df.dtypes.index.tolist())
    arcpy.da.NumPyArrayToTable(zone_piv_nparr, os.path.join(WORKSPACE_GDB, zone_piv_table))

    # create join layer with tazdata and zone_file
    logger.info("Joining {} with {}".format(TAZ_SHPFILE, zone_piv_file))
    taz_zone_pivot_table = arcpy.AddJoin_management(TAZ_SHPFILE, "TAZ1454", 
                                                    os.path.join(WORKSPACE_GDB, zone_piv_table), "zone_id")

    # save it as a feature class -- delete one if it already exists first
    zone_piv_featureclass = "taz_urbansim_input"
    try:    arcpy.Delete_management(zone_piv_featureclass)
    except: pass

    logger.info("Saving it as {}".format(zone_piv_featureclass))
    arcpy.CopyFeatures_management(taz_zone_pivot_table, zone_piv_featureclass)

    # set metadata
    logger.info("Setting featureclass metadata")

    # aprx = arcpy.mp.ArcGISProject(ARCGIS_PROJECT)
    # for m in aprx.listMaps():
    #     logger.debug("Map: {}".format(m.name))
    # for lyt in aprx.listLayouts():
    #     logger.debug("Layout: {}".format(lyt.name))
    # aprx.save()

    new_metadata = arcpy.metadata.Metadata()
    new_metadata.title = "UrbanSim input"
    new_metadata.summary = "Data derived from UrbanSim Basemap and Development Pipeline for review"
    new_metadata.description = \
        "Basemap source: {}\n".format(URBANSIM_BASEMAP_FILE) + \
        "Pipeline source: {}\n".format(URBANSIM_PIPELINE_FILE) + \
        "Employment source: {}\n".format(EMPLOYMENT_FILE)
    new_metadata.credits = "create_tazdata_devpipeline_map.py"

    zone_piv_fc_metadata = arcpy.metadata.Metadata(zone_piv_featureclass)
    logger.debug("feature class metadata isReadOnly? {}".format(zone_piv_fc_metadata.isReadOnly))
    zone_piv_fc_metadata.copy(new_metadata)
    zone_piv_fc_metadata.save()

    logger.info("Complete")