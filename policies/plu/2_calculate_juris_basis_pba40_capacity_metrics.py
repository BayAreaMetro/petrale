USAGE = """

  Given a set of p10 combined with pba40 and basis PLU/BOC data, creates a series of test hybrid configurations
  where all variables are set to use PBA40 values and one variable is set to use BASIS.

  The script then computes set of capacity metrics reflecting the PBA40 and BASIS values for that test variable, summarized by jurisdiction.
  For allowed development building types, a few other metrics are calculated to summarize:
   * number of parcels and number of parcel-acres for each permutation of the PBA40 vs BASIS value of that variable
   * number of parcels and number of parcel-acres for each permutation of allowed_res and/or allowed_nonres given the PBA40 vs BASIS value of that variable

  Input:  p10_plu_boc_allAttrs.csv, p10 combined with pba40 and basis boc data output by 1_PLU_BOC_data_combine.py
          buildings.csv, b10 building data
  Output: juris_basis_pba40_capacity_metrics.csv
          juris_basis_pba40_capacity_metrics.log
  In test mode (specified by --test), outputs files to cwd and without date prefix; otherwise, outputs to PLU_BOC_DIR with date prefix

"""

import pandas as pd
import numpy as np
import argparse, os, glob, logging, sys, time
import dev_capacity_calculation_module

NOW = time.strftime("%Y_%m%d_%H%M")
today = time.strftime("%Y_%m_%d")


if os.getenv("USERNAME") == "ywang":
    BOX_DIR = "C:\\Users\\{}\\Box\\Modeling and Surveys\\Urban Modeling\\Bay Area UrbanSim\\PBA50".format(
        os.getenv("USERNAME")
    )
    M_URBANSIM_DIR = "M:\\Data\\Urban\\BAUS\\PBA50"
    M_SMELT_DIR = "M:\\Data\\GIS layers\\UrbanSim smelt\\2020 03 12"
    GITHUB_PETRALE_DIR = "C:\\Users\\{}\\Documents\\GitHub\\petrale\\".format(
        os.getenv("USERNAME")
    )
elif os.getenv("USERNAME") == "lzorn":
    BOX_DIR = "C:\\Users\\{}\\Box\\Modeling and Surveys\\Urban Modeling\\Bay Area UrbanSim\\PBA50".format(
        os.getenv("USERNAME")
    )
    M_URBANSIM_DIR = "M:\\Data\\Urban\\BAUS\\PBA50"
    M_SMELT_DIR = "M:\\Data\\GIS layers\\UrbanSim smelt\\2020 03 12"
    GITHUB_PETRALE_DIR = "X:\\petrale"


# input file locations
PLU_BOC_M_DIR = os.path.join(M_URBANSIM_DIR, "Draft_Blueprint", "Base zoning", "output")
PLU_BOC_FILE = os.path.join(PLU_BOC_M_DIR, "2020_06_03_p10_plu_boc_allAttrs.csv")

# output file locations
PLU_BOC_BOX_DIR = os.path.join(BOX_DIR, "Policies", "Base zoning", "outputs")

# output file
# In test mode (specified by --test), outputs to cwd and without date prefix; otherwise, outputs to PLU_BOC_DIR with date prefix
JURIS_CAPACITY_FILE = "juris_basis_pba40_capacity_metrics.csv"
LOG_FILE = "juris_basis_pba40_capacity_metrics.log"


def countMissing(df, attr):
    null_attr_count = len(df.loc[df["{}_basis".format(attr)].isnull()])
    logger.info(
        "Number of parcels missing {}_basis info: {:,} or {:.1f}%".format(
            attr, null_attr_count, 100.0 * null_attr_count / len(df)
        )
    )


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=USAGE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--test", action="store_true", help="Test mode")
    args = parser.parse_args()

    if args.test == False:
        LOG_FILE = os.path.join(PLU_BOC_BOX_DIR, "{}_{}".format(today, LOG_FILE))
        JURIS_CAPACITY_FILE = os.path.join(
            PLU_BOC_BOX_DIR, "{}_{}".format(today, JURIS_CAPACITY_FILE)
        )

    pd.set_option("max_columns", 200)
    pd.set_option("display.width", 200)

    # create logger
    logger = logging.getLogger(__name__)
    logger.setLevel("DEBUG")

    # console handler
    ch = logging.StreamHandler()
    ch.setLevel("INFO")
    ch.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p"
        )
    )
    logger.addHandler(ch)
    # file handler
    fh = logging.FileHandler(LOG_FILE, mode="w")
    fh.setLevel("DEBUG")
    fh.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p"
        )
    )
    logger.addHandler(fh)

    logger.info("BOX_DIR             = {}".format(BOX_DIR))
    logger.info("JURIS_CAPACITY_FILE = {}".format(JURIS_CAPACITY_FILE))

    ## P10 parcels with pba40 plu and basis boc data
    plu_boc = pd.read_csv(PLU_BOC_FILE)
    logger.info("Read {:,} rows from {}".format(len(plu_boc), PLU_BOC_FILE))
    logger.info("\n{}".format(plu_boc.head()))

    ## B10 buildings with p10 parcels data
    basemap_b10_file = os.path.join(M_SMELT_DIR, "b10.csv")
    basemap_b10 = pd.read_csv(basemap_b10_file)
    # conver PARCEL_ID to integer:
    basemap_b10["parcel_id"] = basemap_b10["parcel_id"].apply(lambda x: int(round(x)))
    logger.info("Read {:,} rows from {}".format(len(basemap_b10), basemap_b10_file))
    logger.info("\n{}".format(basemap_b10.head()))
    logger.info(
        "Number of unique PARCEL_ID: {}".format(len(basemap_b10.parcel_id.unique()))
    )

    basemap_p10_file = os.path.join(M_SMELT_DIR, "p10.csv")
    basemap_p10 = pd.read_csv(
        basemap_p10_file, usecols=["PARCEL_ID", "geom_id_s", "ACRES", "LAND_VALUE"]
    )
    # conver PARCEL_ID to integer:
    basemap_p10["PARCEL_ID"] = basemap_p10["PARCEL_ID"].apply(lambda x: int(round(x)))
    logger.info("Read {:,} rows from {}".format(len(basemap_p10), basemap_p10_file))
    logger.info("\n{}".format(basemap_p10.head()))
    logger.info(
        "Number of unique PARCEL_ID: {}".format(len(basemap_p10.PARCEL_ID.unique()))
    )

    # join parcels to buildings which is used to determine current built-out condition when calculating net capacity
    building_parcel = pd.merge(
        left=basemap_b10,
        right=basemap_p10[["PARCEL_ID", "LAND_VALUE"]],
        left_on="parcel_id",
        right_on="PARCEL_ID",
        how="outer",
    )

    ## Create test hybrid indices on the fly, representing:
    #  What if we used PBA40 data for all fields and BASIS data for this one field
    #  How would that affect capacity for each jurisdiction?
    juris_df = dev_capacity_calculation_module.get_jurisdiction_county_df()

    # create all PBA40 hybrid idx to start
    pba40_juris_idx = juris_df.copy()
    pba40_juris_idx.set_index("juris_name", inplace=True)
    for dev_type in dev_capacity_calculation_module.ALLOWED_BUILDING_TYPE_CODES:
        # use PBA40 allowed dev type
        pba40_juris_idx[
            "{}_idx".format(dev_type)
        ] = dev_capacity_calculation_module.USE_PBA40
    for intensity in dev_capacity_calculation_module.INTENSITY_CODES:
        # use PBA40 max intensity
        pba40_juris_idx[
            "max_{}_idx".format(intensity)
        ] = dev_capacity_calculation_module.USE_PBA40
        # don't adjust
        pba40_juris_idx["proportion_adj_{}".format(intensity)] = 1.0

    capacity_metrics = pd.DataFrame()

    # for each attribute
    # construct hybrid index for testing -- e.g. use PBA40 idx for all columns, BASIS idx for this one
    for test_attr in (
        dev_capacity_calculation_module.ALLOWED_BUILDING_TYPE_CODES
        + dev_capacity_calculation_module.INTENSITY_CODES
    ):

        logger.info("======== Testing BASIS attribute {}".format(test_attr))
        # start with all PBA40 but use BASIS just for this
        test_hybrid_juris_idx = pba40_juris_idx.copy()
        if test_attr in dev_capacity_calculation_module.ALLOWED_BUILDING_TYPE_CODES:
            test_hybrid_juris_idx[
                "{}_idx".format(test_attr)
            ] = dev_capacity_calculation_module.USE_BASIS
        else:
            test_hybrid_juris_idx[
                "max_{}_idx".format(test_attr)
            ] = dev_capacity_calculation_module.USE_BASIS

        # apply the hybrid jurisdiction index to the parcel data
        test_hybrid_parcel_idx = (
            dev_capacity_calculation_module.create_hybrid_parcel_data_from_juris_idx(
                logger, plu_boc, test_hybrid_juris_idx
            )
        )

        # compute allowed development type - residential vs non-residential for each parcel
        test_hybrid_allow_dev_type = dev_capacity_calculation_module.set_allow_dev_type(
            test_hybrid_parcel_idx, boc_source="urbansim"
        )

        # put them together
        test_hybrid_parcel_idx = pd.merge(
            left=test_hybrid_parcel_idx,
            right=test_hybrid_allow_dev_type,
            how="left",
            on="PARCEL_ID",
        )

        # and join alongside the parcel data
        test_hybrid_parcel_idx = pd.merge(
            left=plu_boc,
            right=test_hybrid_parcel_idx,
            how="left",
            on=["PARCEL_ID", "juris_zmod"],
        )

        logger.debug(
            "test_hybrid_parcel_idx head(30):\n{}".format(
                test_hybrid_parcel_idx.head(30)
            )
        )

        # calculate capacity for PBA40 and BASIS test, where the BASIS test uses the "urbansim" index,
        # which is really a test of BASIS for this attribute only
        capacity_pba40 = dev_capacity_calculation_module.calculate_capacity(
            test_hybrid_parcel_idx, "pba40", "zmod", pass_thru_cols=["juris_zmod"]
        )
        capacity_basisTest = dev_capacity_calculation_module.calculate_capacity(
            test_hybrid_parcel_idx, "basis", "zmod", pass_thru_cols=["juris_zmod"]
        )

        logger.debug("capacity_pba40.head():\n{}".format(capacity_pba40.head()))
        logger.debug("capacity_basisTest.head():\n{}".format(capacity_basisTest.head()))

        # should we keep capacity cols based on test_attr?
        capacity_juris_pba40 = (
            capacity_pba40.groupby(["juris_zmod"])[
                ["zoned_du_pba40", "zoned_Ksqft_pba40", "job_spaces_pba40"]
            ]
            .sum()
            .reset_index()
        )
        capacity_juris_basisTest = (
            capacity_basisTest.groupby(["juris_zmod"])[
                ["zoned_du_basis", "zoned_Ksqft_basis", "job_spaces_basis"]
            ]
            .sum()
            .reset_index()
        )

        logger.debug(
            "capacity_juris_pba40.head():\n{}".format(capacity_juris_pba40.head())
        )
        logger.debug(
            "capacity_juris_basisTest.head():\n{}".format(
                capacity_juris_basisTest.head()
            )
        )

        # calculate net capacity
        net_capacity_pba40 = dev_capacity_calculation_module.calculate_net_capacity(
            logger,
            test_hybrid_parcel_idx,
            "pba40",
            "zmod",
            building_parcel,
            net_pass_thru_cols=["juris_zmod"],
        )
        net_capacity_basisTest = dev_capacity_calculation_module.calculate_net_capacity(
            logger,
            test_hybrid_parcel_idx,
            "basis",
            "zmod",
            building_parcel,
            net_pass_thru_cols=["juris_zmod"],
        )

        logger.debug("net_capacity_pba40.head():\n{}".format(net_capacity_pba40.head()))
        logger.debug(
            "net_capacity_basisTest.head():\n{}".format(net_capacity_basisTest.head())
        )

        net_capacity_juris_pba40 = (
            net_capacity_pba40.groupby(["juris_zmod"])[
                [
                    "zoned_du_vacant_pba40",
                    "zoned_Ksqft_vacant_pba40",
                    "job_spaces_vacant_pba40",
                    "zoned_du_underbuild_pba40",
                    "zoned_Ksqft_underbuild_pba40",
                    "job_spaces_underbuild_pba40",
                    "zoned_du_underbuild_noProt_pba40",
                    "zoned_Ksqft_underbuild_noProt_pba40",
                    "job_spaces_underbuild_noProt_pba40",
                ]
            ]
            .sum()
            .reset_index()
        )
        net_capacity_juris_basisTest = (
            net_capacity_basisTest.groupby(["juris_zmod"])[
                [
                    "zoned_du_vacant_basis",
                    "zoned_Ksqft_vacant_basis",
                    "job_spaces_vacant_basis",
                    "zoned_du_underbuild_basis",
                    "zoned_Ksqft_underbuild_basis",
                    "job_spaces_underbuild_basis",
                    "zoned_du_underbuild_noProt_basis",
                    "zoned_Ksqft_underbuild_noProt_basis",
                    "job_spaces_underbuild_noProt_basis",
                ]
            ]
            .sum()
            .reset_index()
        )

        logger.debug(
            "net_capacity_juris_pba40.head():\n{}".format(
                net_capacity_juris_pba40.head()
            )
        )
        logger.debug(
            "net_capacity_juris_basisTest.head():\n{}".format(
                net_capacity_juris_basisTest.head()
            )
        )

        # put them together and add variable name
        capacity_juris_pba40_basisTest = pd.merge(
            left=capacity_juris_pba40, right=capacity_juris_basisTest, on="juris_zmod"
        )
        net_capacity_juris_pba40_basisTest = pd.merge(
            left=net_capacity_juris_pba40,
            right=net_capacity_juris_basisTest,
            on="juris_zmod",
        )
        capacities_juris_pba40_basisTest = pd.merge(
            left=capacity_juris_pba40_basisTest,
            right=net_capacity_juris_pba40_basisTest,
            on="juris_zmod",
        )

        capacities_juris_pba40_basisTest["variable"] = test_attr

        logger.debug(
            "capacities_juris_pba40_basisTest.head():\n{}".format(
                capacities_juris_pba40_basisTest.head()
            )
        )

        # special metrics for allowed building development type:
        #   count where attribute changes and allow_res/allow_nonres changes, in terms of parcels and acreage
        if test_attr in dev_capacity_calculation_module.ALLOWED_BUILDING_TYPE_CODES:

            dev_type_metric = test_hybrid_parcel_idx[
                [
                    "PARCEL_ID",
                    "juris_zmod",
                    "ACRES",
                    test_attr + "_pba40",
                    test_attr + "_basis",
                    "allow_res_pba40",
                    "allow_res_urbansim",
                    "allow_nonres_pba40",
                    "allow_nonres_urbansim",
                ]
            ].copy()
            dev_type_metric["num_parcels"] = 1

            # convert to simple 1 character codes: 0, 1 or M for missing
            # TODO: 11 shouldn't be a value but apparently OF_basis=11 for two parcels?!
            dev_type_metric.replace(
                to_replace={
                    test_attr + "_pba40": {0: "0", 1: "1", np.nan: "M"},
                    test_attr + "_basis": {0: "0", 1: "1", np.nan: "M", 11: "1"},
                },
                inplace=True,
            )
            logger.debug(
                "dev_type_metric[{}_pba40].value_counts():\n{}".format(
                    test_attr, dev_type_metric[test_attr + "_pba40"].value_counts()
                )
            )
            logger.debug(
                "dev_type_metric[{}_basis].value_counts():\n{}".format(
                    test_attr, dev_type_metric[test_attr + "_basis"].value_counts()
                )
            )

            dev_type_metric["pba40_basis"] = (
                dev_type_metric[test_attr + "_pba40"]
                + " "
                + dev_type_metric[test_attr + "_basis"]
            )
            # aggregate to jurisdiction, attribute (pba40 and basis)
            dev_type_metric_juris = (
                dev_type_metric.groupby(["juris_zmod", "pba40_basis"])
                .agg({"num_parcels": "sum", "ACRES": "sum"})
                .reset_index()
            )

            # pivot so one row per jurisdiction
            dev_type_metric_juris = dev_type_metric_juris.pivot(
                index="juris_zmod",
                columns="pba40_basis",
                values=["num_parcels", "ACRES"],
            )
            # rename columns so they're not tuples; they'll look like "num_parcels 1_0"
            # NOTE: for 1_0 etc, the convention is pba40_basis
            dev_type_metric_juris.columns = [
                col[0] + " " + col[1] for col in dev_type_metric_juris.columns.values
            ]
            dev_type_metric_juris.reset_index(inplace=True)
            dev_type_metric_juris.fillna(value=0, inplace=True)
            dev_type_metric_juris["variable"] = test_attr
            logger.debug(
                "dev_type_metric_juris.head(20):\n{}".format(
                    dev_type_metric_juris.head(20)
                )
            )

            # add to capacities_juris_pba40_basisTest
            capacities_juris_pba40_basisTest = pd.merge(
                left=capacities_juris_pba40_basisTest,
                right=dev_type_metric_juris,
                how="left",
                on=["juris_zmod", "variable"],
            )

            # for development building type codes, also look at how this affects allowed res or nonres
            for devtype in ["res", "nonres"]:
                if (
                    devtype == "res"
                    and test_attr
                    not in dev_capacity_calculation_module.RES_BUILDING_TYPE_CODES
                ):
                    continue  # not relevant

                if (
                    devtype == "nonres"
                    and test_attr
                    not in dev_capacity_calculation_module.NONRES_BUILDING_TYPE_CODES
                ):
                    continue  # not relevant

                # convert to "T"/"F"
                dev_type_metric["allow_pba40"] = (
                    dev_type_metric["allow_" + devtype + "_pba40"] > 0
                )
                dev_type_metric["allow_urbansim"] = (
                    dev_type_metric["allow_" + devtype + "_urbansim"] > 0
                )
                dev_type_metric.replace(
                    to_replace={
                        "allow_pba40": {True: "T", False: "F"},
                        "allow_urbansim": {True: "T", False: "F"},
                    },
                    inplace=True,
                )
                # combine into one column
                dev_type_metric["allow_pba40_basis"] = (
                    dev_type_metric["allow_pba40"].astype(str)
                    + "_"
                    + dev_type_metric["allow_urbansim"].astype(str)
                )
                # aggregate to jurisdiction
                allow_juris = (
                    dev_type_metric.groupby(["juris_zmod", "allow_pba40_basis"])
                    .agg({"num_parcels": "sum", "ACRES": "sum"})
                    .reset_index()
                )
                logger.debug("allow_juris.head(20):\n{}".format(allow_juris.head(20)))

                # pivot so one row per jurisdiction
                allow_juris = allow_juris.pivot(
                    index="juris_zmod",
                    columns="allow_pba40_basis",
                    values=["num_parcels", "ACRES"],
                )
                # rename columns so they're not tuples; they'll look like "allow_res num_parcels T_F"
                # NOTE: for T_F etc, the convention is pba40_basis
                allow_juris.columns = [
                    "allow_" + devtype + " " + col[0] + " " + col[1]
                    for col in allow_juris.columns.values
                ]
                allow_juris.reset_index(inplace=True)
                allow_juris.fillna(value=0, inplace=True)
                allow_juris["variable"] = test_attr
                logger.debug("allow_juris.head():\n{}".format(allow_juris.head()))

                # add to capacities_juris_pba40_basisTest
                capacities_juris_pba40_basisTest = pd.merge(
                    left=capacities_juris_pba40_basisTest,
                    right=allow_juris,
                    how="left",
                    on=["juris_zmod", "variable"],
                )

        logger.debug(
            "capacities_juris_pba40_basisTest.head():\n{}".format(
                capacities_juris_pba40_basisTest.head()
            )
        )

        # add to the full set
        capacity_metrics = pd.concat(
            [capacity_metrics, capacities_juris_pba40_basisTest],
            axis="index",
            sort=True,
        )

    # bring juris_zmod and variable to the left to be more intuitive
    reorder_cols = list(capacity_metrics.columns.values)
    reorder_cols.remove("juris_zmod")
    reorder_cols.remove("variable")
    reorder_cols = ["juris_zmod", "variable"] + reorder_cols
    capacity_metrics = capacity_metrics[reorder_cols]

    # write those capacity metrics out
    capacity_metrics.to_csv(JURIS_CAPACITY_FILE, index=False)
    logger.info("Wrote {}".format(JURIS_CAPACITY_FILE))
