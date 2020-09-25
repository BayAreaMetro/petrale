USAGE = """

Create zoning_mods-level spatial data in three steps:
1) join p10 parcel data with parcel-level zoningmods_attributes.csv
2) dissolve the joined layer by zoning_mods geography (fbpzoningm for Final Blueprint)
3) join the dissolved layer with zoning_mods.csv which contains upzoning information

Run the script in ArcGIS env. Example directory: 
C:\\Users\\ywang\\AppData\\Local\\Programs\\ArcGIS\\Pro\\bin\\Python\\envs\\arcgispro-py3

"""

# example run: 
# python zoningmods_map.py -folder "M:\Data\GIS layers\Blueprint Land Use Strategies\Final_Blueprint"
#                          -input_gdb "2020 03 12\smelt.gdb" 
#                          -output_gdb "Final_Blueprint_Land_Use_Strategies.gdb" 
#                          -p10_layer "p10" 
#                          -zmods_attr_csv "p10_pba50_attr_20200915.csv" 
#                          -zmods_csv "zoning_mods_24.csv" 
#                          -join_field "PARCEL_ID" 
#                          -join_type "KEEP_ALL" 
#                          -dissolve_field "fbpzoningm" 


import argparse, os, sys, time
import arcpy, pandas


if __name__ == '__main__':

    start = time.time()

    parser = argparse.ArgumentParser(description=USAGE, formatter_class=argparse.RawDescriptionHelpFormatter,)
    parser.add_argument("-folder",         metavar="folder",      help="Working folder")
    parser.add_argument("-input_gdb",      metavar="input.gdb",   help="Input geodatabase")
    parser.add_argument("-output_gdb",     metavar="output.gdb",  help="Output geodatabase")
    parser.add_argument("-p10_layer",      metavar="p10_layer",   help="p10 parcel layer")
    parser.add_argument("-zmods_attr_csv", metavar="zmods_attr.csv", help="zoningmods_attribute")
    parser.add_argument("-zmods_csv",      metavar="zmods.csv",  help="zoning_mods")
    parser.add_argument("-join_field",     metavar="join_field",  help="Join field for parcel-zmods join")
    parser.add_argument("-join_type",      choices=["KEEP_ALL","KEEP_COMMON"], default="KEEP_ALL", help="Outer join vs inner join.  Default is KEEP_ALL, or outer")
    parser.add_argument("-dissolve_field", metavar="dissolve_field",  help="Dissolve field")

    args = parser.parse_args()
    print(" {:15}: {}".format("folder",   args.folder))
    print(" {:15}: {}".format("input_gdb",   args.input_gdb))
    print(" {:15}: {}".format("output_gdb",   args.output_gdb))
    print(" {:15}: {}".format("p10_layer",   args.p10_layer))
    print(" {:15}: {}".format("zmods_attr_csv", args.zmods_attr_csv))
    print(" {:15}: {}".format("zmods_csv", args.zmods_csv))
    print(" {:15}: {}".format("join_field",  args.join_field))
    print(" {:15}: {}".format("join_type",   args.join_type))
    print(" {:15}: {}".format("dissolve_field",  args.dissolve_field))


    # create output_gdb if not exists already
    if not os.path.exists(os.path.join(args.folder,args.output_gdb)):
        (head,tail) = os.path.split(os.path.join(args.folder,args.output_gdb))
        print("head: {} tail: {}".format(head, tail))
        if head=="": head="."
        arcpy.CreateFileGDB_management(head, tail)
        print("Created {}".format(os.path.join(args.folder,args.output_gdb)))

    arcpy.env.workspace = os.path.join(args.folder,args.output_gdb)

    ########## Join zmods_attr layer to p10 parcel layer ##########

    # read zmods_attr file
    zmod_fb_col = ['PARCEL_ID', 'fbpzoningm']
    zmod_attr = pandas.read_csv(os.path.join(args.folder, args.zmods_attr_csv), 
                                usecols = zmod_fb_col)
    print("Read {} records from {}, with {} unique PARCEL_IDs and {} fbpzoningm".format(os.path.join(args.folder, args.zmods_attr_csv),
                                                                                        zmod_attr.shape[0],
                                                                                        len(zmod_attr.PARCEL_ID.unique()),
                                                                                        len(zmod_attr.fbpzoningm.unique())))
    # copy the table to output_gdb
    print("Copy {} to {}".format(args.zmods_attr_csv, 
                                 os.path.join(args.folder, args.output_gdb)))
    
    zmod_attr_table = os.path.splitext(args.zmods_attr_csv)[0]

    # delete table if there's already one there by that name
    if arcpy.Exists(zmod_attr_table):
        arcpy.Delete_management(zmod_attr_table)
        print("Found {} -- deleting".format(zmod_attr_table))

    zmod_attr_values = numpy.array(numpy.rec.fromrecords(zmod_attr.values))
    zmod_attr_values.dtype.names = tuple(zmod_attr.dtypes.index.tolist())
    arcpy.da.NumPyArrayToTable(zmod_attr_values, os.path.join(args.folder, args.output_gdb, zmod_attr_table))
    print("Created {}".format(os.path.join(args.folder, args.output_gdb, zmod_attr_table)))

    # target layer
    p10 = os.path.join(args.folder, args.input_gdb, args.p10_layer)
    print("Target layer: {}".format(p10))

    # copy the layer to output_gdb
    print("Copy {} to {}".format(p10, 
                                 os.path.join(args.folder, args.output_gdb)))

    # delete the layer if it already exists in the output gdb
    if arcpy.Exists(args.p10_layer):
        arcpy.Delete_management(args.p10_layer)
        print("Found {} -- deleting".format(args.p10_layer))

    # copy the input to output_gdb with the same name
    arcpy.CopyFeatures_management(os.path.join(args.folder, args.input_gdb, args.p10_layer),
                                  os.path.join(args.folder, args.output_gdb, args.p10_layer))

    # join table to the target layer
    print("Joining {} with {}".format(os.path.join(args.folder, args.output_gdb, args.p10_layer),
                                      os.path.join(args.folder, args.output_gdb, zmod_attr_table)))

    p_zmod_attr_join = arcpy.AddJoin_management(args.p10_layer, args.join_field,
                                                zmod_attr_table, args.join_field,
                                                join_type=args.join_type)

    zmod_attr_version = args.zmods_attr_csv.split('.')[0].split('_')[-1]
    p_zmod_attr_joined = "p10_zmod_attr_joined_{}".format(zmod_attr_version)

    # delete the layer if it already exists in the output gdb
    if arcpy.Exists(p_zmod_attr_joined):
        arcpy.Delete_management(p_zmod_attr_joined)
        print("Found {} -- deleting".format(p_zmod_attr_joined))

    # save it
    arcpy.CopyFeatures_management(p_zmod_attr_join, os.path.join(args.folder, args.output_gdb, p_zmod_attr_joined))
    print("Completed creation of {}".format(os.path.join(args.folder, args.output_gdb, p_zmod_attr_joined)))
    field_names = [f.name for f in arcpy.ListFields(p_zmod_attr_joined)]
    print("{} has the following fields: {}".format(p_zmod_attr_joined,
                                                   field_names))

    ########## Dissolve the joint parcel-zmods layer by zoningmod category ##########

    print("Dissolve {} on field: {}".format(p_zmod_attr_joined,
                                            [zmod_attr_table+'_'+args.dissolve_field]))
    p_zmod_dissolved = 'p10_zmods_dissolved_{}'.format(zmod_attr_version)

    # delete the layer if it already exists in the output gdb
    if arcpy.Exists(p_zmod_dissolved):
        arcpy.Delete_management(p_zmod_dissolved)
        print("Found {} -- deleting".format(p_zmod_dissolved))

    arcpy.Dissolve_management(p_zmod_attr_joined,
                              os.path.join(args.folder, args.output_gdb, p_zmod_dissolved),
                              [zmod_attr_table+'_'+args.dissolve_field], "")

    field_names = [f.name for f in arcpy.ListFields(p_zmod_dissolved)]
    print("Dissolve completed; {} has {} records and the following fields \n{}".format(
            p_zmod_dissolved,
            arcpy.GetCount_management(p_zmod_dissolved),
            field_names))

    ########## Join the dissolved parcels to zoning_mods ##########
    
    # read zoning_mods file
    zmods = pandas.read_csv(os.path.join(args.folder,args.zmods_csv))

    print("Read {} records from {}, with {} fbpzoningm and the following fields: \n{}".format(
            zmods.shape[0],
            os.path.join(args.folder,args.zmods_csv),       
            len(zmods.fbpzoningm.unique()),
            list(zmods)))

    # copy the table to output_gdb
    print("Copy {} to {}".format(args.zmods_csv, 
                                 os.path.join(args.folder, args.output_gdb)))
    zmods_table = os.path.splitext(args.zmods_csv)[0]

    # delete table if there's already one there by that name
    if arcpy.Exists(zmods_table):
        arcpy.Delete_management(zmods_table)
        print("Found {} -- deleting".format(zmods_table))

    zmods_values = numpy.array(numpy.rec.fromrecords(zmods.values))
    zmods_values.dtype.names = tuple(zmods.dtypes.index.tolist())
    arcpy.da.NumPyArrayToTable(zmods_values, os.path.join(args.folder, args.output_gdb, zmods_table))
    print("Created {}".format(os.path.join(args.folder, args.output_gdb, zmods_table)))

    # join table to the dissolved layer
    print("Joining {} with {}".format(os.path.join(args.folder, args.output_gdb, p_zmod_dissolved),
                                      os.path.join(args.folder, args.output_gdb, zmods_table)))    

    p_zmods_join = arcpy.AddJoin_management(p_zmod_dissolved, zmod_attr_table+'_'+args.dissolve_field,
                                            zmods_table, args.dissolve_field,
                                            join_type=args.join_type)

    zmods_version = args.zmods_csv.split('.')[0].split('_')[-1]
    p_zmods_joined = "p10_fb_zoningmods_{}".format(zmods_version)

    # delete the layer if it already exists in the output gdb
    if arcpy.Exists(p_zmods_joined):
        arcpy.Delete_management(p_zmods_joined)
        print("Found {} -- deleting".format(p_zmods_joined))

    # save it
    arcpy.CopyFeatures_management(p_zmods_join, os.path.join(args.folder, args.output_gdb, p_zmods_joined))
    print("Completed creation of {}".format(os.path.join(args.folder, args.output_gdb, p_zmods_joined)))

    print("{} has {} records".format(p_zmods_joined, 
                                     arcpy.GetCount_management(p_zmods_joined)[0]))

    print("Script took {0:0.1f} minutes".format((time.time()-start)/60.0))