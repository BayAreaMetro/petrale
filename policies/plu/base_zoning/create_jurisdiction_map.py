# for arcpy:
# set PATH=C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3
USAGE = """

Creates BASIS vs PBA40 maps comparing DUA, etc by jurisdiction.

"""

import argparse, collections, csv, datetime, os, sys, time
import arcpy, numpy, pandas

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
    WORKSPACE_GDB   = "C:\\Users\\lzorn\\Documents\\UrbanSim_BASIS_zoning\\UrbanSim_BASIS_zoning.gdb"
    ARCGIS_PROJECT  = "C:\\Users\\lzorn\\Documents\\UrbanSim_BASIS_zoning\\UrbanSim_BASIS_zoning.aprx"

elif os.getenv("USERNAME")=="ywang":
    WORKSPACE_GDB   =  "C:\\Users\\{}\\Documents\\Python Scripts\\UrbanSim_BASIS_zoning\\UrbanSim_BASIS_zoning.gdb".format(os.getenv("USERNAME"))
    ARCGIS_PROJECTS = ["C:\\Users\\{}\\Documents\\Python Scripts\\UrbanSim_BASIS_zoning\\UrbanSim_BASIS_zoning_intensity.aprx".format(os.getenv("USERNAME")),
                       "C:\\Users\\{}\\Documents\\Python Scripts\\UrbanSim_BASIS_zoning\\UrbanSim_BASIS_zoning_devType.aprx".format(os.getenv("USERNAME"))]


if __name__ == '__main__':

    JURISDICTION_TO_COUNTY = collections.OrderedDict()

    with open(COUNTY_JURISDICTIONS_CSV, mode='r') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            JURISDICTION_TO_COUNTY[row['Jurisdiction']] = row['County']
    # print(JURISDICTION_TO_COUNTY)
    # for testing
    # JURISDICTION_TO_COUNTY = collections.OrderedDict()
    # JURISDICTION_TO_COUNTY["Alameda"      ] = "Alameda"
    # JURISDICTION_TO_COUNTY["Orinda"       ] = "Contra Costa"
    # JURISDICTION_TO_COUNTY["Mill Valley"  ] = "Marin"
    # JURISDICTION_TO_COUNTY["Napa"         ] = "Napa"
    # JURISDICTION_TO_COUNTY["Menlo Park"   ] = "San Mateo"
    # JURISDICTION_TO_COUNTY["Santa Clara"  ] = "Palo Alto"
    # JURISDICTION_TO_COUNTY["San Francisco"] = "San Francisco"
    # JURISDICTION_TO_COUNTY["Dixon"        ] = "Solano"
    # JURISDICTION_TO_COUNTY["Petaluma"     ] = "Sonoma"

    # set the workspace
    arcpy.env.workspace = WORKSPACE_GDB
    now_str = datetime.datetime.now().strftime("%Y/%m/%d, %H:%M")

    source_str = "Created by create_jurisdiction_map.py " \
                 "(https://github.com/BayAreaMetro/petrale/blob/master/policies/plu/base_zoning/create_jurisdiction_map.py) on {}. " \
                 "Data from 2020_04_30_p10_plu_boc_allAttrs.csv (https://mtcdrive.box.com/s/u92l9nqen5yg5iphgqajly4z4mr0fv1a)".format(now_str)

    metrics_names = ['DUA',
                     'FAR',
                     'HEIGHT',
                     'Allow_HM_(Multi-family Housing)',
                     'Allow_MR_(Mixed-use Residential)',
                     'Allow_RS_(Retail)',
                     'Allow_OF_(Office)']

    prev_jurisdiction = "Palo Alto"
    prev_juris_code   = "palo_alto"

    for jurisdiction in JURISDICTION_TO_COUNTY.keys():

        for arc_project in ARCGIS_PROJECTS:

            # start fresh
            aprx       = arcpy.mp.ArcGISProject(arc_project)
            layouts    = aprx.listLayouts()
            maps       = aprx.listMaps()
            juris_lyr  = {} # key: "BASIS" or "PBA40"

            juris_code = jurisdiction.lower().replace(" ","_").replace(".","")
            print("Creating map for {} ({})".format(jurisdiction, juris_code))

            for my_map in maps:
                print("  Processing map {}".format(my_map.name))
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

            for layout in layouts:
                print("  Found layout {}".format(layout.name))

                for metrics_name in metrics_names:

                    if layout.name == "Layout_"+metrics_name:
        	            print("  Processing layout {}".format(layout.name))
        	            for element in layout.listElements():
        	                print("    Processing element {}: {}".format(element.name, element))

        	                if element.name == "Source":
        	                    element.text = source_str
        	                if element.name == "Jurisdiction":
        	                    element.text = jurisdiction

        	                # zoom to the jurisdiction
        	                if element.name.find("Map Frame") >= 0:
        	                    if element.name.endswith("BASIS"):
        	                        map_type = "BASIS_"+metrics_name
        	                    else:
        	                        map_type = "PBA40_"+metrics_name

        	                    # get the jurisdiction layer extent
        	                    layer_extent = element.getLayerExtent(juris_lyr[map_type])
        	                    # apply extent to mapframe camera
        	                    element.camera.setExtent(layer_extent)

        	            juris_pdf = "{}_{}.pdf".format(juris_code, metrics_name)
        	            layout.exportToPDF(juris_pdf)
        	            print("Wrote {}".format(juris_pdf))

            # done with jurisdiction
            print("")

            # sys.exit()

