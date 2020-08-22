USAGE="""

  Extract base zoning data for a given jurisdiction or county.

  Input:  p10_plu_boc_allAttrs.csv, parcel-level base zoning data, including both PBA40 and BASIS
          
  Output: basezoning_area.csv, base zoning data for a given jurisdiction or county

  Run with: python extract_area_basezoning.py --area_list "san_francisco" "palo_alto"

"""

import pandas as pd
import numpy as np
import argparse, os, glob, logging, sys, time

today = time.strftime('%Y_%m_%d')

if os.getenv('USERNAME') =='ywang':
    M_DIR                = 'M:\\Data\\Urban\\BAUS\\PBA50\\Draft_Blueprint'
    BOX_DIR              = 'C:\\Users\\{}\\Box\\Modeling and Surveys\\Urban Modeling\\Bay Area UrbanSim\\PBA50'.format(os.getenv('USERNAME'))
    GITHUB_URBANSIM_DIR  = 'C:\\Users\\{}\\Documents\\GitHub\\bayarea_urbansim\\data'.format(os.getenv('USERNAME'))

# input
M_BASEZONING_DIR         = os.path.join(M_DIR, 'Base zoning', 'output')
BASEZONING_FILE          = os.path.join(M_BASEZONING_DIR, '2020_06_03_p10_plu_boc_allAttrs.csv')

# output
BOX_BASEZONING_DIR       = os.path.join(BOX_DIR, 'Policies', 'Base zoning', 'outputs')
AREA_BASEZONING_FILE     = os.path.join(BOX_BASEZONING_DIR, '{}_basezoning'.format(today))

juris_list = ['livermore', 'hayward', 'unincorporated_sonoma', 'fremont',
              'pleasanton', 'dublin', 'unincorporated_contra_costa', 'brentwood',
              'san_ramon', 'oakley', 'antioch', 'unincorporated_napa',
              'san_francisco', 'unincorporated_san_mateo', 'petaluma',
              'santa_rosa', 'rohnert_park', 'unincorporated_marin', 'richmond',
              'pittsburg', 'orinda', 'alameda', 'napa', 'hercules', 'newark',
              'unincorporated_alameda', 'martinez', 'danville', 'healdsburg',
              'concord', 'sunnyvale', 'clayton', 'daly_city', 'rio_vista',
              'oakland', 'lafayette', 'san_pablo', 'walnut_creek',
              'pleasant_hill', 'union_city', 'brisbane', 'cloverdale',
              'san_leandro', 'pinole', 'fairfield', 'san_jose',
              'south_san_francisco', 'palo_alto', 'novato', 'hillsborough',
              'half_moon_bay', 'berkeley', 'unincorporated_solano', 'milpitas',
              'american_canyon', 'redwood_city', 'mountain_view', 'sonoma',
              'fairfax', 'santa_clara', 'vallejo', 'woodside',
              'unincorporated_santa_clara', 'windsor', 'moraga', 'dixon',
              'vacaville', 'gilroy', 'morgan_hill', 'cupertino', 'benicia',
              'larkspur', 'piedmont', 'san_mateo', 'san_rafael', 'san_bruno',
              'calistoga', 'cotati', 'mill_valley', 'san_anselmo', 'los_altos',
              'el_cerrito', 'saratoga', 'suisun_city', 'sebastopol', 'campbell',
              'st_helena', 'albany', 'los_gatos', 'menlo_park', 'san_carlos',
              'los_altos_hills', 'sausalito', 'pacifica', 'belmont', 'tiburon',
              'east_palo_alto', 'emeryville', 'corte_madera', 'foster_city',
              'millbrae', 'burlingame', 'atherton', 'portola_valley',
              'monte_sereno', 'ross', 'yountville', 'colma', 'belvedere']
county_list = ['Alameda', 'Sonoma', 'Contra Costa', 'Napa', 'San Francisco',
               'San Mateo', 'Marin', 'Santa Clara', 'Solano']

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=USAGE, formatter_class=argparse.RawDescriptionHelpFormatter,)
    parser.add_argument('--area_list', nargs='+', help='list of jurisdiction or county name')
    args = parser.parse_args()

    # read basezoning data
    basezoning_all = pd.read_csv(BASEZONING_FILE)
    print('Read {} records from {}'.format(len(BASEZONING_FILE), BASEZONING_FILE))

    # extract data for areas in the list
    for area in args.area_list:
        print('Select records for {}'.format(area))
        if area in juris_list:
            area_basezoning = basezoning_all.loc[basezoning_all.juris_zmod == area]
        if area in county_list:
            area_basezoning = basezoning_all.loc[basezoning_all.county_name == area]

        if (area not in juris_list) & (area not in county_list):
            print('Wrong jurisdiction or county name: {}'.format(area))
            continue

        export_file_name = '{}_{}.csv'.format(AREA_BASEZONING_FILE, area)
        print('Export {} records of basezoning for {} to {}'.format(len(area_basezoning),
                                                                    area,
                                                                    export_file_name))
        area_basezoning.to_csv(export_file_name, index = False)