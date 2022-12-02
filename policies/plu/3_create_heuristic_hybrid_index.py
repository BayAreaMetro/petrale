USAGE = """

  Creates the heuristic hybrid index given a threshold argument.

"""

import pandas as pd
import numpy as np
import argparse, os, logging, sys

import dev_capacity_calculation_module


if os.getenv("USERNAME") == "ywang":
    M_DIR = "M:\\Data\\Urban\\BAUS\\PBA50\\Draft_Blueprint\\Base zoning"
    GITHUB_PETRALE_DIR = "C:\\Users\\{}\\Documents\\GitHub\\petrale\\".format(
        os.getenv("USERNAME")
    )
elif os.getenv("USERNAME") == "lzorn":
    M_DIR = "M:\\Data\\Urban\\BAUS\\PBA50\\Draft_Blueprint\\Base zoning"
    GITHUB_PETRALE_DIR = "X:\\petrale\\".format(os.getenv("USERNAME"))

# input file locations
PLU_BOC_M_DIR = os.path.join(M_DIR, "outputs")
JURIS_CAPACITY_FILE = os.path.join(
    PLU_BOC_M_DIR, "2020_06_03_juris_basis_pba40_capacity_metrics.csv"
)

# output file
OUTPUT_FILE = os.path.join(
    GITHUB_PETRALE_DIR,
    "policies\\plu\\base_zoning\\hybrid_index",
    "idx_urbansim_heuristic.csv",
)
LOG_FILE = os.path.join(
    GITHUB_PETRALE_DIR,
    "policies\\plu\\base_zoning\\hybrid_index",
    "idx_urbansim_heuristic.log",
)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=USAGE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "threshold",
        type=float,
        help="Threshold for capacity metric percentage change used to accept BASIS for a jurisdiction; should be between 0.0 and 1.0",
    )
    args = parser.parse_args()

    if args.threshold <= 0 or args.threshold >= 1.0:
        print("Expect threshold in (0,1)")
        sys.exit()

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

    logger.info("JURIS_CAPACITY_FILE = {}".format(JURIS_CAPACITY_FILE))
    logger.info("THRESHOLD           = {}".format(args.threshold))

    # Read jurisdiction capacity metrics
    capacity_juris_pba40_basis = pd.read_csv(JURIS_CAPACITY_FILE)
    logger.info(
        "Read {} lines from {}; head:\n{}".format(
            len(capacity_juris_pba40_basis),
            JURIS_CAPACITY_FILE,
            capacity_juris_pba40_basis.head(),
        )
    )
    logger.debug("dtypes:\n{}".format(capacity_juris_pba40_basis.dtypes))

    # pull jurisdictions to start the index dataframe we're building
    index_df = capacity_juris_pba40_basis[["juris_zmod"]].drop_duplicates()
    logger.debug("Have {} unique jurisdictions".format(len(index_df)))

    # intensity variables first
    for variable in (
        dev_capacity_calculation_module.INTENSITY_CODES
        + dev_capacity_calculation_module.ALLOWED_BUILDING_TYPE_CODES
    ):

        # does it affect residential?
        is_res = False
        if (
            variable
            in ["dua", "height"]
            + dev_capacity_calculation_module.RES_BUILDING_TYPE_CODES
        ):
            is_res = True

        # does it affect non-residential?
        # Note: it can be both res and non-res.
        # Also, strictly speaking, height doesn't really affect either since it affects
        # the imputation of dua and far, so this will effectively turn on BASIS for height
        is_nonres = False
        if (
            variable
            in ["far", "height"]
            + dev_capacity_calculation_module.NONRES_BUILDING_TYPE_CODES
        ):
            is_nonres = True

        logger.info(
            "Setting hybrid index for variable {:10}  res? {:5}  nonres? {:5}".format(
                variable, is_res, is_nonres
            )
        )

        # variable index name - for allowed development types, it just has a suffix "_idx"
        variable_idx = "{}_idx".format(variable)
        # for intensity variables, it has max_XX_idx
        if variable in dev_capacity_calculation_module.INTENSITY_CODES:
            variable_idx = "max_{}_idx".format(variable)

            # intensity have proportion variables too --- set to 1.0
            index_df["proportion_adj_{}".format(variable)] = 1.0

        # pull the select rows from capacity_juris_pba40_basis relevant for this variable
        capacity_juris_var = capacity_juris_pba40_basis.loc[
            capacity_juris_pba40_basis["variable"] == variable,
        ].copy()
        # default to PBA40
        capacity_juris_var[variable_idx] = dev_capacity_calculation_module.USE_PBA40

        # for variables that are res and nonres, require units AND sqft to be within threshold
        if is_res and is_nonres:
            capacity_juris_var.loc[
                (
                    (
                        abs(
                            capacity_juris_var.units_basis
                            - capacity_juris_var.units_pba40
                        )
                        / capacity_juris_var.units_pba40
                    )
                    <= args.threshold
                )
                & (
                    (
                        abs(
                            capacity_juris_var.Ksqft_basis
                            - capacity_juris_var.Ksqft_pba40
                        )
                        / capacity_juris_var.Ksqft_pba40
                    )
                    <= args.threshold
                ),
                variable_idx,
            ] = dev_capacity_calculation_module.USE_BASIS

        # for res variables, require units to be within threshold
        elif is_res:
            capacity_juris_var.loc[
                (
                    abs(capacity_juris_var.units_basis - capacity_juris_var.units_pba40)
                    / capacity_juris_var.units_pba40
                )
                <= args.threshold,
                variable_idx,
            ] = dev_capacity_calculation_module.USE_BASIS

        # for nonres variables, require sqft to be within threshold
        elif is_nonres:

            capacity_juris_var.loc[
                (
                    abs(capacity_juris_var.Ksqft_basis - capacity_juris_var.Ksqft_pba40)
                    / capacity_juris_var.Ksqft_pba40
                )
                <= args.threshold,
                variable_idx,
            ] = dev_capacity_calculation_module.USE_BASIS

        # bring into index_df
        index_df = pd.merge(
            left=index_df, right=capacity_juris_var[["juris_zmod", variable_idx]]
        )

    # report out number of BASIS jurisdictions for each variable
    # these should match the tableau
    logger.info(
        "Number of jurisdictions using BASIS variable:\n{}".format(index_df.sum())
    )

    # rename jurisdiction
    index_df.rename(columns={"juris_zmod": "juris_name"}, inplace=True)

    # save it
    index_df.to_csv(OUTPUT_FILE, index=False)
    logger.info("Wrote {}".format(OUTPUT_FILE))
