# for arcpy:
# set PATH=C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3
USAGE = """

Creates BASIS vs PBA40 maps comparing DUA, etc by jurisdiction.
Includes information on whether or not the BASIS data was reviewed (for relevant types of data) and
whether or not UrbanSim input is currently configured to use the BASIS data.

"""

import argparse, collections, csv, datetime, os, sys, time
import arcpy, numpy, pandas, xlrd

COUNTY_JURISDICTIONS_CSV = "M:\\Data\\GIS layers\\Jurisdictions\\county_jurisdictions.csv"

if os.getenv("USERNAME")=="lzorn":
    # This was created by joining output of 1_PLU_BOC_data_combine.ipynb with p10
    #
    # e.g. using the command
    #
    # python import_filegdb_layers.py "M:\Data\GIS layers\UrbanSim smelt\2020 03 12\smelt.gdb" p10
    #    "C:\Users\lzorn\Box\Modeling and Surveys\Urban Modeling\Bay Area UrbanSim 1.5\PBA50\Policies\Base zoning\outputs\2020_04_30_p10_plu_boc_allAttrs.csv"
    #    PARCEL_ID UrbanSim_BASIS_zoning.gdb
    #
    WORKSPACE_DIR   = "M:\\Data\\GIS layers\\UrbanSim_BASIS_zoning"
    WORKSPACE_GDB   = os.path.join(WORKSPACE_DIR,"UrbanSim_BASIS_zoning.gdb")
    ARCGIS_PROJECTS = [os.path.join(WORKSPACE_DIR,"UrbanSim_BASIS_zoning_intensity.aprx"),
                       os.path.join(WORKSPACE_DIR,"UrbanSim_BASIS_zoning_devType.aprx")]

    # location of BASIS_Local_Jurisdiction_Review_Summary.xlsx (https://mtcdrive.box.com/s/s2w68pnboa3gzq5z228mqbxtdehgdcxd)
    JURIS_REVIEW    = "C:\\Users\\lzorn\\Box\\BASIS Land Use Data Store\\Jurisdiction Review\\BASIS_Local_Jurisdiction_Review_Summary.xlsx"

    PETRALE_GITHUB_DIR = "X:\\petrale"
    # location of current hybrid configuration
    HYBRID_CONFIG   = os.path.join(PETRALE_GITHUB_DIR, "policies", "plu", "base_zoning", "hybrid_index", "idx_BASIS_devType_intensity_partial.csv")

elif os.getenv("USERNAME")=="ywang":
    WORKSPACE_DIR   = "C:\\Users\\ywang\\Documents\\Python Scripts\\UrbanSim_BASIS_zoning"
    WORKSPACE_GDB   = os.path.join(WORKSPACE_DIR,"UrbanSim_BASIS_zoning.gdb")
    ARCGIS_PROJECTS = [os.path.join(WORKSPACE_DIR,"UrbanSim_BASIS_zoning_intensity.aprx"),
                       os.path.join(WORKSPACE_DIR,"UrbanSim_BASIS_zoning_devType.aprx")]

    # location of BASIS_Local_Jurisdiction_Review_Summary.xlsx (https://mtcdrive.box.com/s/s2w68pnboa3gzq5z228mqbxtdehgdcxd)
    JURIS_REVIEW    = "C:\\Users\\ywang\\Box\\BASIS Land Use Data Store\\Jurisdiction Review\\BASIS_Local_Jurisdiction_Review_Summary.xlsx"

    PETRALE_GITHUB_DIR = "C:\\Users\\ywang\\Documents\\GitHub\\petrale"
    # location of current hybrid configuration
    HYBRID_CONFIG   = os.path.join(PETRALE_GITHUB_DIR, "policies", "plu", "base_zoning", "hybrid_index", "idx_BASIS_devType_intensity_partial.csv")


if __name__ == '__main__':
    pandas.options.display.max_rows = 999

    parser = argparse.ArgumentParser(description=USAGE, formatter_class=argparse.RawDescriptionHelpFormatter,)
    parser.add_argument("--jurisdiction",  help="Jurisdiction. If none passed, will process all", nargs='+', )
    parser.add_argument("--metric",        help="Metrics type(s). If none passed, will process all", nargs='+',
                                           choices=["DUA","FAR","height","HM","MR","RS","OF"])
    args = parser.parse_args()
    print(args)

    # read list of jurisdictions
    JURISDICTION_TO_COUNTY = collections.OrderedDict()

    with open(COUNTY_JURISDICTIONS_CSV, mode='r') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            JURISDICTION_TO_COUNTY[row['Jurisdiction']] = row['County']
    
    # read jurisdiction review status for BASIS
    juris_review_df = pandas.read_excel(JURIS_REVIEW, sheet_name="Sheet 1", header=1)
    juris_review_df = juris_review_df.loc[ pandas.notnull(juris_review_df.Jurisdiction) ]
    juris_review_df.set_index("Jurisdiction", inplace=True)
    # print(juris_review_df)
    juris_review_dict = juris_review_df.to_dict(orient="index")
    # print(juris_review_dict["Berkeley"])
    # e.g. {
    #  'County': 'Alameda', 
    #  'Check Allowable Building Heights': True, 
    #  'Check Development Pipeline': True,
    #  'Check Floor Area Ratio': True,
    #  'Check Residential Densities': True,
    #  'Check Spheres of Influence': True,
    #  'Check Urban Growth Boundaries': True,
    #  'Check Zoning Codes': True,
    #  'Check Zoning Description': True,
    #  'Zoning Document': True,
    #  'Zoning Map': True,
    #  'Zoning Ordinance Effective Date': True,
    #  'Check Zoning Parcel Map': True,
    #  'Percent Complete': 1
    # }

    # read hybrid configuration 
    hybrid_config_df = pandas.read_csv(HYBRID_CONFIG)
    # print(hybrid_config_df.head())
    hybrid_config_df.set_index("juris_name", inplace=True)
    hybrid_config_dict = hybrid_config_df.to_dict(orient="index")
    # print(hybrid_config_dict["berkeley"])
    # e.g. {
    #  'juris_id': 'berk',
    #  'county': 'ala',
    #  'OF_idx': 0,
    #  'HO_idx': 0,
    #  'SC_idx': 0,
    #  'IL_idx': 0,
    #  'IW_idx': 0, 
    #  'IH_idx': 0,
    #  'RS_idx': 0,
    #  'RB_idx': 0,
    #  'MR_idx': 0,
    #  'MT_idx': 0,
    #  'ME_idx': 0,
    #  'HS_idx': 0,
    #  'HT_idx': 0,
    #  'HM_idx': 1,
    #  'MAX_DUA_idx': 0,
    #  'MAX_FAR_idx': 0,
    #  'MAX_HEIGHT_idx': 0,
    #  'proportion_adj_dua': 1,
    #  'proportion_adj_far': 1, 
    #  'proportion_adj_height': 1
    # }

    # if jurisdictino passed, remove others and only process that one
    if args.jurisdiction:
        JURISDICTION_TO_COUNTY_arg = {}
        for juris in args.jurisdiction:
            if juris not in JURISDICTION_TO_COUNTY:
                print("Jurisdiction [{}] not found in {}".format(juris, COUNTY_JURISDICTIONS_CSV))
            else:
                JURISDICTION_TO_COUNTY_arg[juris] = JURISDICTION_TO_COUNTY[juris]

        # use that instead
        JURISDICTION_TO_COUNTY = JURISDICTION_TO_COUNTY_arg
    print("Will process jurisdictions: {}".format(JURISDICTION_TO_COUNTY.keys()))

    # set the workspace
    arcpy.env.workspace = WORKSPACE_GDB
    now_str = datetime.datetime.now().strftime("%Y/%m/%d, %H:%M")

    source_str = "<FNT size=\"7\">Created by " \
                 "<ITA>https://github.com/BayAreaMetro/petrale/blob/master/policies/plu/base_zoning/create_jurisdiction_map.py</ITA> on {}. " \
                 "Hybrid config: <ITA>https://github.com/BayAreaMetro/petrale/blob/master/policies/plu/base_zoning/hybrid_index/idx_BASIS_devType_intensity_partial.csv</ITA></FNT>".format(now_str)

    METRICS_DEF = collections.OrderedDict([
                   # ArcGIS project, detail name, BASIS jusidiction col, hybrid config col
        ('DUA'    ,["UrbanSim_BASIS_zoning_intensity.aprx", 'DUA',                              'Check Residential Densities',     'MAX_DUA_idx'   ]),
        ('FAR'    ,["UrbanSim_BASIS_zoning_intensity.aprx", 'FAR',                              'Check Floor Area Ratio',          'MAX_FAR_idx'   ]),
        ('height' ,["UrbanSim_BASIS_zoning_intensity.aprx", 'HEIGHT',                           'Check Allowable Building Heights','MAX_HEIGHT_idx']),
        ('HM'     ,["UrbanSim_BASIS_zoning_devType.aprx",   'Allow_HM_(Multi-family Housing)',  None,                              'HM_idx'        ]),
        ('MR'     ,["UrbanSim_BASIS_zoning_devType.aprx",   'Allow_MR_(Mixed-use Residential)', None,                              'MR_idx'        ]),
        ('RS'     ,["UrbanSim_BASIS_zoning_devType.aprx",   'Allow_RS_(Retail)',                None,                              'RS_idx'        ]),
        ('OF'     ,["UrbanSim_BASIS_zoning_devType.aprx",   'Allow_OF_(Office)',                None,                              'OF_idx'        ]),
    ])

    # these are the metrics we'll process
    if args.metric:
        metric_list = args.metric
    else:
        metric_list = METRICS_DEF.keys()
    print("Will process metrics: {}".format(metric_list))

    prev_jurisdiction = "Palo Alto"
    prev_juris_code   = "palo_alto"

    for jurisdiction in JURISDICTION_TO_COUNTY.keys():

        juris_code = jurisdiction.lower().replace(" ","_").replace(".","")
        print("Creating map for {} ({})".format(jurisdiction, juris_code))

        for metric in metric_list:

            print("  Creating map for metric {}".format(metric))
            arc_project      = METRICS_DEF[metric][0]
            metric_name      = METRICS_DEF[metric][1]
            basis_check_col  = METRICS_DEF[metric][2]
            basis_hybrid_col = METRICS_DEF[metric][3]

            basis_check_val = False
            if basis_check_col:
                if jurisdiction not in juris_review_dict:
                    print("Couldn't find jurisdiction {} in BASIS jurisdiction review {}".format(jurisdiction, JURIS_REVIEW))
                else:
                    basis_check_val = juris_review_dict[jurisdiction][basis_check_col]
                    print("  BASIS check val for {}: {}".format(basis_check_col, basis_check_val))
            basis_hybrid_val = hybrid_config_dict[juris_code][basis_hybrid_col]
            print("  BASIS hybrid config val for {}: {}".format(basis_hybrid_col, basis_hybrid_val))

            # start fresh
            aprx       = arcpy.mp.ArcGISProject(arc_project)
            layouts    = aprx.listLayouts("Layout_{}".format(metric_name))
            maps       = aprx.listMaps()
            juris_lyr  = {} # key: "BASIS" or "PBA40"

            assert(len(layouts)==1)

            for my_map in maps:
                if my_map.name.endswith(metric) or my_map.name.endswith(metric_name):
                    # process this one
                    print("  Processing map {}".format(my_map.name))
                else:
                    print("  Skipping map {}".format(my_map.name))
                    continue

                for layer in my_map.listLayers():
                    if not layer.isFeatureLayer: continue
                    print("    Processing layer {}: {}".format(layer.name, layer))
                    print("      Definition query: {}".format(layer.definitionQuery))
                    # modify to current jurisdiction
                    layer.definitionQuery = layer.definitionQuery.replace(prev_jurisdiction, jurisdiction)
                    layer.definitionQuery = layer.definitionQuery.replace(prev_juris_code,   juris_code)
                    print("      => Definition query: {}".format(layer.definitionQuery))

                    # save this for extent
                    if layer.name == "Jurisdictions - primary":
                        juris_lyr[my_map.name] = layer
                        print("      saving juris_lyr[{}]".format(my_map.name))

            layout = layouts[0]


            print("  Processing layout {}".format(layout.name))
            for element in layout.listElements():
                print("    Processing element {}: {}".format(element.name, element))

                if element.name == "Source":
                    element.text = source_str
                if element.name == "Jurisdiction":
                    element.text = jurisdiction

                if element.name == "juris_review_false":
                    element.visible = not basis_check_val   # visible if basis_check_val==False
                if element.name == "juris_review_true":
                    element.visible =  basis_check_val      # visible if basis_check_val==True

                if element.name == "arrow_basis":
                    element.visible = basis_hybrid_val      # visible if basis_hybrid_val==True
                if element.name == "input_basis":
                    element.visible = basis_hybrid_val      # visible if basis_hybrid_val==True

                if element.name == "arrow_pba40":
                    element.visible = not basis_hybrid_val  # visible if basis_hybrid_val==False
                if element.name == "input_pba40":
                    element.visible = not basis_hybrid_val  # visible if basis_hybrid_val==False


                # zoom to the jurisdiction
                if element.name.find("Map Frame") >= 0:
                    if element.name.endswith("BASIS"):
                        map_type = "BASIS_"+metric_name
                    else:
                        map_type = "PBA40_"+metric_name

                    # get the jurisdiction layer extent
                    layer_extent = element.getLayerExtent(juris_lyr[map_type])
                    # apply extent to mapframe camera
                    element.camera.setExtent(layer_extent)

            juris_pdf = "{}_{}.pdf".format(juris_code, metric_name)
            layout.exportToPDF(juris_pdf)
            print("  Wrote {}".format(juris_pdf))

        # done with jurisdiction
        print("")

            # sys.exit()

