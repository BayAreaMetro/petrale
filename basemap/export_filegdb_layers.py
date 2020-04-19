USAGE = """
  Pass in a file geodatabase and layer name and this will export into the current working directory:

  1) a shapefile if the layer is a feature class
  2) a dbf if the layer is a table

  To see a list of the feature classes and/or tables, pass the geodatabase name only.

"""

import argparse, os, sys, time
import arcpy

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=USAGE, formatter_class=argparse.RawDescriptionHelpFormatter,)
    parser.add_argument("geodatabase",  metavar="geodatabase.gdb", help="File geodatabase with layer export")
    parser.add_argument("--layer", help="Layer to export")

    args = parser.parse_args()

    arcpy.env.workspace = args.geodatabase

    if not args.layer:
        print("workspace: {}".format(arcpy.env.workspace))
        for dataset in arcpy.ListDatasets():
            print("  dataset: {}".format(dataset))
            print("    feature classes: {} ".format(arcpy.ListFeatureClasses(feature_dataset=dataset)))
    
        print("  feature classes: {} ".format(arcpy.ListFeatureClasses()))
        print("  tables: {} ".format(arcpy.ListTables()))

    if args.layer in arcpy.ListFeatureClasses():

        result = arcpy.GetCount_management(os.path.join(args.geodatabase, args.layer))
        print("Feature Class []{} has {} rows".format(os.path.join(args.geodatabase, args.layer), result[0]))

        # outfile = "{}.geojson".format(args.layer)
        # arcpy.FeaturesToJSON_conversion(os.path.join(args.geodatabase, args.layer), outfile, geoJSON='GEOJSON')
        # print("Wrote {}".format(outfile))

        outfile = "{}.shp".format(args.layer)
        arcpy.FeatureClassToShapefile_conversion(os.path.join(args.geodatabase, args.layer), Output_Folder=".")
        print("Write {}".format(outfile))

    if args.layer in arcpy.ListTables():

        result = arcpy.GetCount_management(os.path.join(args.geodatabase, args.layer))
        print("Table [{}] has {} rows".format(os.path.join(args.geodatabase, args.layer), result[0]))

        outfile = "{}.csv".format(args.layer)
        arcpy.TableToTable_conversion(os.path.join(args.geodatabase, args.layer), out_path=".", out_name=outfile)
        print("Write {}".format(outfile))

        # outfile = "{}.dbf".format(args.layer)
        # arcpy.TableToTable_conversion(os.path.join(args.geodatabase, args.layer), out_path=".", out_name=outfile)
        # print("Wrote {}".format(outfile))

