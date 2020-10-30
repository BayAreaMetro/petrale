import glob, os, sys, time
import arcpy, pandas, numpy

if __name__ == '__main__':

    if os.getenv('USERNAME')=='ywang':
        file_dir = 'C:\\Users\\{}\\Documents\\ArcGIS\\Projects\\SantaClara_subsidized_blgs'.format(os.getenv('USERNAME'))
        gdb_dir = 'C:\\Users\\{}\\Documents\\ArcGIS\\Projects\\SantaClara_subsidized_blgs\\SantaClara_subsidized_blgs.gdb'.format(os.getenv('USERNAME'))

    arcpy.env.workspace = gdb_dir

    files = {'v2.1.csv':   'v2_1',
             'v2.2.1.csv': 'v2_2_1',
             'v2.3.csv':   'v2_3',
             'v2.3.1.csv': 'v2_3_1',
             'v2.4.csv':   'v2_4',
             'v2.5.csv':   'v2_5',
             'v2.6.csv':   'v2_6',
             'v2.7.csv':   'v2_7',
             'v2.8.csv':   'v2_8',
             'v2.9.csv':   'v2_9'}

    for filename in list(glob.glob(file_dir+'\\*.csv')):

#        start = time.time()

        if 'parcel_summary' in filename:
            print('Process {}'.format(filename))

            base_name = os.path.basename(filename)
            print(base_name)

            parcel_summary = pandas.read_csv(filename)
            # copy the table to gdb_dir
            print('Copy {} to {}'.format(filename, gdb_dir))

            # delete table if there's already one there by that name
            parcel_summary_cp = 'parcel_summary_cp_'+files[base_name.split('_')[2]]
            if arcpy.Exists(parcel_summary_cp):
                arcpy.Delete_management(parcel_summary_cp)
                print("Found {} -- deleting".format(parcel_summary_cp))
            
            parcel_summary_values = numpy.array(numpy.rec.fromrecords(parcel_summary.values))
            parcel_summary_values.dtype.names = tuple(parcel_summary.dtypes.index.tolist())
            parcel_summary_table_path = os.path.join(gdb_dir, parcel_summary_cp)
            arcpy.da.NumPyArrayToTable(parcel_summary_values, parcel_summary_table_path)
            print("Created {}".format(parcel_summary_table_path))

            # make a copy of the p10_scl layer as the join target layer

            # delete the layer if it already exists
            if arcpy.Exists('p10_scl_cp'):
                arcpy.Delete_management('p10_scl_cp')
                print("Found {} -- deleting".format('p10_scl_cp'))
            
            arcpy.CopyFeatures_management('p10_scl',
                                          'p10_scl_cp')

            # join table to p10_scl layer
            print('Joining {} with {}'.format('p10_scl_cp',
                                              parcel_summary_table_path))

            parcel_summary_join = arcpy.AddJoin_management('p10_scl_cp', 'PARCEL_ID',
                                                           parcel_summary_cp, 'parcel_id',
                                                           join_type="KEEP_ALL")

            parcel_summary_version = files[base_name.split('_')[2]]
            parcel_summary_rename = 'p10_scl_{}'.format(parcel_summary_version)
            print('Save {}'.format(parcel_summary_rename))

            # delete the layer if it already exists in the output gdb
            if arcpy.Exists(parcel_summary_rename):
                arcpy.Delete_management(parcel_summary_rename)
                print("Found {} -- deleting".format(parcel_summary_rename))

            # save it
            arcpy.CopyFeatures_management(parcel_summary_join, os.path.join(gdb_dir, parcel_summary_rename))
            print("Completed creation of {}".format(os.path.join(gdb_dir, parcel_summary_rename)))
            field_names = [f.name for f in arcpy.ListFields(parcel_summary_rename)]
            print("{} has the following fields: {}".format(parcel_summary_rename,
                                                           field_names))

        # print('{} took {0:0.1f} minutes'.format(base_name,
        #                                         (time.time()-start)/60.0))
