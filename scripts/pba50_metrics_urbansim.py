USAGE = """

  python pba50_metrics_urbansim.py

  Needs access to these box folders and M Drive
    Box/Modeling and Surveys/Urban Modeling/Bay Area UrbanSim 1.5/PBA50/Draft Blueprint runs/
    Box/Horizon and Plan Bay Area 2050/Equity and Performance/7_Analysis/Metrics/

  Processes model outputs and creates a single csv with scenario metrics in this folder:
    Box/Horizon and Plan Bay Area 2050/Equity and Performance/7_Analysis/Metrics/

  This csv file will have 6 columns:
    1) modelrun ID
    2) metric ID
    3) metric name
    4) year  (note: for metrics that depict change from 2015 to 2050, this value will be 2050)
    5) blueprint type
    6) metric value

"""

import datetime, os, sys
import numpy, pandas as pd
from collections import OrderedDict, defaultdict


def calculate_normalize_factor_Q1Q2(parcel_sum_df):
    return (
        (parcel_sum_df["hhq1_2050"].sum() + parcel_sum_df["hhq2_2050"].sum())
        / parcel_sum_df["tothh_2050"].sum()
    ) / (
        (parcel_sum_df["hhq1_2015"].sum() + parcel_sum_df["hhq2_2015"].sum())
        / parcel_sum_df["tothh_2015"].sum()
    )


def calculate_normalize_factor_Q1(parcel_sum_df):
    return (parcel_sum_df["hhq1_2050"].sum() / parcel_sum_df["tothh_2050"].sum()) / (
        parcel_sum_df["hhq1_2015"].sum() / parcel_sum_df["tothh_2015"].sum()
    )


def calculate_Affordable2_deed_restricted_housing(runid, parcel_sum_df, metrics_dict):

    metric_id = "A2"

    # totals for 2050 and 2015
    metrics_dict[runid, metric_id, "deed_restricted", y2] = parcel_sum_df[
        "deed_restricted_units_2050"
    ].sum()
    metrics_dict[runid, metric_id, "deed_restricted", y1] = parcel_sum_df[
        "deed_restricted_units_2015"
    ].sum()
    metrics_dict[runid, metric_id, "residential_units", y2] = parcel_sum_df[
        "residential_units_2050"
    ].sum()
    metrics_dict[runid, metric_id, "residential_units", y1] = parcel_sum_df[
        "residential_units_2015"
    ].sum()
    metrics_dict[runid, metric_id, "deed_restricted_HRA", y2] = parcel_sum_df.loc[
        parcel_sum_df["fbpchcat"].str.contains("HRA", na=False),
        "deed_restricted_units_2050",
    ].sum()
    metrics_dict[runid, metric_id, "deed_restricted_HRA", y1] = parcel_sum_df.loc[
        parcel_sum_df["fbpchcat"].str.contains("HRA", na=False),
        "deed_restricted_units_2015",
    ].sum()
    metrics_dict[runid, metric_id, "residential_units_HRA", y2] = parcel_sum_df.loc[
        parcel_sum_df["fbpchcat"].str.contains("HRA", na=False),
        "residential_units_2050",
    ].sum()
    metrics_dict[runid, metric_id, "residential_units_HRA", y1] = parcel_sum_df.loc[
        parcel_sum_df["fbpchcat"].str.contains("HRA", na=False),
        "residential_units_2015",
    ].sum()

    # diff between 2050 and 2015
    metrics_dict[runid, metric_id, "deed_restricted", y_diff] = (
        metrics_dict[runid, metric_id, "deed_restricted", y2]
        - metrics_dict[runid, metric_id, "deed_restricted", y1]
    )
    metrics_dict[runid, metric_id, "residential_units", y_diff] = (
        metrics_dict[runid, metric_id, "residential_units", y2]
        - metrics_dict[runid, metric_id, "residential_units", y1]
    )
    metrics_dict[runid, metric_id, "deed_restricted_HRA", y_diff] = (
        metrics_dict[runid, metric_id, "deed_restricted_HRA", y2]
        - metrics_dict[runid, metric_id, "deed_restricted_HRA", y1]
    )
    metrics_dict[runid, metric_id, "residential_units_HRA", y_diff] = (
        metrics_dict[runid, metric_id, "residential_units_HRA", y2]
        - metrics_dict[runid, metric_id, "residential_units_HRA", y1]
    )
    metrics_dict[runid, metric_id, "deed_restricted_nonHRA", y_diff] = (
        metrics_dict[runid, metric_id, "deed_restricted", y_diff]
        - metrics_dict[runid, metric_id, "deed_restricted_HRA", y_diff]
    )
    metrics_dict[runid, metric_id, "residential_units_nonHRA", y_diff] = (
        metrics_dict[runid, metric_id, "residential_units", y_diff]
        - metrics_dict[runid, metric_id, "residential_units_HRA", y_diff]
    )

    # metric: deed restricted % of total units: overall, HRA and non-HRA
    metrics_dict[runid, metric_id, "deed_restricted_pct_new_units", y_diff] = (
        metrics_dict[runid, metric_id, "deed_restricted", y_diff]
        / metrics_dict[runid, metric_id, "residential_units", y_diff]
    )
    metrics_dict[runid, metric_id, "deed_restricted_pct_new_units_HRA", y_diff] = (
        metrics_dict[runid, metric_id, "deed_restricted_HRA", y_diff]
        / metrics_dict[runid, metric_id, "residential_units_HRA", y_diff]
    )
    metrics_dict[runid, metric_id, "deed_restricted_pct_new_units_nonHRA", y_diff] = (
        metrics_dict[runid, metric_id, "deed_restricted_nonHRA", y_diff]
        / metrics_dict[runid, metric_id, "residential_units_nonHRA", y_diff]
    )

    print("********************A2 Affordable********************")
    print(
        "DIS pct of new units %s"
        % metrics_dict[runid, metric_id, "deed_restricted_pct_new_units", y_diff]
    )
    print(
        "DIS pct of new units in HRAs %s"
        % metrics_dict[runid, metric_id, "deed_restricted_pct_new_units_HRA", y_diff]
    )
    print(
        "DIS pct of new units outside of HRAs %s"
        % metrics_dict[runid, metric_id, "deed_restricted_pct_new_units_nonHRA", y_diff]
    )

    # Forcing preservation metrics
    # metrics_dict[runid,metric_id,'preservation_affordable_housing',y_diff] = 1


def calculate_Diverse1_LIHHinHRAs(
    runid,
    parcel_sum_df,
    tract_sum_df,
    normalize_factor_Q1Q2,
    normalize_factor_Q1,
    metrics_dict,
):

    metric_id = "D1"

    # Share of region's LIHH households that are in HRAs
    metrics_dict[runid, metric_id, "LIHH_total", y2] = (
        parcel_sum_df["hhq1_2050"].sum() + parcel_sum_df["hhq2_2050"].sum()
    )
    metrics_dict[runid, metric_id, "LIHH_total", y1] = (
        parcel_sum_df["hhq1_2015"].sum() + parcel_sum_df["hhq2_2015"].sum()
    )
    metrics_dict[runid, metric_id, "LIHH_total", y_diff] = (
        metrics_dict[runid, metric_id, "LIHH_total", y2]
        - metrics_dict[runid, metric_id, "LIHH_total", y1]
    )

    metrics_dict[runid, metric_id, "LIHH_inHRA", y2] = (
        parcel_sum_df.loc[
            parcel_sum_df["fbpchcat"].str.contains("HRA", na=False), "hhq1_2050"
        ].sum()
        + parcel_sum_df.loc[
            parcel_sum_df["fbpchcat"].str.contains("HRA", na=False), "hhq2_2050"
        ].sum()
    )
    metrics_dict[runid, metric_id, "LIHH_inHRA", y1] = (
        parcel_sum_df.loc[
            parcel_sum_df["fbpchcat"].str.contains("HRA", na=False), "hhq1_2015"
        ].sum()
        + parcel_sum_df.loc[
            parcel_sum_df["fbpchcat"].str.contains("HRA", na=False), "hhq2_2015"
        ].sum()
    )
    metrics_dict[runid, metric_id, "LIHH_inHRA", y_diff] = (
        metrics_dict[runid, metric_id, "LIHH_inHRA", y2]
        - metrics_dict[runid, metric_id, "LIHH_inHRA", y1]
    )

    metrics_dict[runid, metric_id, "LIHH_shareinHRA", y2] = (
        metrics_dict[runid, metric_id, "LIHH_inHRA", y2]
        / metrics_dict[runid, metric_id, "LIHH_total", y2]
    )
    metrics_dict[runid, metric_id, "LIHH_shareinHRA", y1] = (
        metrics_dict[runid, metric_id, "LIHH_inHRA", y1]
        / metrics_dict[runid, metric_id, "LIHH_total", y1]
    )

    # normalizing for overall growth in LIHH
    metrics_dict[runid, metric_id, "LIHH_shareinHRA_normalized", y1] = (
        metrics_dict[runid, metric_id, "LIHH_shareinHRA", y1] * normalize_factor_Q1Q2
    )
    metrics_dict[runid, metric_id, "LIHH_shareinHRA_normalized", y2] = metrics_dict[
        runid, metric_id, "LIHH_shareinHRA", y2
    ]
    # Total HHs in CoC Tracts, in 2015 and 2050
    metrics_dict[runid, metric_id, "TotHH_inCoC", y1] = tract_sum_df.loc[
        (tract_sum_df["coc_flag_pba2050"] == 1), "tothh_2015"
    ].sum()
    metrics_dict[runid, metric_id, "TotHH_inCoC", y2] = tract_sum_df.loc[
        (tract_sum_df["coc_flag_pba2050"] == 1), "tothh_2050"
    ].sum()
    metrics_dict[runid, metric_id, "TotHH_inCoC", y_diff] = (
        metrics_dict[runid, metric_id, "TotHH_inCoC", y2]
        - metrics_dict[runid, metric_id, "TotHH_inCoC", y1]
    )

    ########### Tracking movement of Q1 households: Q1 share of Households
    # Share of Households that are Q1, within each geography type in this order:
    # Overall Region; HRAs; DIS Tracts; CoCs; PDAs; TRAs
    # Region
    metrics_dict[runid, metric_id, "Q1HH_shareofRegion", y1] = (
        parcel_sum_df["hhq1_2015"].sum() / parcel_sum_df["tothh_2015"].sum()
    )
    metrics_dict[runid, metric_id, "Q1HH_shareofRegion_normalized", y1] = (
        parcel_sum_df["hhq1_2015"].sum()
        / parcel_sum_df["tothh_2015"].sum()
        * normalize_factor_Q1
    )
    metrics_dict[runid, metric_id, "Q1HH_shareofRegion", y2] = (
        parcel_sum_df["hhq1_2050"].sum() / parcel_sum_df["tothh_2050"].sum()
    )
    metrics_dict[runid, metric_id, "Q1HH_shareofRegion_normalized", y2] = metrics_dict[
        runid, metric_id, "Q1HH_shareofRegion", y2
    ]
    # HRA
    metrics_dict[runid, metric_id, "Q1HH_shareofHRA", y1] = (
        parcel_sum_df.loc[
            parcel_sum_df["fbpchcat"].str.contains("HRA", na=False), "hhq1_2015"
        ].sum()
        / parcel_sum_df.loc[
            parcel_sum_df["fbpchcat"].str.contains("HRA", na=False), "tothh_2015"
        ].sum()
    )
    metrics_dict[runid, metric_id, "Q1HH_shareofHRA_normalized", y1] = (
        metrics_dict[runid, metric_id, "Q1HH_shareofHRA", y1] * normalize_factor_Q1
    )
    metrics_dict[runid, metric_id, "Q1HH_shareofHRA", y2] = (
        parcel_sum_df.loc[
            parcel_sum_df["fbpchcat"].str.contains("HRA", na=False), "hhq1_2050"
        ].sum()
        / parcel_sum_df.loc[
            parcel_sum_df["fbpchcat"].str.contains("HRA", na=False), "tothh_2050"
        ].sum()
    )
    metrics_dict[runid, metric_id, "Q1HH_shareofHRA_normalized", y2] = metrics_dict[
        runid, metric_id, "Q1HH_shareofHRA", y2
    ]
    # DIS
    metrics_dict[runid, metric_id, "Q1HH_shareofDIS", y1] = (
        parcel_sum_df.loc[
            parcel_sum_df["fbpchcat"].str.contains("DIS", na=False), "hhq1_2015"
        ].sum()
        / parcel_sum_df.loc[
            parcel_sum_df["fbpchcat"].str.contains("DIS", na=False), "tothh_2015"
        ].sum()
    )
    metrics_dict[runid, metric_id, "Q1HH_shareofDIS_normalized", y1] = (
        metrics_dict[runid, metric_id, "Q1HH_shareofDIS", y1] * normalize_factor_Q1
    )
    metrics_dict[runid, metric_id, "Q1HH_shareofDIS", y2] = (
        parcel_sum_df.loc[
            parcel_sum_df["fbpchcat"].str.contains("DIS", na=False), "hhq1_2050"
        ].sum()
        / parcel_sum_df.loc[
            parcel_sum_df["fbpchcat"].str.contains("DIS", na=False), "tothh_2050"
        ].sum()
    )
    metrics_dict[runid, metric_id, "Q1HH_shareofDIS_normalized", y2] = metrics_dict[
        runid, metric_id, "Q1HH_shareofDIS", y2
    ]
    # CoC
    metrics_dict[runid, metric_id, "Q1HH_shareofCoC", y1] = (
        tract_sum_df.loc[(tract_sum_df["coc_flag_pba2050"] == 1), "hhq1_2015"].sum()
        / tract_sum_df.loc[(tract_sum_df["coc_flag_pba2050"] == 1), "tothh_2015"].sum()
    )
    metrics_dict[runid, metric_id, "Q1HH_shareofCoC_normalized", y1] = (
        metrics_dict[runid, metric_id, "Q1HH_shareofCoC", y1] * normalize_factor_Q1
    )
    metrics_dict[runid, metric_id, "Q1HH_shareofCoC", y2] = (
        tract_sum_df.loc[(tract_sum_df["coc_flag_pba2050"] == 1), "hhq1_2050"].sum()
        / tract_sum_df.loc[(tract_sum_df["coc_flag_pba2050"] == 1), "tothh_2050"].sum()
    )
    metrics_dict[runid, metric_id, "Q1HH_shareofCoC_normalized", y2] = metrics_dict[
        runid, metric_id, "Q1HH_shareofCoC", y2
    ]
    # GG
    metrics_dict[runid, metric_id, "Q1HH_shareofGG", y1] = (
        parcel_sum_df.loc[
            parcel_sum_df["fbpchcat"].str.contains("GG", na=False), "hhq1_2015"
        ].sum()
        / parcel_sum_df.loc[
            parcel_sum_df["fbpchcat"].str.contains("GG", na=False), "tothh_2015"
        ].sum()
    )
    metrics_dict[runid, metric_id, "Q1HH_shareofGG_normalized", y1] = (
        metrics_dict[runid, metric_id, "Q1HH_shareofGG", y1] * normalize_factor_Q1
    )
    metrics_dict[runid, metric_id, "Q1HH_shareofGG", y2] = (
        parcel_sum_df.loc[
            parcel_sum_df["fbpchcat"].str.contains("GG", na=False), "hhq1_2050"
        ].sum()
        / parcel_sum_df.loc[
            parcel_sum_df["fbpchcat"].str.contains("GG", na=False), "tothh_2050"
        ].sum()
    )
    metrics_dict[runid, metric_id, "Q1HH_shareofGG_normalized", y2] = metrics_dict[
        runid, metric_id, "Q1HH_shareofGG", y2
    ]

    # TRAGG
    parcel_GG = parcel_sum_df.loc[
        parcel_sum_df["fbpchcat"].str.contains("GG", na=False)
    ]
    parcel_TRAGG = parcel_GG.loc[parcel_GG["fbpchcat"].str.contains("tra", na=False)]

    metrics_dict[runid, metric_id, "Q1HH_shareofTRAGG", y1] = (
        parcel_TRAGG["hhq1_2015"].sum() / parcel_TRAGG["tothh_2015"].sum()
    )
    metrics_dict[runid, metric_id, "Q1HH_shareofTRAGG_normalized", y1] = (
        metrics_dict[runid, metric_id, "Q1HH_shareofTRAGG", y1] * normalize_factor_Q1
    )
    metrics_dict[runid, metric_id, "Q1HH_shareofTRAGG", y2] = (
        parcel_TRAGG["hhq1_2050"].sum() / parcel_TRAGG["tothh_2050"].sum()
    )
    metrics_dict[runid, metric_id, "Q1HH_shareofTRAGG_normalized", y2] = metrics_dict[
        runid, metric_id, "Q1HH_shareofTRAGG", y2
    ]

    print("********************D1 Diverse********************")
    print(
        "Growth of LIHH share of population (normalize factor))", normalize_factor_Q1Q2
    )
    print(
        "LIHH Share in HRA 2050 %s"
        % metrics_dict[runid, metric_id, "LIHH_shareinHRA", y2]
    )
    print(
        "LIHH Share in HRA 2015 %s"
        % metrics_dict[runid, metric_id, "LIHH_shareinHRA_normalized", y1]
    )


def calculate_Diverse2_LIHH_Displacement(
    runid, parcel_sum_df, tract_sum_df, normalize_factor_Q1, metrics_dict
):

    metric_id = "D2"

    # For reference: total number of LIHH in tracts
    metrics_dict[runid, metric_id, "LIHH_inDIS", y2] = parcel_sum_df.loc[
        parcel_sum_df["fbpchcat"].str.contains("DIS", na=False), "hhq1_2050"
    ].sum()
    metrics_dict[runid, metric_id, "LIHH_inDIS", y1] = parcel_sum_df.loc[
        parcel_sum_df["fbpchcat"].str.contains("DIS", na=False), "hhq1_2015"
    ].sum()
    metrics_dict[runid, metric_id, "LIHH_inDIS_normalized", y1] = (
        metrics_dict[runid, metric_id, "LIHH_inDIS", y1] * normalize_factor_Q1
    )
    metrics_dict[runid, metric_id, "LIHH_inDIS_normalized", y2] = metrics_dict[
        runid, metric_id, "LIHH_inDIS", y2
    ]

    print("********************D2 Diverse********************")
    print(
        "Total Number of LIHH in DIS tracts in 2050",
        metrics_dict[runid, metric_id, "LIHH_inDIS", y2],
    )
    print(
        "Number of LIHH in DIS tracts in 2015",
        metrics_dict[runid, metric_id, "LIHH_inDIS", y1],
    )
    print(
        "Number of LIHH in DIS tracts in normalized",
        metrics_dict[runid, metric_id, "LIHH_inDIS_normalized", y1],
    )


def calculate_Healthy1_HHs_SLRprotected(runid, parcel_sum_df, metrics_dict):

    metric_id = "H1"

    # Renaming Parcels as "Protected", "Unprotected", and "Unaffected"

    # Basic
    def label_SLR(row):
        if row["SLR"] == 12:
            return "Unprotected"
        elif row["SLR"] == 24:
            return "Unprotected"
        elif row["SLR"] == 36:
            return "Unprotected"
        elif row["SLR"] == 100:
            return "Protected"
        else:
            return "Unaffected"

    parcel_sum_df["SLR_protection"] = parcel_sum_df.apply(
        lambda row: label_SLR(row), axis=1
    )

    # Calculating protected households

    # All households
    tothh_2050_affected = parcel_sum_df.loc[
        (parcel_sum_df["SLR_protection"].str.contains("rotected") == True), "tothh_2050"
    ].sum()
    tothh_2050_protected = parcel_sum_df.loc[
        (parcel_sum_df["SLR_protection"].str.contains("Protected") == True),
        "tothh_2050",
    ].sum()
    tothh_2015_affected = parcel_sum_df.loc[
        (parcel_sum_df["SLR_protection"].str.contains("rotected") == True), "tothh_2015"
    ].sum()
    tothh_2015_protected = parcel_sum_df.loc[
        (parcel_sum_df["SLR_protection"].str.contains("Protected") == True),
        "tothh_2015",
    ].sum()

    # Q1 Households
    hhq1_2050_affected = parcel_sum_df.loc[
        (parcel_sum_df["SLR_protection"].str.contains("rotected") == True), "hhq1_2050"
    ].sum()
    hhq1_2050_protected = parcel_sum_df.loc[
        (parcel_sum_df["SLR_protection"].str.contains("Protected") == True), "hhq1_2050"
    ].sum()
    hhq1_2015_affected = parcel_sum_df.loc[
        (parcel_sum_df["SLR_protection"].str.contains("rotected") == True), "hhq1_2015"
    ].sum()
    hhq1_2015_protected = parcel_sum_df.loc[
        (parcel_sum_df["SLR_protection"].str.contains("Protected") == True), "hhq1_2015"
    ].sum()

    # CoC Households

    CoChh_2050_affected = parcel_sum_df.loc[
        (
            (parcel_sum_df["SLR_protection"].str.contains("rotected") == True)
            & parcel_sum_df["coc_flag_pba2050"]
            == 1
        ),
        "tothh_2050",
    ].sum()
    CoChh_2050_protected = parcel_sum_df.loc[
        (
            (parcel_sum_df["SLR_protection"].str.contains("Protected") == True)
            & parcel_sum_df["coc_flag_pba2050"]
            == 1
        ),
        "tothh_2050",
    ].sum()
    CoChh_2015_affected = parcel_sum_df.loc[
        (
            (parcel_sum_df["SLR_protection"].str.contains("rotected") == True)
            & parcel_sum_df["coc_flag_pba2050"]
            == 1
        ),
        "tothh_2015",
    ].sum()
    CoChh_2015_protected = parcel_sum_df.loc[
        (
            (parcel_sum_df["SLR_protection"].str.contains("Protected") == True)
            & parcel_sum_df["coc_flag_pba2050"]
            == 1
        ),
        "tothh_2015",
    ].sum()

    metrics_dict[runid, metric_id, "SLR_protected_pct_affected_tothh", y2] = (
        tothh_2050_protected / tothh_2050_affected
    )
    metrics_dict[runid, metric_id, "SLR_protected_pct_affected_hhq1", y2] = (
        hhq1_2050_protected / hhq1_2050_affected
    )
    metrics_dict[runid, metric_id, "SLR_protected_pct_affected_CoChh", y2] = (
        CoChh_2050_protected / CoChh_2050_affected
    )

    print("********************H1 Healthy********************")
    print(
        "Pct of HHs affected by 3ft SLR that are protected in 2050 in %s"
        % metrics_dict[runid, metric_id, "SLR_protected_pct_affected_tothh", y2]
    )
    print(
        "Pct of Q1 HHs affected by 3ft SLR that are protected in 2050 in %s"
        % metrics_dict[runid, metric_id, "SLR_protected_pct_affected_hhq1", y2]
    )
    print(
        "Pct of CoC HHs affected by 3ft SLR that are protected in 2050 in %s"
        % metrics_dict[runid, metric_id, "SLR_protected_pct_affected_CoChh", y2]
    )


def calculate_Healthy1_HHs_EQprotected(runid, parcel_sum_df, metrics_dict):

    metric_id = "H1"

    """
    # Reading building codes file, which has info at building level, on which parcels are inundated and protected

    buildings_code = pd.read_csv('C:/Users/ATapase/Box/Horizon and Plan Bay Area 2050/Equity and Performance/7_Analysis/Metrics/Healthy/buildings_with_eq_code.csv')
    buildings_eq = pd.merge(left=buildings_code[['building_id', 'parcel_id', 'residential_units', 'year_built', 'earthquake_code']], right=parcel_sum_df[['parcel_id','zone_id','tract_id','coc_flag_pba2050','fbpchcat','hhq1_2015','hhq1_2050','tothh_2015','tothh_2050']], left_on="parcel_id", right_on="parcel_id", how="left")
    buildings_eq = pd.merge(left=buildings_eq, right=coc_flag[['tract_id_coc','county_fips']], left_on="tract_id", right_on="tract_id_coc", how="left")
    buildings_cat = pd.read_csv('C:/Users/ATapase/Box/Horizon and Plan Bay Area 2050/Equity and Performance/7_Analysis/Metrics/Healthy/building_eq_categories.csv')
    buildings_eq = pd.merge(left=buildings_eq, right=buildings_cat, left_on="earthquake_code", right_on="building_eq_code", how="inner")
    buildings_eq.drop(['building_eq_code', 'tract_id_coc'], axis=1, inplace=True)
    buildings_eq['cost_retrofit_total'] = buildings_eq['residential_units'] * buildings_eq['cost_retrofit']

    # Calculated protected households in PLus

    # Number of Units retrofitted
    metrics_dict['H2_eq_num_units_retrofit'] = buildings_eq['residential_units'].sum()
    metrics_dict['H2_eq_num_CoC_units_retrofit'] = buildings_eq.loc[(buildings_eq['coc_flag_pba2050']== 1), 'residential_units'].sum()

    metrics_dict['H2_eq_total_cost_retrofit'] = buildings_eq['cost_retrofit_total'].sum()
    metrics_dict['H2_eq_CoC_cost_retrofit'] = buildings_eq.loc[(buildings_eq['coc_flag_pba2050']== 1), 'cost_retrofit_total'].sum()

    print('Total number of units retrofited',metrics_dict['H2_eq_num_units_retrofit'])
    print('CoC number of units retrofited',metrics_dict['H2_eq_num_CoC_units_retrofit'])

    print('Total cost of retrofit',metrics_dict['H2_eq_total_cost_retrofit'])
    print('CoC cost of retrofit',metrics_dict['H2_eq_CoC_cost_retrofit'])
    """


def calculate_Healthy1_HHs_WFprotected(runid, arcel_sum_df, metrics_dict):

    metric_id = "H1"

    """
    # 
    """


def calculate_Healthy2_HHs_WFprotected(runid, parcel_sum_df, metrics_dict):

    metric_id = "H2"

    """
    # 
    """


def calculate_Healthy2_GreenfieldDev(runid, greenfield_sum_df, metrics_dict):

    metric_id = "H2-3"
    print("********************H2-3 Annual Greenfield Development********************")

    metrics_dict[runid, metric_id, "Annual_greenfield_develop_acres", y2] = (
        greenfield_sum_df.iloc[3]["urban_footprint_0_2050"]
        - greenfield_sum_df.iloc[3]["urban_footprint_0_2015"]
    ) / (
        int(y2) - int(y1)
    )  # 3 is the rownumber for "acres"
    metrics_dict[runid, metric_id, "Annual_greenfield_develop_acres", y1] = (
        6642 / 2
    )  # 2015 is observed data

    print(
        "Annual Greenfield Development Acres in 2050 %s"
        % metrics_dict[runid, metric_id, "Annual_greenfield_develop_acres", y2]
    )
    print(
        "Annual Greenfield Development Acres in 2015 %s"
        % metrics_dict[runid, metric_id, "Annual_greenfield_develop_acres", y1]
    )


def calculate_Vibrant2_Jobs(runid, parcel_sum_df, metrics_dict):

    metric_id = "V2"
    print("********************V2 Vibrant********************")

    # Total Jobs Growth

    metrics_dict[runid, metric_id, "Total_jobs", y2] = parcel_sum_df[
        "totemp_2050"
    ].sum()
    metrics_dict[runid, metric_id, "Total_jobs", y1] = parcel_sum_df[
        "totemp_2015"
    ].sum()
    metrics_dict[runid, metric_id, "Total_jobs", y_diff] = (
        metrics_dict[runid, metric_id, "Total_jobs", y2]
        / metrics_dict[runid, metric_id, "Total_jobs", y1]
        - 1
    )
    print(
        "Number of Jobs in 2050 %s" % metrics_dict[runid, metric_id, "Total_jobs", y2]
    )
    print(
        "Number of Jobs in 2015 %s" % metrics_dict[runid, metric_id, "Total_jobs", y1]
    )
    print(
        "Job Growth from 2015 to 2050 %s"
        % metrics_dict[runid, metric_id, "Total_jobs", y_diff]
    )

    # MWTEMPN jobs
    metrics_dict[runid, metric_id, "Total_MWTEMPN_jobs", y2] = parcel_sum_df[
        "MWTEMPN_2050"
    ].sum()
    metrics_dict[runid, metric_id, "Total_MWTEMPN_jobs", y1] = parcel_sum_df[
        "MWTEMPN_2015"
    ].sum()
    metrics_dict[runid, metric_id, "Total_MWTEMPN_jobs", y_diff] = (
        metrics_dict[runid, metric_id, "Total_MWTEMPN_jobs", y2]
        / metrics_dict[runid, metric_id, "Total_MWTEMPN_jobs", y1]
        - 1
    )
    print(
        "Number of Total MWTEMPN Jobs 2050 %s"
        % metrics_dict[runid, metric_id, "Total_MWTEMPN_jobs", y2]
    )
    print(
        "Number of Total MWTEMPN Jobs 2015 %s"
        % metrics_dict[runid, metric_id, "Total_MWTEMPN_jobs", y1]
    )
    print(
        "Job Growth Total MWTEMPN from 2015 to 2050 %s"
        % metrics_dict[runid, metric_id, "Total_MWTEMPN_jobs", y_diff]
    )

    # Jobs Growth in PPAs

    metrics_dict[runid, metric_id, "PPA_jobs", y2] = parcel_sum_df.loc[
        parcel_sum_df["fbpchcat"].str.contains("ppa", na=False), "totemp_2050"
    ].sum()
    metrics_dict[runid, metric_id, "PPA_jobs", y1] = parcel_sum_df.loc[
        parcel_sum_df["fbpchcat"].str.contains("ppa", na=False), "totemp_2015"
    ].sum()
    metrics_dict[runid, metric_id, "PPA_jobs", y_diff] = (
        metrics_dict[runid, metric_id, "PPA_jobs", y2]
        / metrics_dict[runid, metric_id, "PPA_jobs", y1]
        - 1
    )
    print(
        "Number of Jobs in PPAs 2050 %s"
        % metrics_dict[runid, metric_id, "PPA_jobs", y2]
    )
    print(
        "Number of Jobs in PPAs 2015 %s"
        % metrics_dict[runid, metric_id, "PPA_jobs", y1]
    )
    print(
        "Job Growth in PPAs from 2015 to 2050 %s"
        % metrics_dict[runid, metric_id, "Total_MWTEMPN_jobs", y_diff]
    )

    # Jobs Growth MWTEMPN in PPAs (Manufacturing & Wholesale, Transportation & Utilities)

    metrics_dict[runid, metric_id, "PPA_MWTEMPN_jobs", y2] = parcel_sum_df.loc[
        parcel_sum_df["fbpchcat"].str.contains("ppa", na=False), "MWTEMPN_2050"
    ].sum()
    metrics_dict[runid, metric_id, "PPA_MWTEMPN_jobs", y1] = parcel_sum_df.loc[
        parcel_sum_df["fbpchcat"].str.contains("ppa", na=False), "MWTEMPN_2015"
    ].sum()
    metrics_dict[runid, metric_id, "PPA_MWTEMPN_jobs", y_diff] = (
        metrics_dict[runid, metric_id, "PPA_MWTEMPN_jobs", y2]
        / metrics_dict[runid, metric_id, "PPA_MWTEMPN_jobs", y1]
        - 1
    )
    print(
        "Number of MWTEMPN Jobs in PPAs 2050 %s"
        % metrics_dict[runid, metric_id, "PPA_MWTEMPN_jobs", y2]
    )
    print(
        "Number of MWTEMPN Jobs in PPAs 2015 %s"
        % metrics_dict[runid, metric_id, "PPA_MWTEMPN_jobs", y1]
    )
    print(
        "Job Growth MWTEMPN in PPAs from 2015 to 2050 %s"
        % metrics_dict[runid, metric_id, "PPA_MWTEMPN_jobs", y_diff]
    )


def parcel_building_output_sum(urbansim_runid):

    #################### creating parcel level df from buildings output
    ###this is to analyze changes of residential units and total deed_restricted units

    building_output_2050 = pd.read_csv(
        urbansim_runid + "_building_data_2050.csv", engine="python"
    )
    building_output_2015 = pd.read_csv(
        urbansim_runid + "_building_data_2015.csv", engine="python"
    )

    parcel_building_output_2050 = (
        building_output_2050[
            ["parcel_id", "residential_units", "deed_restricted_units"]
        ]
        .groupby(["parcel_id"])
        .sum()
        .reset_index()
    )
    parcel_building_output_2015 = (
        building_output_2015[
            ["parcel_id", "residential_units", "deed_restricted_units"]
        ]
        .groupby(["parcel_id"])
        .sum()
        .reset_index()
    )
    parcel_building_output_2050 = parcel_building_output_2050.add_suffix("_2050")
    parcel_building_output_2015 = parcel_building_output_2015.add_suffix("_2015")
    parcel_building_output = pd.merge(
        left=parcel_building_output_2050,
        right=parcel_building_output_2015,
        left_on="parcel_id_2050",
        right_on="parcel_id_2015",
        how="left",
    )
    parcel_building_output = parcel_building_output.rename(
        columns={"parcel_id_2050": "parcel_id"}
    )

    return parcel_building_output


def calc_urbansim_metrics():

    parcel_geo_df = pd.read_csv(parcel_geography_file)
    parcel_tract_crosswalk_df = pd.read_csv(parcel_tract_crosswalk_file)
    udp_DR_df = pd.read_csv(udp_file)
    coc_flag_df = pd.read_csv(coc_flag_file)
    slr_plus = pd.read_csv(slr_plus_file)
    # parcel_GG_xwalk_df          = pd.read_csv(parcel_GG_crosswalk_file)

    for us_runid in list_us_runid:

        urbansim_runid = urbansim_run_location + us_runid
        run_num = us_runid.split("/")[-2]

        # Temporary forcing until we have a Plus run
        # urbansim_runid     = urbansim_run_location + 'Blueprint Basic (s21)/v1.5/run939'

        #################### creating parcel level df from buildings output

        parcel_building_output_sum_df = parcel_building_output_sum(urbansim_runid)

        #################### Creating parcel summary

        parcel_output_2050_df = pd.read_csv(
            urbansim_runid + "_parcel_data_2050.csv", engine="python"
        )
        parcel_output_2015_df = pd.read_csv(
            urbansim_runid + "_parcel_data_2015.csv", engine="python"
        )

        if "fbpchcat" in parcel_output_2050_df.columns:
            zoningtag = "fbpchcat"
        elif "pba50chcat" in parcel_output_2050_df.columns:
            zoningtag = "pba50chcat"
        elif "zoningmodcat" in parcel_output_2050_df.columns:
            zoningtag = "zoningmodcat"
        else:
            zoningtag = "zoninghzcat"
        # keeping essential columns / renaming columns
        if us_runid == us_2050_DBP_Plus_runid:
            parcel_output_2050_df.drop(
                [
                    "x",
                    "y",
                    "geom_id",
                    "total_residential_units",
                    "total_job_spaces",
                    "zoned_du",
                    "zoned_du_underbuild",
                    "zoned_du_underbuild_nodev",
                    "first_building_type",
                ],
                axis=1,
                inplace=True,
            )
            parcel_output_2015_df.drop(
                [
                    "x",
                    "y",
                    "geom_id",
                    "total_residential_units",
                    "total_job_spaces",
                    "zoned_du",
                    "zoned_du_underbuild",
                    "zoned_du_underbuild_nodev",
                    "first_building_type",
                ],
                axis=1,
                inplace=True,
            )
        else:
            parcel_output_2050_df.drop(
                [
                    "x",
                    "y",
                    "geom_id",
                    zoningtag,
                    "residential_units",
                    "deed_restricted_units",
                    "total_job_spaces",
                    "zoned_du",
                    "zoned_du_underbuild",
                    "zoned_du_underbuild_nodev",
                    "first_building_type",
                ],
                axis=1,
                inplace=True,
            )
            parcel_output_2015_df.drop(
                [
                    "x",
                    "y",
                    "geom_id",
                    zoningtag,
                    "residential_units",
                    "deed_restricted_units",
                    "total_job_spaces",
                    "zoned_du",
                    "zoned_du_underbuild",
                    "zoned_du_underbuild_nodev",
                    "first_building_type",
                ],
                axis=1,
                inplace=True,
            )
        parcel_output_2050_df = parcel_output_2050_df.add_suffix("_2050")
        parcel_output_2015_df = parcel_output_2015_df.add_suffix("_2015")

        # creating parcel summaries with 2050 and 2015 outputs, and parcel geographic categories
        parcel_sum_df = pd.merge(
            left=parcel_output_2050_df,
            right=parcel_output_2015_df,
            left_on="parcel_id_2050",
            right_on="parcel_id_2015",
            how="left",
        )
        parcel_sum_df.drop(["parcel_id_2015"], axis=1, inplace=True)
        parcel_sum_df = pd.merge(
            left=parcel_sum_df,
            right=parcel_building_output_sum_df,
            left_on="parcel_id_2050",
            right_on="parcel_id",
            how="left",
        ).fillna(0)
        parcel_sum_df.drop(["parcel_id", "parcel_id_2015"], axis=1, inplace=True)
        parcel_sum_df = parcel_sum_df.rename(columns={"parcel_id_2050": "parcel_id"})

        ################### Create parcel geography tagging
        # if us_runid == us_2050_DBP_Plus_runid:
        parcel_geo_df = parcel_geo_df[["PARCEL_ID", "juris", "fbpchcat"]]
        parcel_sum_df = pd.merge(
            left=parcel_geo_df,
            right=parcel_sum_df,
            left_on="PARCEL_ID",
            right_on="parcel_id",
            how="left",
        )
        parcel_sum_df.drop(["PARCEL_ID"], axis=1, inplace=True)
        # else:
        #    parcel_sum_df.drop(['fbpchcat_2015'], axis=1, inplace=True)
        #    parcel_sum_df = parcel_sum_df.rename(columns={'fbpchcat_2050': 'fbpchcat'}) #others should have geo tagging already

        ################### Create tract summary
        parcel_sum_df = pd.merge(
            left=parcel_sum_df,
            right=parcel_tract_crosswalk_df[
                ["parcel_id", "zone_id", "tract_id", "county"]
            ],
            on="parcel_id",
            how="left",
        )

        tract_sum_df = (
            parcel_sum_df.groupby(["tract_id"])[
                "tothh_2050", "tothh_2015", "hhq1_2050", "hhq1_2015"
            ]
            .sum()
            .reset_index()
        )

        # Adding displacement risk by tract from UDP
        tract_sum_df = pd.merge(
            left=tract_sum_df,
            right=udp_DR_df[["Tract", "DispRisk"]],
            left_on="tract_id",
            right_on="Tract",
            how="left",
        )

        # Adding county fips to tract id
        import math

        def fips_tract_coc(row):
            return (
                row["county_fips"] * (10 ** (int(math.log10(row["tract"])) + 1))
                + row["tract"]
            )

        # Adding CoC flag to tract_sum_df
        coc_flag_df["tract_id_coc"] = coc_flag_df.apply(
            lambda row: fips_tract_coc(row), axis=1
        )
        tract_sum_df = pd.merge(
            left=tract_sum_df,
            right=coc_flag_df[["tract_id_coc", "coc_flag_pba2050"]],
            left_on="tract_id",
            right_on="tract_id_coc",
            how="left",
        )

        # Adding CoC flag to parcel_sum_df
        parcel_sum_df = pd.merge(
            left=parcel_sum_df,
            right=coc_flag_df[["tract_id_coc", "coc_flag_pba2050"]],
            left_on="tract_id",
            right_on="tract_id_coc",
            how="left",
        )
        parcel_sum_df.drop(["tract_id_coc"], axis=1, inplace=True)

        # Merging SLR data with parcel summary file
        parcel_sum_df = pd.merge(
            left=parcel_sum_df,
            right=slr_plus,
            left_on="parcel_id",
            right_on="ParcelID",
            how="left",
        )
        parcel_sum_df = parcel_sum_df.rename(columns={"Plus": "SLR"})
        parcel_sum_df.drop(["ParcelID"], axis=1, inplace=True)

        normalize_factor_Q1Q2 = calculate_normalize_factor_Q1Q2(parcel_sum_df)
        normalize_factor_Q1 = calculate_normalize_factor_Q1(parcel_sum_df)

        #################### Create greenfield summary: currently defined as urban_footprint == 0
        greenfield_2050_df = pd.read_csv(
            (urbansim_runid + "_urban_footprint_summary_2050.csv")
        )
        greenfield_2015_df = pd.read_csv(
            (urbansim_runid + "_urban_footprint_summary_2015.csv")
        )
        greenfield_2050_df = greenfield_2050_df.rename(
            columns={"Unnamed: 0": "category"}
        )
        greenfield_2015_df = greenfield_2015_df.rename(
            columns={"Unnamed: 0": "category"}
        )
        greenfield_2050_df = greenfield_2050_df.add_suffix("_2050")
        greenfield_2015_df = greenfield_2015_df.add_suffix("_2015")
        greenfield_sum_df = pd.merge(
            left=greenfield_2050_df,
            right=greenfield_2015_df,
            left_on="category_2050",
            right_on="category_2015",
            how="left",
        )
        greenfield_sum_df = greenfield_sum_df.rename(
            columns={"category_2050": "category"}
        )

        calculate_Affordable2_deed_restricted_housing(
            run_num, parcel_sum_df, metrics_dict
        )
        calculate_Diverse1_LIHHinHRAs(
            run_num,
            parcel_sum_df,
            tract_sum_df,
            normalize_factor_Q1Q2,
            normalize_factor_Q1,
            metrics_dict,
        )
        calculate_Diverse2_LIHH_Displacement(
            run_num, parcel_sum_df, tract_sum_df, normalize_factor_Q1, metrics_dict
        )
        calculate_Healthy2_GreenfieldDev(run_num, greenfield_sum_df, metrics_dict)
        calculate_Healthy1_HHs_SLRprotected(run_num, parcel_sum_df, metrics_dict)
        # calculate_Healthy1_HHs_EQprotected(run_num, parcel_sum_df, metrics_dict)
        # calculate_Healthy1_HHs_WFprotected(run_num, parcel_sum_df, metrics_dict)
        calculate_Vibrant2_Jobs(run_num, parcel_sum_df, metrics_dict)


if __name__ == "__main__":

    # pd.set_option('display.width', 500)

    # Set UrbanSim inputs
    urbansim_run_location = "C:/Users/{}/Box/Modeling and Surveys/Urban Modeling/Bay Area UrbanSim/PBA50/".format(
        os.getenv("USERNAME")
    )
    us_2050_DBP_Plus_runid = "Draft Blueprint runs/Blueprint Plus Crossing (s23)/v1.7.1- FINAL DRAFT BLUEPRINT/run98"
    # us_2050_FBP_Oct_v3      = 'Final Blueprint runs/Final Blueprint (s24)/BAUS v2.2.1 (growth summary updates)/run325'
    # us_2050_FBP_Oct_v4      = 'Final Blueprint runs/Final Blueprint (s24)/BAUS v2.3.1 (devproj updates)/run242'
    # us_2050_FBP_Oct_v5      = 'Final Blueprint runs/Final Blueprint (s24)/BAUS v2.4/run152'
    # us_2050_FBP_Oct_v6      = 'Final Blueprint runs/Final Blueprint (s24)/BAUS v2.5/run327'
    # us_2050_FBP_Oct_v7      = 'Final Blueprint runs/Final Blueprint (s24)/BAUS v2.6.1 (growth summary updates)/run153'
    # us_2050_FBP_Oct_v8      = 'Final Blueprint runs/Final Blueprint (s24)/BAUS v2.7/run158'
    # us_2050_FBP_Oct_v9      = 'Final Blueprint runs/Final Blueprint (s24)/BAUS v2.8/run335'
    # us_2050_FBP_Oct_v10      = 'Final Blueprint runs/Final Blueprint (s24)/BAUS v2.8.1 (parcels geography update)/run159'
    # us_2050_FBP_Oct_v11      = 'Final Blueprint runs/Final Blueprint (s24)/BAUS v2.9/run160'
    # FBP_v8                      = 'Final Blueprint runs/Final Blueprint (s24)/BAUS v2.7'
    # FBP_v9                      = 'Final Blueprint runs/Final Blueprint (s24)/BAUS v2.8'
    # FBP_v10                    = "Final Blueprint runs/Final Blueprint (s24)/BAUS v2.8.1 (parcels geography update)"
    # FBP_v11                    = "Final Blueprint runs/Final Blueprint (s24)/BAUS v2.9/run160"
    FBP_v12 = "Final Blueprint runs/Final Blueprint (s24)/BAUS v2.10/run253"
    FBP_v13 = "Final Blueprint runs/Final Blueprint (s24)/BAUS v2.11/run161"
    FBP_v14 = "Final Blueprint runs/Final Blueprint (s24)/BAUS v2.12/run340"
    FBP_v19 = "Final Blueprint runs/Final Blueprint (s24)/BAUS v2.19/run262"
    FBP_v20 = "Final Blueprint runs/Final Blueprint (s24)/BAUS v2.20.1 (adds project to devproj)/run181"
    FBP_v22 = "Final Blueprint runs/Final Blueprint (s24)/BAUS v2.22/run352"
    FBP_v23 = "Final Blueprint runs/Final Blueprint (s24)/BAUS v2.23/run353"
    FBP_v25 = "Final Blueprint runs/Final Blueprint (s24)/BAUS v2.25/run182"
    FBP_v26 = "Final Blueprint runs/Final Blueprint (s24)/BAUS v2.26/run183"

    list_us_runid = [us_2050_DBP_Plus_runid, FBP_v25, FBP_v26]

    # Set external inputs
    metrics_source_folder = "C:/Users/{}/Box/Horizon and Plan Bay Area 2050/Equity and Performance/7_Analysis/Metrics/metrics_files/".format(
        os.getenv("USERNAME")
    )
    parcel_geography_file = (
        urbansim_run_location
        + "Current PBA50 Large General Input Data/2020_10_27_parcels_geography.csv"
    )
    parcel_tract_crosswalk_file = metrics_source_folder + "parcel_tract_crosswalk.csv"
    udp_file = metrics_source_folder + "udp_2017results.csv"
    coc_flag_file = metrics_source_folder + "COCs_ACS2018_tbl_TEMP.csv"
    slr_plus_file = metrics_source_folder + "slr_parcel_inundation_plus.csv"

    metrics_dict = OrderedDict()
    y1 = "2015"
    y2 = "2050"
    y_diff = "2015-50"

    # Calculate all metrics
    print("Starting metrics functions...")
    calc_urbansim_metrics()
    print(
        "*****************#####################Completed urbansim_metrics#####################*******************"
    )

    # Write output
    idx = pd.MultiIndex.from_tuples(
        metrics_dict.keys(), names=["modelrunID", "metric", "variable", "year"]
    )
    metrics = pd.Series(metrics_dict, index=idx, name="values").to_frame().reset_index()
    metrics.set_index(["modelrunID", "metric", "variable", "year"], inplace=True)
    metrics = metrics.stack().unstack("year").reset_index()
    metrics = metrics[["modelrunID", "metric", "variable", "2015", "2050", "2015-50"]]

    out_filename = "C:/Users/{}/Box/Modeling and Surveys/Urban Modeling/Bay Area UrbanSim/PBA50/Visualizations/urbansim_metrics.csv".format(
        os.getenv("USERNAME")
    )
    metrics.to_csv(out_filename, index=False, header=True, sep=",", float_format="%.9f")

    print("Wrote {}".format(out_filename))
