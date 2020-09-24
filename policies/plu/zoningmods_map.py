import argparse, os, sys, time
import arcpy

# python zoningmods_map.py input_gdb "2020 03 12\2020 03 12\smelt.gdb" output_gdb "Final_Blueprint_Land_Use_Strategies.gdb" p10_layer "p10" zmods_attr_csv "p10_pba50_attr_20200915.csv"
# zmods_csv "zoning_mods_24.csv" join_field "PARCEL_ID" dissolve_field "fbpzoningm" zmods_version "09162020"

# input_gdb = "C:\Users\ywang\Documents\ArcGIS\Projects\Final_Blueprint_Land_Use_Strategies\2020 03 12\smelt.gdb"
# output_gdb = "C:\Users\ywang\Documents\ArcGIS\Projects\Final_Blueprint_Land_Use_Strategies\Final_Blueprint_Land_Use_Strategies.gdb"
# join_field = "PARCEL_ID"
# dissolve_field = "fbpzoningm"
# zmods_version = "20200916"

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=USAGE, formatter_class=argparse.RawDescriptionHelpFormatter,)
    parser.add_argument("input_gdb",      metavar="input.gdb",   help="Input geodatabase")
    parser.add_argument("output_gdb",     metavar="output.gdb",  help="Output geodatabase")
    parser.add_argument("p10_layer",      metavar="p10_layer",   help="p10 parcel layer")
    parser.add_argument("zmods_attr_csv", metavar="zmods_attr_csv", help="zoningmods_attribute")
    parser.add_argument("zmods_csv",      metavar="zmods_csv",  help="zoning_mods")
    parser.add_argument("join_field",     metavar="join_field",  help="Join field for parcel-zmods join")
    parser.add_argument("join_type",      choices=["KEEP_ALL","KEEP_COMMON"], default="KEEP_ALL", help="Outer join vs inner join.  Default is KEEP_ALL, or outer")
    parser.add_argument("dissolve_field", metavar="dissolve_field",  help="Dissolve field")
    parser.add_argument("zmods_version",  metavar="zmods_version",  help="Version of zoning_mods_24, use date")


    arcpy.env.workspace = args.output_gdb

    ## Join zmods_attr layer to p10 parcel layer

    # read zmods_attr file
    zmod_fb_col = ['PARCEL_ID', 'geom_id', 'fbpzoningm']
    zmod_attr = pandas.read_csv(args.zmods_attr_csv, 
                                usecols = zmods_fb_col)
    # target layer
    p10 = os.path.join(args.input_gdb, args.p10_layer)

    p_zmod_attr_join = arcpy.AddJoin_management(p10, args.join_field,
                                                zmod_attr, args.join_field,
                                                join_type=args.join_type)

    p_zmod_attr_joined = "p10_zmod_attr_joined"

    # delete the layer if it already exists in the output gdb
    if arcpy.Exists(p_zmod_attr_joined):
        arcpy.Delete_management(p_zmod_attr_joined)
        print("Found {} -- deleting".format(p_zmod_attr_joined))

    # save it
    arcpy.CopyFeatures_management(p_zmod_attr_join, os.path.join(args.output_gdb, p_zmod_attr_joined))
    print("Completed creation of {}".format(os.path.join(args.output_gdb, p_zmod_attr_joined)))


    ## Dissolve the joint parcel-zmods layer by zoningmod category

    p_zmod_dissolved = os.path.join(args.output_gdb, 'p10_zmods_dissolved')
    arcpy.Dissolve_management(p_zmod_attr_join, p_zmod_dissolved,
                              args.dissolve_field, "")


    ## Join the dissolved parcels to zoning_mods
    
    # read zoning_mods file
    zmods = pandas.read_csv(args.zmods_csv)

    p_zmods_join = arcpy.AddJoin_management(p_zmod_dissolved, args.dissolve_field,
                                            zmods, args.dissolve_field,
                                            join_type=args.join_type)

    p_zmods_joined = "p10_fb_zoningmods_{}".format(zmods_version)

    # delete the layer if it already exists in the output gdb
    if arcpy.Exists(p_zmods_joined):
        arcpy.Delete_management(p_zmods_joined)
        print("Found {} -- deleting".format(p_zmods_joined))

    # save it
    arcpy.CopyFeatures_management(p_zmod_attr_join, os.path.join(args.output_gdb, p_zmods_joined))
    print("Completed creation of {}".format(os.path.join(args.output_gdb, p_zmods_joined)))